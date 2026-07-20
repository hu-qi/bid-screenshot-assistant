# 九个平台 Adapter 协议

- 状态：Accepted
- 版本：1.0-draft

## 1. 目标

统一九个平台的输入、输出、状态和证据要求，同时允许每个平台使用不同的 URL、登录、搜索、分页和详情流程。

## 2. Adapter 生命周期

```text
prepare_session
  → navigate_to_search
  → apply_filters
  → submit_query
  → wait_for_result_state
  → collect_hits
  → capture_result_page
  → open_and_capture_details
  → validate_evidence
  → finalize
```

Adapter 可以在公共接口内部增加步骤，但不能跳过结果判定和证据校验。

## 3. 输入契约

```python
AdapterRequest(
    task_id: str,
    run_id: str,
    query_id: str,
    query_name: str,
    platform_id: PlatformId,
    match_mode: MatchMode,
    date_from: datetime | None,
    date_to: datetime | None,
    notice_types: list[str],
    include_terms: list[str],
    exclude_terms: list[str],
    max_hits: int,
    attempt: int,
    browser_session_id: str | None,
)
```

## 4. 输出契约

```python
PlatformExecutionResult(
    status: PlatformRunStatus,
    hits: list[SearchHit],
    artifacts: list[EvidenceArtifact],
    started_at: datetime,
    finished_at: datetime,
    duration_ms: int,
    current_step: str,
    feedback: str | None,
    error_code: str | None,
    retryable: bool,
    browser_session_id: str | None,
)
```

## 5. 状态判定

| 状态 | 必要条件 | 是否可自动重试 |
|---|---|---|
| FOUND | 搜索成功且至少一个候选通过匹配 | 视证据完整性 |
| NOT_FOUND | 搜索流程完成，有明确无结果状态和结果页证据 | 否 |
| PARTIAL | 有命中但部分详情/证据失败 | 是 |
| LOGIN_REQUIRED | 未登录或会话失效 | 人工后恢复 |
| CAPTCHA_REQUIRED | 验证码/扫码/人机验证 | 人工后恢复 |
| PAGE_CHANGED | 关键入口或结果结构与已知规则不符 | 否，需更新 Adapter |
| TIMEOUT | 超过步骤或总预算 | 是，限制次数 |
| PLATFORM_ERROR | 平台返回明确系统异常 | 是 |
| FAILED | 未归类技术失败 | 是，限制次数 |

严禁把以下情况判为 `NOT_FOUND`：搜索按钮未生效、登录失效、结果区未加载、页面结构变化、网络错误、验证码拦截。

## 6. 证据要求

### FOUND

至少包含：

- 搜索结果页证据；
- 每个纳入结果的详情页证据或不可打开原因；
- 原始 URL、标题、发布日期；
- 采集时间和 SHA-256。

### NOT_FOUND

至少包含：

- 查询词可见；
- 平台名称/URL 可见；
- “无结果”或结果数为 0 的页面状态；
- 采集时间和 SHA-256。

### 失败状态

尽可能保存当前页面快照、可见关键词、当前步骤和已执行动作。

## 7. 登录与人工接管

- Adapter 只复用授权 Profile，不保存明文密码；
- 遇到验证码立即暂停，不自动刷新消耗验证码；
- 输出 `browser_session_id`、当前 URL、步骤和人工说明；
- 人工完成后使用同一 session 和新的 attempt 恢复；
- 恢复前验证页面仍处于预期阶段。

## 8. 选择器策略

优先级：

1. 稳定的可访问性角色/文本；
2. `data-*` 或业务语义属性；
3. 稳定的表单 name/id；
4. CSS 结构选择器；
5. 坐标操作仅作最后手段且必须有截图基线。

选择器、关键词和页面指纹必须集中在对应 Adapter，不散落在 Prompt。

## 9. Adapter 元数据

每个平台实现暴露：

```json
{
  "platform_id": "china-mobile",
  "display_name": "中国移动采购与招标网",
  "adapter_version": "0.1.0",
  "stage": "experimental",
  "requires_login": true,
  "supports_date_filter": true,
  "supports_notice_type_filter": false,
  "last_verified_at": null
}
```

## 10. 契约测试

所有 Adapter 必须通过公共测试：

- 元数据字段完整且 ID 唯一；
- `NOT_FOUND` 有证据；
- 命中上限生效；
- 超时能分类；
- 验证码不自动绕过；
- 任何异常都返回结构化结果；
- Artifact 哈希可验证；
- 不泄露 Cookie、Token 或账号信息。
