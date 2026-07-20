# 广东政府采购智慧云平台 Adapter 实现报告

- 日期：2026-07-20
- Platform ID：`gd-gp`
- 状态：`implemented / fixture-tested / live-regression-pending`

## 1. 本次目标

在不登录电子卖场或交易工作台的前提下，实现广东政府采购公开公告的关键词检索、详情证据、状态分类和归档闭环。

## 2. 设计选择

### 2.1 公开 API 作为主数据契约

平台公开检索和详情 API 返回结构化 JSON，适合验证：

- 搜索是否真正完成；
- 是否明确零结果；
- 公告标题、时间、类型、采购人、项目编号和地区；
- 正文、预算、采购方式和公开附件。

因此第一版以官方 API 响应作为必需证据。

### 2.2 门户页面作为增强截图

门户详情路由更适合业务人员阅读，但历史 SPA 路由存在直接打开 403 的情况。Adapter 会尝试门户截图；失败时保留 API 详情证据并返回 `PARTIAL`。

这避免了两个错误：

1. 因门户路由失败丢掉已确认的官方公告；
2. 把 JSON 证据成功误称为完整公告页面截图成功。

## 3. 代码产物

```text
src/bid_screenshot_assistant/adapters/gd_gp/
├── __init__.py
├── adapter.py
├── driver.py
├── models.py
└── parser.py
```

同时更新：

- `adapters/profiles.py`
- `adapters/catalog.py`
- `adapters/__init__.py`
- `cli.py`
- 浏览器 Profile 契约测试。

## 4. 执行流程

```text
打开官方首页建立同站会话
  → 打开公开检索 API 并截图
  → 验证 code=200 和 rows
  → 标题匹配排序
  → 打开详情 API 并截图
  → 解析正文和附件
  → 尝试打开门户公告页并截图
  → 生成 metadata / diagnostics
  → manifest / ZIP
```

## 5. 状态结果

| 场景 | 状态 |
|---|---|
| API 明确 `rows=[]` | `NOT_FOUND` |
| 详情 API 与门户截图成功 | `FOUND` |
| 详情 API 成功但门户截图失败 | `PARTIAL` |
| 单条详情 API 失败 | `PARTIAL` |
| 响应不是成功 JSON | `PAGE_CHANGED` |
| 页面/请求超时 | `TIMEOUT` |
| 其他平台错误 | `PLATFORM_ERROR` |

## 6. 证据文件

单条命中可生成：

```text
result-api-page.png
detail-001.api.png
detail-001.png
detail-001.json
capture-errors.json   # 仅有异常时
summary.json
manifest.json
report.html
```

其中：

- `result-api-page.png`：官方搜索响应截图；
- `detail-001.api.png`：官方详情响应截图；
- `detail-001.png`：门户公告页截图；
- metadata 同时保留 API URL 与门户 URL。

## 7. 自动测试

测试覆盖：

- 带 `<font>` 高亮的标题还原；
- 详情 API 与门户 URL 生成；
- 官方空结果；
- 详情正文、采购人、项目编号、预算和附件；
- 外部附件过滤；
- 门户失败降级为 `PARTIAL`；
- 非成功响应归类为 `PAGE_CHANGED`；
- 真实证据 `simulation=false`。

## 8. 实验命令

```bash
bid-screenshot gd-gp \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

## 9. 风险与后续

- 搜索参数、渠道和门户路由仍需生产回放；
- 当前默认宽时间范围需要改为任务可配置；
- 门户路由 403 时需要验证站内导航恢复方式；
- 附件只记录 URL，尚未下载；
- 生产启用前必须完成至少 10 个真实样例和连续回归。
