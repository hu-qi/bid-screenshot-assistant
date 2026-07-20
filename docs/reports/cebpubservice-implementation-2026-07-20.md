# 中国招标投标公共服务平台 Adapter 实现报告

- 日期：2026-07-20
- Platform ID：`cebpubservice`
- 状态：`implemented / fixture-tested / live-regression-pending`

## 1. 目标

实现公开公告搜索与证据采集，同时把验证码、滑块、短信查证和反自动化页面作为人工边界，禁止任何识别或绕过。

## 2. 实现结构

```text
src/bid_screenshot_assistant/adapters/cebpubservice/
├── adapter.py
├── driver.py
├── models.py
└── parser.py
```

## 3. 候选契约

生产搜索路径候选：

```text
/xxfbcmses/search/bulletin.html?categoryId=88&dates=300&page=1&showStatus=1
```

详情候选：

```text
/<biddingBulletin|qualifyBulletin|candidateBulletin|resultBulletin|changeBulletin>/<YYYY-MM-DD>/<32-hex-id>.html
```

这些路径通过公开测试环境、公开页面和近期第三方实现交叉确认，但生产环境仍需真实 Chrome 回归。

## 4. 状态机

- `FOUND`：搜索完成，标题达到匹配阈值，详情页通过发布日期/标题契约；
- `NOT_FOUND`：搜索完成且出现明确无结果状态；
- `CAPTCHA_REQUIRED`：出现图形验证码、滑块或安全验证，立即停止；
- `PARTIAL`：列表命中但部分详情失败；
- `PAGE_CHANGED`：输入、搜索、结果或详情契约不匹配；
- `TIMEOUT`、`PLATFORM_ERROR`：超时和明确平台异常。

## 5. 证据

- `result-page.png`
- `search-signals.json`
- `detail-NNN.png`
- `detail-NNN.json`
- 可选 `detail-errors.json`
- summary、manifest、report、ZIP

## 6. 安全边界

- 只允许生产公告域名；
- 只打开已知公告类型目录和 32 位标识详情；
- 外部详情与附件链接过滤；
- 验证码不识别、不刷新轰炸、不绕过；
- “上链查证”的手机号/短信验证码不填写；
- 不执行发布、注册、登录、付款、报名或投标。

## 7. Fixture 测试

覆盖：

- 正常列表命中；
- 明确未命中；
- 验证码人工边界；
- 详情字段与同域附件；
- 外链过滤；
- 详情失败保留列表命中；
- 搜索完成无法证明时不返回 `NOT_FOUND`。

## 8. 未完成

- 生产 Chrome 搜索回归；
- 当前关键词 input、按钮和结果容器最终定位；
- categoryId 与五种公告分类映射；
- 分页与日期/行业/地区筛选；
- 真实验证码人工接管恢复；
- 公告正文 iframe/附件下载策略；
- 10+ 样例和 Playwright Trace。

完成上述项目之前保持 `experimental / disabled`。
