# Changelog

本项目采用 Keep a Changelog 风格记录重要变化。版本号在首个真实平台 Adapter 达到可验收状态后启用语义化版本。

## [Unreleased]

### Added

- 文档即代码项目基线。
- 完整 PRD、架构、九平台 Adapter 协议、数据模型、UI/UX、测试、安全与运维文档。
- 九个平台目录与确定性模拟 Adapter。
- 可运行 CLI、FastAPI 管理入口、证据文件生成、SHA-256 manifest 与 ZIP 打包。
- JiuwenSwarm Skill、SwarmFlow 和 MCP 配置样例。
- 基线测试与 GitHub Actions。
- 中国移动、中国联通、中国铁塔电子采购平台的真实入口调查档案。
- ADR-0004：真实平台优先采用公开浏览器页面契约。
- 中国铁塔电子采购平台实验性 Playwright Adapter、解析器、状态机和 Fixture 测试。
- 中国联通采购与招标网实验性 Playwright Adapter、解析器、状态机和 Fixture 测试。
- 中国移动采购与招标网实验性 Playwright Adapter、搜索完成信号、解析器和 Fixture 测试。
- 中国移动候选详情 URL 白名单、首页初始空状态保护和同域附件过滤。
- 中国联通当前/历史详情 URL 兼容、501/未水合识别和官方附件域名防护。
- 受显式确认参数保护的 `bid-screenshot mobile`、`bid-screenshot tower-eproc` 和 `bid-screenshot unicom` 实验命令。
- simulation 与 experimental-live 执行模式在 summary、manifest 和报告中分离记录。

### Changed

- 三个 P0 平台均更新为 `implemented / fixture-tested / live-regression-pending`，继续默认关闭。
- 下一阶段从 P0 真实 Chrome 回归转向中国电信、公共服务平台等 P1 Adapter 调查。
