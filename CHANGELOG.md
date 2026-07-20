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
- 中国移动、中国联通、中国铁塔电子采购平台的首轮真实入口调查档案。
- ADR-0004：真实平台优先采用公开浏览器页面契约。

### Changed

- MVP 实现顺序调整为：中国铁塔电子采购平台 → 中国联通 → 中国移动。
