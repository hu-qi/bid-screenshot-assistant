# 中国联通采购与招标网平台档案

- Platform ID：`china-unicom`
- 状态：`entry-verified / detail-pattern-verified`
- 当前 Adapter：`experimental / disabled`
- last_verified_at：2026-07-20
- 官方首页：https://www.chinaunicombidding.cn/
- 公告列表：https://www.chinaunicombidding.cn/bidInformation

## 1. 已核实事实

公告列表页面公开展示：

- 标题“搜索公告”；
- 关键词输入框，占位文案“请输入公告关键词”；
- 时间快捷条件“不限、今天、近三天、近一周、近一月、自定义”；
- 页面为 Ant Design 风格单页应用，未执行 JavaScript 时仅提示启用 JavaScript；
- 某些非浏览器抓取环境会在页面底部看到“请求错误，请联系管理员。错误码：501”。

公开详情页 URL 已核实为：

```text
https://www.chinaunicombidding.cn/bidInformation/detail?id=<numeric-id>
```

详情页可公开读取，并稳定出现：

- 公告标题；
- 招标编号（部分公告可能为空或使用采购编号）；
- 发布时间，格式类似 `2026-04-02 18:19:35`；
- 公告正文；
- 附件区域（部分公告有附件）。

## 2. 当前判断

- 详情页公开且 URL 模式清晰；
- 列表页强依赖 JavaScript，真实 Adapter 必须使用 Playwright；
- 不能把静态抓取环境中的 501 直接解释为平台不可用，应先用真实浏览器验证；
- 列表搜索可能通过 XHR/Fetch 加载，实施时应同时观察 DOM 和网络响应，但不得依赖未公开、未经验证的内部接口作为唯一能力。

## 3. 页面契约

### 列表页指纹

必须同时满足至少两项：

- URL 路径为 `/bidInformation`；
- 可见“搜索公告”；
- 可见占位文案“请输入公告关键词”；
- 可见时间筛选“不限/今天/近三天/近一周/近一月”。

### 搜索动作

1. 等待 Ant Design 应用完成 hydration；
2. 定位关键词输入框并填入原始查询名称；
3. 点击文本为“搜索”的按钮；
4. 等待结果列表、明确无结果状态或明确错误状态三者之一；
5. 对结果标题做候选匹配，不因标题截断丢失原文；
6. 打开详情时校验 URL 符合 `/bidInformation/detail?id=数字`。

### 详情页指纹

- URL 满足详情模式；
- 页面有一级标题或主标题；
- 页面出现“发布时间”；
- 主体正文非空。

## 4. 失败和降级

- 未执行 JavaScript/仅出现启用 JavaScript提示：`PLATFORM_ERROR`，反馈为浏览器运行时不可用；
- 页面出现 501 且真实浏览器重试后仍存在：`PLATFORM_ERROR`；
- 搜索输入或搜索按钮缺失：`PAGE_CHANGED`；
- 结果列表成功加载且明确无结果：`NOT_FOUND`；
- 详情 URL 正常但正文为空：`PARTIAL` 或 `PAGE_CHANGED`，保留列表证据；
- 下载附件需要额外权限时，只记录附件，不进入未授权操作。

## 5. 证据要求

- 列表页搜索条件和结果同屏截图；
- 详情页全页截图；
- 标题、编号、发布时间和 URL 的结构化元数据；
- 如果列表报错，保存错误码、页面 URL、控制台和失败网络摘要；
- 附件只在公开可下载且文件类型/大小检查通过时保存。

## 6. 下一步任务

1. 用真实 Chrome 验证搜索提交方式、结果容器和无结果文案；
2. 捕获列表请求的请求方法、参数名和响应字段，仅作为辅助契约；
3. 准备 10 个真实样例和脱敏 fixture；
4. 实现列表搜索与详情解析分离的 Adapter；
5. 增加 Ant Design hydration、501 和空正文回归测试。
