# 中国电信阳光采购网平台档案

- Platform ID：`china-telecom`
- 状态：`candidate-api-discovered / live-contract-pending`
- Adapter：未实现
- 更新日期：2026-07-20
- 官方入口：`https://caigou.chinatelecom.com.cn/`

## 1. 已确认边界

中国电信阳光采购网同时包含公开公告浏览与供应商业务流程。供应商注册、采购文件获取、应答、投标、CA 和交易操作不属于本助手的公开标讯截图范围。

第一版 Adapter 只允许：

- 查询公开公告；
- 打开公开公告详情；
- 保存查询页和详情页证据；
- 记录公开附件 URL。

## 2. 候选公开契约

近期公开代码显示，门户可能使用以下候选契约：

- 公告查询：`POST /portal/base/announcementJoin/queryListNew`
- 查询字段：`title`、`type`、`pageSize`、`pageNum`、`noticeSummary`、`provinceCode`
- 详情候选路由：`/DeclareDetails?id=<docId>&type=<type>&docTypeCode=<code>&securityViewCode=<code>`

查询中的 `type` 使用非语义字符串，并存在多种公告类型映射。上述信息只作为真实浏览器调查线索，未经过本项目的生产 Chrome 验证，不能直接标记为稳定协议。

## 3. 实施门槛

进入 Adapter 编码前必须通过真实 Chrome 确认：

1. 公开公告搜索入口；
2. 搜索请求是否确为公开、无需账号；
3. 公告类型与候选 `type` 的当前映射；
4. 明确命中和明确未命中的响应；
5. 详情 URL 与详情页稳定字段；
6. 分页和省份筛选；
7. 登录、验证码、短信和 CA 边界；
8. 是否存在请求签名、临时安全码或会话绑定。

## 4. 状态原则

- 未确认搜索请求完成时不得返回 `NOT_FOUND`；
- 公开查询被重定向登录时返回 `LOGIN_REQUIRED`；
- 图形验证、滑块、短信或其他人工验证返回 `CAPTCHA_REQUIRED`；
- 候选 API 或详情结构不符时返回 `PAGE_CHANGED`；
- 不使用供应商账号补齐公开公告能力，不自动获取采购文件。

## 5. 证据要求

真实调查需要保存：

- 首页和公告搜索入口截图；
- 搜索请求 URL、方法、状态和脱敏字段名；
- 命中/未命中结果截图；
- 详情页截图和 URL；
- 公告类型、标题、发布时间、项目编号、采购人和附件结构；
- 人工边界截图。

不得记录 Cookie、Token、密码、短信、CA/UKey 数据或 `securityViewCode` 的敏感值。

## 6. 当前结论

已获得候选 API 和详情路由线索，但尚不足以安全实现真实 Adapter。完成浏览器录制前保持 `experimental / disabled`，不加入真实 Registry。
