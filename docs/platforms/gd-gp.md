# 广东政府采购智慧云平台档案

- Platform ID：`gd-gp`
- 状态：`implemented / fixture-tested / live-regression-pending`
- Adapter：`experimental / disabled`
- 更新日期：2026-07-20
- 官方入口：`https://gdgpo.czt.gd.gov.cn/`

## 1. 已核实的公开能力

广东政府采购公开门户提供采购公告、结果公告等公开信息。当前实现使用以下公开契约：

- 全文检索：`/gpcms/rest/web/v2/info/selectInfoForIndex`
- 详情数据：`/gpcms/rest/web/v2/info/getInfoById?id=<record-id>`
- 门户详情候选路由：`/noticeGd`、`/articleGd`、`/articleRedHeadGd`、`/noticeKjxyGd`

检索响应可包含标题、公告时间、公告类型、采购人、地区、项目编号、渠道和记录 ID。详情响应可包含公告正文、采购方式、预算和公开附件。

## 2. 双证据策略

### 必需证据

- 官方检索 API 响应截图；
- 官方详情 API 响应截图；
- 解析后的 metadata、原始 URL、采集时间和 SHA-256。

### 增强证据

- 人类可读的门户公告页截图。

部分 SPA 历史路由可能在直接打开时返回 403，即使从站内点击可访问。门户截图失败时，任务返回 `PARTIAL`；不会把 API 成功声明为完整页面截图成功。

## 3. 搜索参数基线

第一版实验 Adapter 使用：

- `siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a`
- 两个公开公告渠道；
- `searchKey=<项目名称>`；
- `selectTimeName=noticeTime`；
- 默认每页 20 条；
- 当前暂用 2000-01-01 至执行当日的宽时间范围。

真实回归后应把日期范围暴露为任务参数，并验证分页和渠道覆盖。

## 4. URL 与附件边界

只允许：

- HTTPS；
- `gdgpo.czt.gd.gov.cn`；
- 已登记的详情 API 和四类门户路由。

附件当前只记录同域公开 URL，不自动下载。外部域名附件会被过滤。后续下载必须增加 MIME、大小、扩展名和恶意文件隔离。

## 5. 状态判定

- API 返回 `code=200` 且 `rows=[]`：`NOT_FOUND`；
- 搜索或详情响应不是成功 JSON：`PAGE_CHANGED`；
- 详情 API 成功、门户页失败：`PARTIAL`；
- 详情 API 和门户页均成功：`FOUND`；
- 单条详情失败时保留列表命中并输出诊断；
- 超时与平台错误分别返回 `TIMEOUT`、`PLATFORM_ERROR`。

## 6. 当前测试资产

- `tests/fixtures/gd_gp/search_found.json`
- `tests/fixtures/gd_gp/search_not_found.json`
- `tests/fixtures/gd_gp/detail_found.json`
- `tests/test_gd_gp_parser.py`
- `tests/test_gd_gp_adapter.py`

覆盖标题高亮还原、空结果、详情字段、同域附件、外部附件过滤、门户失败降级和错误响应。

## 7. 未完成

1. 10+ 生产 Chrome 样例；
2. 当前公开门户路由的站内点击回放；
3. 日期、地区、采购方式和公告类型筛选；
4. 分页；
5. 更多 channel/noticeType 路由映射；
6. 公开附件下载与文件安全检查；
7. Playwright Trace 与脱敏网络摘要；
8. 连续多日回归。

完成前保持 `experimental / disabled`。
