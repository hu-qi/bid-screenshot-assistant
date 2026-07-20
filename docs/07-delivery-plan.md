# 实施与提交计划

- 状态：Accepted baseline
- 原则：每个阶段都包含文档、实现、测试和可审阅 Commit。

## Phase 0 — 工程基线（本次）

产物：

- 项目章程、PRD、架构、Adapter 协议、DESIGN.md；
- 九平台目录；
- 可运行 simulation 闭环；
- API、CLI、证据/manifest/ZIP；
- JiuwenSwarm Skill/SwarmFlow/MCP 样例；
- 测试与 CI。

完成标准：本地 `pytest` 和 `compileall` 通过；生成归档包。

## Phase 1 — 平台侦察与测试资产

建议 3 个 PR：

1. `docs(platforms): verify china-mobile flows`
2. `docs(platforms): verify china-unicom flows`
3. `docs(platforms): verify china-tower-eproc flows`

每个 PR 同时提交平台调查文档、脱敏页面 fixture、Adapter 状态机和契约测试。

## Phase 2 — 三平台真实 MVP

每个平台独立 PR，实现：

- 会话准备；
- 搜索和分页；
- 命中/未命中判定；
- 搜索页和详情页截图；
- 失败分类和人工接管；
- 回归测试。

集成 PR 实现真实任务矩阵、持久化和队列。

## Phase 3 — 九平台覆盖

按平台逐个交付，不做一个包含全部选择器的巨型 PR。公共协议变更必须先单独 ADR/PR。

## Phase 4 — 交付与定时监控

- SMTP/企业邮箱；
- 大附件下载链接；
- JiuwenSwarm Cron；
- 新公告去重；
- 飞书/企业微信渠道；
- 运维指标和告警。

## 推荐 Commit 粒度

1. `bootstrap repository governance`
2. `document product and architecture baseline`
3. `add domain and adapter contracts`
4. `add simulation runner and evidence package`
5. `add api ui and jiuwenswarm integration skeleton`
6. `add tests and continuous integration`

本次由于连接器提交能力限制，可在一个基线 Commit 中包含上述完整内容，但后续严格按可审阅意图拆分。
