# 中国联通采购与招标网平台档案

- Platform ID：`china-unicom`
- 状态：`adapter-implemented / fixture-tested / live-regression-pending`
- 当前 Adapter：`experimental / disabled`
- last_verified_at：2026-07-20
- 官方首页：https://www.chinaunicombidding.cn/
- 公告列表：https://www.chinaunicombidding.cn/bidInformation
- 实现报告：[`../reports/china-unicom-implementation-2026-07-20.md`](../reports/china-unicom-implementation-2026-07-20.md)

## 1. 已核实事实

公告列表页面公开展示：

- 标题“搜索公告”；
- 关键词输入框，占位文案“请输入公告关键词”；
- 时间快捷条件“不限、今天、近三天、近一周、近一月、自定义”；
- 页面为 Ant Design 风格单页应用，强依赖 JavaScript；
- 某些非浏览器抓取环境会出现“请求错误，请联系管理员。错误码：501”。

公开详情页 URL 已核实为：

```text
https://www.chinaunicombidding.cn/bidInformation/detail?id=<numeric-id>
https://www.chinaunicombidding.cn/bidInformation/detail?cid=<numeric>&id=<numeric-id>
```

详情页可公开读取，并稳定出现：

- 公告标题；
- 招标编号，或正文中的采购项目/代理编号；
- 发布时间，格式类似 `2026-04-02 18:19:35`；
- 公告正文；
- 可选附件区域。

## 2. 当前实现

已实现：

- Playwright 打开公告列表并等待 hydration；
- 搜索输入框和列表页文本指纹校验；
- 按原始查询名称执行搜索；
- 当前与历史详情 URL 识别；
- 标题匹配与结果排序；
- 详情标题、发布时间、可选编号、正文摘要和附件 URL 解析；
- 搜索页和详情页全页 PNG；
- 详情 metadata JSON；
- `FOUND`、`NOT_FOUND`、`PARTIAL`、`PAGE_CHANGED`、`TIMEOUT`、`PLATFORM_ERROR`；
- 501/未水合页面不误判为 `NOT_FOUND`；
- 详情和附件官方域名限制；
- 独立实验 Registry 与 `bid-screenshot unicom` 命令；
- Fixture 与 Fake Browser Driver 状态机测试。

当前未实现：

- 时间筛选；
- 结果分页；
- XHR/Fetch 响应辅助解析；
- 公开附件实际下载；
- 供应商交易流程；
- 10+ 真实 Chrome 回归样例。

因此 Adapter 不进入默认 Registry，不能升级为 `pilot` 或 `enabled`。

## 3. 页面契约

### 列表页指纹

- URL 路径为 `/bidInformation`；
- 可见“搜索公告”；
- 可见占位文案“请输入公告关键词”；
- 可见时间筛选；
- 页面不能停留在启用 JavaScript 提示或错误码 501。

### 搜索动作

1. 等待单页应用完成 hydration；
2. 定位关键词输入框并填入原始查询名称；
3. 点击文本为“搜索”的按钮；
4. 等待页面稳定；
5. 从渲染后页面提取详情链接；
6. 只打开符合官方数字 ID 模式的链接；
7. 受 `max_hits` 和总超时限制。

### 详情页指纹

- URL 满足当前或历史详情模式；
- 页面有主标题；
- 页面出现“发布时间”；
- 主体正文非空。

## 4. 状态与降级

- 未执行 JavaScript、仅出现启用提示或错误码 501：`PAGE_CHANGED`；
- 搜索输入或搜索按钮缺失：`PAGE_CHANGED`；
- 结果列表成功加载且明确无结果：`NOT_FOUND`；
- 有列表命中但详情失败：`PARTIAL`，保留列表命中和诊断证据；
- 浏览器超时：`TIMEOUT`；
- 其他平台/浏览器异常：`PLATFORM_ERROR`。

## 5. 安全边界

允许域名：

- `www.chinaunicombidding.cn`
- `chinaunicombidding.cn`

- 仅允许 HTTPS 和标准端口；
- 详情链接必须符合已验证数字 ID 模式；
- 附件链接也必须属于官方域名；
- `cuecp.cn` 等供应商注册、购标、支付、应答和异议流程不在当前范围；
- 不绕过验证码、权限和风控。

## 6. 已提交测试资产

```text
tests/fixtures/china_unicom/
├── list_found.html
├── list_not_found.html
├── list_501.html
└── detail_found.html
```

覆盖当前/历史 URL、恶意外链、明确未命中、501、公开详情字段、附件域名、详情失败和模糊空状态。

## 7. 下一步任务

1. 在受控 Chrome 中运行至少 10 个真实样例；
2. 核实搜索刷新信号、真实无结果文案和分页；
3. 实现时间快捷条件和自定义时间；
4. 记录脱敏网络响应字段，仅作辅助契约；
5. 实现公开附件下载的 MIME、大小和哈希验证；
6. 达到指标后再升级为 `pilot`。
