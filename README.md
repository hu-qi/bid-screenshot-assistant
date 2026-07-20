# 标讯截图助手（Bid Screenshot Assistant）

输入一个或一批项目名称，系统按配置访问 9 个主流标讯平台，保存搜索结果与公告详情证据，生成可校验的归档包，并通过邮件或 JiuwenSwarm 频道交付。

> 当前阶段：**工程基线 / simulation-first**。仓库已经提供可运行的模拟闭环、完整文档结构、九平台 Adapter 协议、JiuwenSwarm Skill/SwarmFlow 接入骨架。真实平台自动化将在 Adapter 验证通过后逐个平台启用，不在未验证时宣称可用。

## 为什么不是普通标讯聚合器

本项目的核心产物不是一条聚合链接，而是一套可追溯的证据包：

- 搜索关键词、平台、时间、页面 URL 与命中状态；
- 搜索结果页与详情页截图/页面快照；
- 每个文件的 SHA-256；
- 平台级执行状态、耗时、重试与失败原因；
- 汇总清单、manifest 和 ZIP 归档；
- 邮件或消息渠道交付记录。

## 九个平台

1. 中国移动采购与招标网
2. 中国联通采购与招标网
3. 中国电信阳光采购网
4. 中国铁塔在线商务平台
5. 中国铁塔电子采购平台
6. 中国招标投标公共服务平台
7. 工业和信息化部通信工程建设项目招标投标管理信息平台
8. 广东政府采购智慧云平台
9. 广东省公共资源交易平台

平台标识、登录要求和第一阶段验证结论见 [`docs/04-platform-matrix.md`](docs/04-platform-matrix.md)。

## 快速运行

要求 Python 3.11+。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'

# 运行模拟闭环：创建任务 → 9 平台并行执行 → 生成证据 → 打包 ZIP
bid-screenshot demo --query "广州市某智慧园区项目"

# 启动 API 和轻量管理页
uvicorn bid_screenshot_assistant.api:app --reload
# 浏览器访问 http://127.0.0.1:8000

# 验证
pytest
python -m compileall src skills
```

模拟模式使用确定性 Adapter，不访问真实网站：

- 普通名称：模拟命中并生成 SVG 页面快照；
- 名称包含“未命中”：模拟查询无结果；
- 名称包含“失败”：模拟平台执行异常。

## 目录

```text
.
├── DESIGN.md                         # 产品界面与交互设计基线
├── docs/                             # PRD、架构、协议、ADR、测试、运维与合规
├── config/                           # 平台与 JiuwenSwarm/MCP 配置样例
├── skills/bid-screenshot/            # JiuwenSwarm Skill + SwarmFlow
├── src/bid_screenshot_assistant/     # 可运行 Python 项目骨架
├── tests/                            # 基线测试
└── .github/workflows/ci.yml          # 持续集成
```

## 文档即代码

所有需求、设计、接口、决策、验收标准和变更记录必须与实现一起走分支、Commit 和 Pull Request。主要规则见：

- [`docs/00-project-charter.md`](docs/00-project-charter.md)
- [`docs/decisions/0001-docs-as-code.md`](docs/decisions/0001-docs-as-code.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## 当前边界

当前代码没有绕过验证码、风控或登录控制；没有声称已经稳定抓取九个平台；没有将模拟快照作为真实公告证据。真实 Adapter 必须通过平台回归样例、人工接管路径与合规评审后才能从 `experimental` 升级为 `enabled`。
