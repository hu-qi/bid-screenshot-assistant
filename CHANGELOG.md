# Changelog

本项目采用 Keep a Changelog 风格记录重要变化。版本号在首个真实平台 Adapter 达到可验收状态后启用语义化版本。

## [Unreleased]

### Added

- 文档即代码项目基线、完整 PRD、架构、九平台 Adapter 协议、设计、测试、安全和运维文档。
- 九个平台确定性模拟 Adapter、FastAPI、CLI、证据、manifest、HTML 报告与 ZIP。
- JiuwenSwarm Skill、SwarmFlow、MCP 配置样例和 GitHub Actions。
- 中国铁塔电子采购平台实验性 Playwright Adapter、解析器、状态机和 Fixture 测试。
- 中国联通采购与招标网实验性 Playwright Adapter、501/未水合识别和当前/历史详情 URL。
- 中国移动采购与招标网实验性 Playwright Adapter、搜索完成信号和首页初始空状态保护。
- 中国招标投标公共服务平台实验性 Playwright Adapter、公告类型详情契约和验证码人工边界。
- 四个平台的独立实验 Registry、CLI、平台档案和实现报告。
- simulation 与 experimental-live 在 summary、manifest 和报告中分离记录。

### Changed

- 中国移动、中国联通、中国铁塔电子采购平台更新为 `implemented / fixture-tested / live-regression-pending`。
- 中国招标投标公共服务平台更新为 `implemented / fixture-tested / production-live-regression-pending`。
- 所有真实 Adapter 继续默认关闭；验证码、滑块、短信和 CA 场景不得自动绕过。
