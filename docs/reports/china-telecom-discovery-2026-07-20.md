# 中国电信阳光采购网公开公告调查记录

- 日期：2026-07-20
- Platform ID：`china-telecom`
- 状态：`candidate-api-discovered / live-contract-pending`

## 1. 调查目标

确认中国电信阳光采购网中无需登录即可访问的公告查询和详情流程，并与供应商注册、文件获取、应答、投标和 CA 操作严格分离。

## 2. 当前线索

近期第三方公开实现使用：

```text
POST https://caigou.chinatelecom.com.cn/portal/base/announcementJoin/queryListNew
```

候选请求体：

```json
{
  "title": "项目名称",
  "type": "公告类型候选值",
  "pageSize": 10,
  "pageNum": 1,
  "noticeSummary": "",
  "provinceCode": ""
}
```

候选详情路由：

```text
https://caigou.chinatelecom.com.cn/DeclareDetails
  ?id=<docId>
  &type=<type-id>
  &docTypeCode=<doc-type-code>
  &securityViewCode=<security-view-code>
```

已观察到多个非语义 `type` 值和数字类型映射。这些值可能随前端版本变化，也可能与会话或公告类别绑定，因此不能未经验证直接固化为生产契约。

## 3. 真实录制计划

### 入口

- 公开首页；
- 公告栏目；
- 搜索框、公告类型、省份和时间筛选；
- 搜索按钮与结果刷新信号。

### 样例

- 5 个已知命中项目；
- 3 个随机未命中项目；
- 多公告类型项目；
- 一个详情不可访问或安全码失效场景。

### 记录

- accessibility snapshot；
- 全页截图；
- DOM 摘要；
- 网络请求 URL、方法、状态和脱敏字段名；
- 详情 URL 形态；
- 登录/验证码/短信/CA 边界。

## 4. 安全与合规

- 不复用第三方硬编码安全码；
- 不读取或导出账号、Cookie、Token、密码、短信或 CA 数据；
- 不自动注册、登录、下载采购文件、应答或投标；
- 不通过反复请求消耗验证码或规避限流；
- 公开公告能力不足时返回人工处理或明确失败，不以登录账号补齐。

## 5. Adapter 计划

真实契约确认后，按以下结构实施：

```text
src/bid_screenshot_assistant/adapters/china_telecom/
├── __init__.py
├── adapter.py
├── driver.py
├── models.py
└── parser.py
```

至少覆盖：

- `FOUND`
- `NOT_FOUND`
- `PARTIAL`
- `LOGIN_REQUIRED`
- `CAPTCHA_REQUIRED`
- `PAGE_CHANGED`
- `TIMEOUT`
- `PLATFORM_ERROR`

## 6. 当前决定

本轮只提交平台档案、候选契约和真实录制清单，不提交依据不足的 Adapter。真实浏览器验证完成后再编码，避免把第三方历史参数误认为当前官方协议。
