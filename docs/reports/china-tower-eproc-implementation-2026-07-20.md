# 中国铁塔电子采购平台 Adapter 实现报告

- 日期：2026-07-20
- Platform ID：`china-tower-eproc`
- 实现状态：`implemented / fixture-tested / live-regression-pending`
- 默认状态：`disabled`
- 对应 Issue：#2

## 1. 本次实现范围

已实现公开“采购公告”页面的实验性 Adapter：

- 打开采购公告列表；
- 校验列表页公开页面指纹；
- 按原始项目名称填写“请输入搜索关键字”；
- 点击“查询”并等待页面稳定；
- 从渲染后 HTML 中提取符合已验证 URL 模式的公告详情链接；
- 对候选标题执行确定性匹配和排序；
- 打开详情页并校验“信息时间”等指纹；
- 提取标题、发布日期、正文摘要和公开附件 URL；
- 保存结果页 PNG、详情页 PNG、详情 metadata JSON；
- 输出 `FOUND`、`NOT_FOUND`、`PARTIAL`、`PAGE_CHANGED`、`TIMEOUT` 和 `PLATFORM_ERROR`；
- 生成 SHA-256 manifest 与 ZIP 归档。

未实现：

- 供应商登录；
- 采购文件领取、付款、报名、投标、异议；
- CA 操作；
- 需要身份权限的附件下载；
- 省份、时间、行业筛选的自动设置；
- 翻页和多公告分类执行。

## 2. 代码结构

```text
src/bid_screenshot_assistant/adapters/china_tower_eproc/
├── adapter.py   # 状态机、证据写入和结果分类
├── driver.py    # Playwright 导航、搜索、截图和页面指纹
├── parser.py    # 列表/详情 HTML 解析、日期与标题匹配
└── models.py    # 浏览器快照和解析结果模型
```

真实 Adapter 通过独立的 `build_china_tower_eproc_registry()` 加载，不会混入默认九平台 simulation Registry。

## 3. 页面契约依据

公开列表页已观察到：

- “公告公示”；
- “省份”“时间”“行业”“搜索关键字”；
- 输入占位文案“请输入搜索关键字”；
- “查询”按钮；
- 采购公告列表入口 `/zgtt/gggs/003001/detailpage.html`。

公开详情页已观察到：

- URL：`/zgtt/gggs/<6位分类>/<YYYYMMDD>/<uuid-or-id>.html`；
- 公告标题；
- “信息时间：YYYY-MM-DD”；
- 正文；
- 可选公开附件。

公开样例：

- `https://ebid.chinatowercom.cn/zgtt/gggs/003001/20260507/68fee2cd-e504-468b-83d1-65164b4e4b65.html`
- `https://ebid.chinatowercom.cn/zgtt/gggs/003001/20260326/13a7d402-1e30-4026-942c-165b204cb262.html`
- `https://ebid.chinatowercom.cn/zgtt/gggs/003001/20260205/eb462997-e4b6-4adf-bb94-5325379ffce6.html`

## 4. 状态判定

### FOUND

列表中存在符合官方详情 URL 模式的候选，且选中的详情页可以完成截图和解析。

### NOT_FOUND

只有在搜索动作已完成、无合法详情链接，并且页面明确出现“暂无数据”等无结果标记时返回。

### PARTIAL

列表命中被保留，但一个或多个详情页打开、指纹、截图或解析失败。失败详情写入 `detail-errors.json`。

### PAGE_CHANGED

以下情况不会被误判为未命中：

- 列表页关键文字消失；
- 搜索后既无合法详情链接，也无明确无结果状态；
- 详情页缺少“信息时间”；
- 导航离开官方域名或详情 URL 不符合模式。

## 5. 安全控制

- 仅允许 HTTPS；
- 详情页仅允许 `ebid.chinatowercom.cn`；
- 详情 URL 必须符合已验证公告路径；
- 列表中的外部、伪造或欺骗域名链接被忽略；
- 附件 URL 也必须属于官方域名；
- 不执行登录、购买、领取、报名或投标动作；
- 真实命令必须显式传入 `--acknowledge-experimental`。

## 6. 测试资产

已提交脱敏 Fixture：

- `list_found.html`：两个合法公告链接和一个恶意外链；
- `list_not_found.html`：明确无结果状态；
- `detail_found.html`：标题、信息时间、正文和附件。

自动测试覆盖：

- 合法详情链接提取和去重；
- 外部详情链接过滤；
- 日期、标题、正文和附件解析；
- 外部详情 URL 拒绝；
- 明确无结果判定；
- FOUND、NOT_FOUND、PARTIAL、PAGE_CHANGED 状态机；
- 真实证据 `simulation=false`；
- 附件官方域名限制。

GitHub Actions 已通过 `compileall` 和全部 `pytest`。

## 7. 运行方式

```bash
pip install -e '.[dev,browser]'
playwright install chromium

bid-screenshot tower-eproc \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

可通过 `--user-data-dir` 指定隔离的 Chrome Profile，但当前公开公告流程不要求登录。

## 8. 未完成验证

当前执行环境未运行可交互的真实 Chrome 会话，因此以下内容仍需受控浏览器回归：

- 实际 DOM 中搜索按钮和输入框是否能稳定由语义 Locator 命中；
- 搜索结果刷新信号和真实无结果文案；
- 列表分页结构；
- 公开附件的最终跳转域名、MIME 和大小；
- 网站限流、验证码或访问风控；
- 5 类公告编码的完整确认。

在完成至少 10 个真实样例之前，平台继续保持 `experimental / disabled`，不能升级为 `pilot` 或默认启用。
