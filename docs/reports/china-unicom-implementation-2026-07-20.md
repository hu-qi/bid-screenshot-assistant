# 中国联通采购与招标网 Adapter 实现报告

- 日期：2026-07-20
- Platform ID：`china-unicom`
- 实现状态：`implemented / fixture-tested / live-regression-pending`
- 默认状态：`disabled`
- 对应 Issue：#3

## 1. 本次实现范围

已实现公开公告页面的实验性 Adapter：

- 打开 `/bidInformation` JavaScript 列表页；
- 等待关键词输入框可见并校验页面 hydration；
- 按原始项目名称执行公告搜索；
- 从渲染后 HTML 提取合法详情链接；
- 兼容 `detail?id=<数字>` 和历史 `detail?cid=<数字>&id=<数字>`；
- 提取标题、发布时间、可选招标/采购编号、正文摘要和公开附件 URL；
- 保存搜索结果页 PNG、详情页 PNG 和详情 metadata JSON；
- 输出 `FOUND`、`NOT_FOUND`、`PARTIAL`、`PAGE_CHANGED`、`TIMEOUT`、`PLATFORM_ERROR`；
- 将静态 501、未水合和启用 JavaScript 提示判定为页面契约失败，不判定为未命中；
- 生成 SHA-256 manifest 与 ZIP 归档。

未实现：

- 时间快捷条件和自定义时间设置；
- 列表分页；
- 网络响应字段辅助解析；
- 公开附件实际下载；
- 供应商注册、购标、应答、支付或异议操作；
- 10+ 真实 Chrome 样例回归。

## 2. 代码结构

```text
src/bid_screenshot_assistant/adapters/china_unicom/
├── adapter.py
├── driver.py
├── parser.py
└── models.py
```

真实 Adapter 通过独立 `build_china_unicom_registry()` 加载，不会进入默认 simulation Registry。

## 3. 已验证公开契约

列表页公开可见：

- “搜索公告”；
- 关键词占位文案“请输入公告关键词”；
- 搜索按钮；
- 不限、今天、近三天、近一周、近一月、自定义时间。

详情页公开可见：

- 公告标题；
- `发布时间：YYYY-MM-DD HH:MM:SS`；
- 可选招标编号、采购项目编号或采购代理编号；
- 公告正文；
- 可选附件。

已观察的详情 URL：

```text
https://www.chinaunicombidding.cn/bidInformation/detail?id=<numeric-id>
https://www.chinaunicombidding.cn/bidInformation/detail?cid=<numeric>&id=<numeric-id>
```

## 4. 状态判定

### FOUND

搜索结果中存在合法官方详情链接，且选中的详情页完成截图和解析。

### NOT_FOUND

必须同时满足：搜索已完成、没有合法详情链接、页面出现“暂无数据”等明确空状态。

### PARTIAL

列表命中被保留，但一个或多个详情页打开、指纹、截图或解析失败；失败写入 `detail-errors.json`。

### PAGE_CHANGED

以下情况均不会误报未命中：

- 搜索框未出现；
- 页面未完成 JavaScript hydration；
- 页面出现错误码 501；
- 搜索后既没有合法详情链接，也没有明确空状态；
- 详情缺少发布时间；
- URL 不符合官方模式。

## 5. 安全控制

- 只允许 HTTPS；
- 只允许 `www.chinaunicombidding.cn` 和 `chinaunicombidding.cn`；
- 详情 URL 必须匹配数字 ID 模式；
- 外部或欺骗域名详情链接被过滤；
- 附件 URL 也必须属于官方域名；
- 不进入 `cuecp.cn` 等供应商交易流程；
- 真实命令必须传入 `--acknowledge-experimental`。

## 6. 测试资产

```text
tests/fixtures/china_unicom/
├── list_found.html
├── list_not_found.html
├── list_501.html
└── detail_found.html
```

覆盖：

- 当前和历史详情 URL；
- 外部详情链接过滤；
- 正常标题、发布时间、编号、正文和附件解析；
- 外部附件过滤；
- 明确未命中；
- 501/未水合不是未命中；
- FOUND、NOT_FOUND、PARTIAL、PAGE_CHANGED；
- 实验证据 `simulation=false`。

## 7. 运行方式

```bash
pip install -e '.[dev,browser]'
playwright install chromium

bid-screenshot unicom \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

## 8. 未完成验证

当前环境未运行可交互的真实 Chrome 回归，以下事项仍需核实：

- 搜索按钮和结果刷新信号的稳定 Locator；
- 真实无结果文案；
- 列表分页和时间筛选；
- 站点是否对频率、地区或浏览器环境实施限制；
- 附件最终下载 URL、MIME 和大小；
- 至少 10 个真实命中、未命中和异常样例。

完成真实回归前，Adapter 保持 `experimental / disabled`。
