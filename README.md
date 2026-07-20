# 标讯截图助手（Bid Screenshot Assistant）

输入一个或一批项目名称，系统按配置访问 9 个主流标讯平台，保存搜索结果与公告详情证据，生成可校验的归档包，并通过邮件或 JiuwenSwarm 频道交付。

> 当前阶段：**工程基线 / simulation-first + 四平台 experimental-live**。仓库提供可运行的九平台模拟闭环，以及中国移动、中国联通、中国铁塔电子采购平台、中国招标投标公共服务平台四个实验性 Playwright Adapter。真实 Adapter 均默认关闭，在完成受控浏览器回归前不宣称生产可用。

## 核心产物

- 搜索关键词、平台、时间、页面 URL 与命中状态；
- 搜索结果页与详情页截图；
- 每个文件的 SHA-256；
- 平台级执行状态、耗时、重试与失败原因；
- summary、manifest、HTML 报告和 ZIP；
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

平台状态见 [`docs/04-platform-matrix.md`](docs/04-platform-matrix.md)。

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'

bid-screenshot demo --query "广州市某智慧园区项目"
uvicorn bid_screenshot_assistant.api:app --reload
pytest
python -m compileall src skills
```

模拟模式不访问真实网站。

## 实验性真实平台运行

```bash
pip install -e '.[dev,browser]'
playwright install chromium
```

### 中国移动

```bash
bid-screenshot mobile --acknowledge-experimental --query "项目名称" --headed
```

首页初始“无匹配数据”或无法证明搜索完成时返回 `PAGE_CHANGED`，不会误报 `NOT_FOUND`。详见 [`docs/reports/china-mobile-implementation-2026-07-20.md`](docs/reports/china-mobile-implementation-2026-07-20.md)。

### 中国铁塔电子采购平台

```bash
bid-screenshot tower-eproc --acknowledge-experimental --query "项目名称" --headed
```

详见 [`docs/reports/china-tower-eproc-implementation-2026-07-20.md`](docs/reports/china-tower-eproc-implementation-2026-07-20.md)。

### 中国联通

```bash
bid-screenshot unicom --acknowledge-experimental --query "项目名称" --headed
```

静态 501、未 hydration 或模糊空页面返回 `PAGE_CHANGED`。详见 [`docs/reports/china-unicom-implementation-2026-07-20.md`](docs/reports/china-unicom-implementation-2026-07-20.md)。

### 中国招标投标公共服务平台

```bash
bid-screenshot cebpubservice --acknowledge-experimental --query "项目名称" --headed
```

验证码、滑块或安全验证返回 `CAPTCHA_REQUIRED` 并停止，不尝试识别或绕过。“上链查证”的手机号与短信验证码不属于公告浏览流程。详见 [`docs/reports/cebpubservice-implementation-2026-07-20.md`](docs/reports/cebpubservice-implementation-2026-07-20.md)。

通用参数：`--user-data-dir`、`--timeout-ms`、重复 `--query`、`--headed`。

所有实验运行在 summary、manifest 和报告中标记为 `experimental-live`，并通过独立 Registry 加载。

## 目录

```text
.
├── DESIGN.md
├── docs/
├── config/
├── skills/bid-screenshot/
├── src/bid_screenshot_assistant/
├── tests/
└── .github/workflows/ci.yml
```

## 文档即代码

需求、设计、协议、平台调查、实现报告、测试和运维决策必须与代码走同一分支、Commit 和 Pull Request。

## 当前边界

当前代码不绕过验证码、风控或登录控制，不把模拟证据作为真实公告证据。四个真实 Adapter 已通过 Fixture/状态机测试，但仍需生产 Chrome 样例、分页/筛选、附件下载和人工接管回归，因此继续保持 `experimental / disabled`。
