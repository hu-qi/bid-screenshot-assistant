# 平台调查档案

本目录记录每个平台在真实公开页面上的可验证事实、页面契约、失败边界和下一步实现任务。

## 状态定义

- `entry-verified`：官方入口和公开页面已核实；
- `flow-mapped`：搜索、结果、详情和无结果流程已在真实浏览器中走通；
- `fixture-ready`：已提交脱敏 HTML/网络响应/截图基线；
- `adapter-pilot`：真实 Adapter 已实现并在受控环境试跑；
- `enabled`：满足平台矩阵中的生产门槛。

## 规则

1. 只记录已经观察到的事实；推测必须标记为“待验证”。
2. 页面文案可作为辅助定位器，但正式 Adapter 需同时保存页面指纹和回归样例。
3. 公告公开浏览与报名、领标书、投标是不同权限边界，不能混为一谈。
4. 遇到登录、验证码、风控或权限门，转人工接管，不设计绕过方案。
5. 每次平台改版必须更新档案中的 `last_verified_at`、Adapter 版本和已知差异。

## 当前优先级

1. [`china-tower-eproc.md`](china-tower-eproc.md)：公开列表和详情结构最完整，优先实现。
2. [`china-unicom.md`](china-unicom.md)：详情公开，但列表为 JavaScript 单页应用，需要 Playwright 网络与 DOM 双重观察。
3. [`china-mobile.md`](china-mobile.md)：公开首页可确认搜索入口，结果流仍需真实浏览器侦察。
