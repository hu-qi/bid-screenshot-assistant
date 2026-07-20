# 标讯截图助手（Bid Screenshot Assistant）

输入一个或一批项目名称，系统按配置访问 9 个主流标讯平台，保存搜索结果与公告详情证据，生成可校验的归档包，并通过邮件或 JiuwenSwarm 频道交付。

> 当前阶段：**工程基线 / simulation-first + 三平台 experimental-live**。仓库提供可运行的九平台模拟闭环，以及中国移动、中国联通、中国铁塔电子采购平台三个实验性 Playwright Adapter。真实 Adapter 均默认关闭，在完成受控浏览器回归前不宣称生产可用。

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
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'

# 九平台确定性模拟闭环
bid-screenshot demo --query "广州市某智慧园区项目"

# API 和轻量管理页
uvicorn bid_screenshot_assistant.api:app --reload

# 验证
pytest
python -m compileall src skills
```

模拟模式不访问真实网站：普通名称模拟命中；名称包含“未命中”模拟零结果；名称包含“失败”模拟平台异常。

## 实验性真实平台运行

安装浏览器依赖：

```bash
pip install -e '.[dev,browser]'
playwright install chromium
```

### 中国移动采购与招标网

```bash
bid-screenshot mobile \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

中国移动 Adapter 会记录搜索完成信号。首页初始“无匹配数据”或无法证明搜索完成时返回 `PAGE_CHANGED`，不会误报 `NOT_FOUND`。候选详情 URL 仍需真实 Chrome 回归确认。

实现说明：[`docs/reports/china-mobile-implementation-2026-07-20.md`](docs/reports/china-mobile-implementation-2026-07-20.md)。

### 中国铁塔电子采购平台

```bash
bid-screenshot tower-eproc \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

实现说明：[`docs/reports/china-tower-eproc-implementation-2026-07-20.md`](docs/reports/china-tower-eproc-implementation-2026-07-20.md)。

### 中国联通采购与招标网

```bash
bid-screenshot unicom \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

中国联通 Adapter 会等待 JavaScript 单页应用 hydration；静态错误码 501、启用 JavaScript 提示或模糊空页面会返回 `PAGE_CHANGED`，不会误报 `NOT_FOUND`。

实现说明：[`docs/reports/china-unicom-implementation-2026-07-20.md`](docs/reports/china-unicom-implementation-2026-07-20.md)。

通用可选参数：

- `--user-data-dir <path>`：使用隔离 Chrome Profile；
- `--timeout-ms 45000`：调整页面操作超时；
- 多次使用 `--query`：批量查询多个名称；
- 去掉 `--headed`：无头模式运行。

实验模式在 `summary.json`、`manifest.json` 和报告中标记为 `experimental-live`。三个真实 Adapter 都通过独立 Registry 加载，不会混入默认 simulation Registry。

## 目录

```text
.
├── DESIGN.md                         # 产品界面与交互设计基线
├── docs/                             # PRD、架构、协议、ADR、测试、运维与合规
├── config/                           # 平台与 JiuwenSwarm/MCP 配置样例
├── skills/bid-screenshot/            # JiuwenSwarm Skill + SwarmFlow
├── src/bid_screenshot_assistant/     # 可运行 Python 项目骨架
├── tests/                            # 基线与平台契约测试
└── .github/workflows/ci.yml          # 持续集成
```

## 文档即代码

所有需求、设计、接口、决策、验收标准和变更记录必须与实现一起走分支、Commit 和 Pull Request。主要规则见：

- [`docs/00-project-charter.md`](docs/00-project-charter.md)
- [`docs/decisions/0001-docs-as-code.md`](docs/decisions/0001-docs-as-code.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## 当前边界

当前代码不绕过验证码、风控或登录控制，不把模拟快照作为真实公告证据。中国移动、中国联通和中国铁塔 Adapter 已实现并通过 Fixture/状态机测试，但尚未完成各自 10+ 真实浏览器样例，因此继续保持 `experimental / disabled`。真实 Adapter 必须通过平台回归样例、人工接管路径与合规评审后才能升级为 `pilot` 或 `enabled`。
