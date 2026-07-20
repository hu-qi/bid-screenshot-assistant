# 贡献指南

## 基本原则

1. **文档与代码同 PR**：改变用户行为、平台规则、数据结构或运维方式时，必须同时更新对应文档。
2. **Adapter 独立演进**：一个平台一个 Adapter；禁止用平台 A 的特例污染公共协议。
3. **证据优先**：任何“成功”状态必须有可验证产物或明确的 `NOT_FOUND` 页面证据。
4. **不得绕过安全控制**：验证码、扫码、风控、权限门均转人工接管。
5. **不伪造能力**：未连接真实平台的代码只能标记为 `simulation`、`stub` 或 `experimental`。

## 分支与提交

- 分支：`agent/<scope>`、`feat/<scope>`、`fix/<scope>`、`docs/<scope>`。
- Commit 使用动词开头并说明一个可审阅意图，例如：
  - `establish product and architecture baseline`
  - `add china-mobile adapter discovery flow`
  - `document captcha handoff state`
- 每个 PR 描述必须包含：变更、原因、用户影响、验证方式、文档影响和已知风险。

## Definition of Done

平台 Adapter 只有同时满足以下条件才可标记为 `enabled`：

- 有公开入口、搜索条件和详情页路径记录；
- 有至少 10 个可复现样例（命中、未命中、重名、分页、异常）；
- 能保存结果页和详情页证据；
- 能正确区分 `NOT_FOUND` 与技术失败；
- 登录、验证码、风控能转入人工接管；
- 有单元测试、契约测试和浏览器回归测试；
- 更新平台矩阵、操作手册和变更日志。

## 本地验证

```bash
pip install -e '.[dev]'
pytest
python -m compileall src skills
bid-screenshot demo --query "测试项目"
```
