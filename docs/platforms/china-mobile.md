# 中国移动采购与招标网平台档案

- Platform ID：`china-mobile`
- 状态：`implemented / fixture-tested / live-regression-pending`
- 当前 Adapter：`experimental / disabled`
- last_verified_at：2026-07-20
- 官方公开入口：https://b2b.10086.cn/

## 1. 已核实事实

官方首页公开展示：

- 全站搜索框，占位文案“请输入公告标题包含的关键字”；
- 分类“全部、招标采购公告、供应商公告、采购服务、系统通知、重点信息”；
- 招标大厅“正在招标、即将开标、正在候选人公示”；
- 首页初始状态可能出现“无匹配数据”；
- 供应商、专家和员工登录与公开公告入口同页但属于不同权限边界。

公开资料持续引用两类详情链接：

```text
https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id=<numeric-id>
https://b2b.10086.cn/b2b/main/viewVendorNoticeContent.html?noticeBean.id=<numeric-id>
```

第一类用于采购/候选人/结果等公开公告；第二类用于供应商通知。它们已加入**候选 URL 白名单**，但仍需真实 Playwright 回归确认当前站内搜索是否继续返回相同形态。

## 2. 当前实现

代码：

```text
src/bid_screenshot_assistant/adapters/china_mobile/
├── adapter.py
├── driver.py
├── models.py
└── parser.py
```

已实现：

- 使用 Playwright 打开公开首页；
- 通过占位文案定位搜索输入框；
- 优先点击“搜索”，不可见时使用回车；
- 记录 URL 变化、详情链接数量变化、公告相关网络响应或查询词进入结果区等完成信号；
- 解析候选详情链接、标题、公告类型和日期；
- 采集搜索结果页和详情页 PNG；
- 保存搜索信号、详情 metadata 和详情失败诊断；
- 过滤外部详情链接和外部附件；
- 支持 `FOUND`、`NOT_FOUND`、`PARTIAL`、`PAGE_CHANGED`、`TIMEOUT`、`PLATFORM_ERROR`。

## 3. 关键状态规则

### NOT_FOUND

只有同时满足以下条件才允许返回：

1. 查询词已填写；
2. 搜索完成信号已被验证；
3. 页面没有达到匹配阈值的合法详情链接；
4. 页面出现明确“无匹配数据/暂无数据”等状态。

首页初始“无匹配数据”、搜索提交无法确认、结果区域未刷新，均返回 `PAGE_CHANGED`，不能返回 `NOT_FOUND`。

### FOUND

- 仅接受官方 HTTPS 域名；
- 详情 URL 必须符合候选白名单；
- 标题匹配分不低于 0.55；
- 详情页至少需要可提取标题和非空正文。

### PARTIAL

列表候选可用但单个详情无法打开、正文结构变化或截图失败时，保留列表命中并记录 `detail-errors.json`。

## 4. 安全边界

- 仅访问 `b2b.10086.cn`；
- 不访问 `es.b2b.10086.cn/newbid/` 的登录后电子投标流程；
- 不执行供应商注册、登录、购标、付款、文件递交、投标、异议或 CA 操作；
- 不读取或提交 Cookie、密码、短信、二维码或证书；
- 附件只记录同域公开链接，尚不自动下载。

## 5. Fixture 测试

```text
tests/fixtures/china_mobile/
├── list_found.html
├── list_not_found.html
└── detail_found.html
```

覆盖：

- 正常命中和详情证据；
- 外部详情链接过滤；
- 同域附件识别与外部附件过滤；
- 搜索完成后的明确未命中；
- 首页初始空状态不能判为未命中；
- 单个详情失败转为 `PARTIAL`；
- 模糊空页面转为 `PAGE_CHANGED`。

## 6. 实验命令

```bash
pip install -e '.[dev,browser]'
playwright install chromium

bid-screenshot mobile \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

## 7. 未完成

- 受控真实 Chrome 搜索回归；
- 5 个已知命中、3 个随机未命中及异常样例；
- 当前搜索按钮/图标的最终 locator；
- 真实搜索响应和 DOM 刷新信号确认；
- 当前结果容器、公告类型字段和分页；
- 当前详情页稳定字段和附件下载；
- Playwright trace 与脱敏网络摘要。

完成上述回归前保持 `experimental / disabled`，不得升级为 `pilot`。
