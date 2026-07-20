# 平台矩阵与验证台账

- 状态：Draft / live verification in progress
- 日期：2026-07-20

> 本表是实施台账，不代表当前已经稳定抓取。每个平台启用前必须补齐真实入口、样例、登录方式、页面指纹和回归时间。

| Platform ID | 平台 | 已验证入口形态 | 登录风险 | 当前阶段 | 默认启用 | MVP 优先级 | 平台档案 |
|---|---|---|---|---|---|---|---|
| `china-mobile` | 中国移动采购与招标网 | 公开首页标题搜索；结果流待 Playwright 核实 | 中 | entry-verified | 否 | P0 | [查看](platforms/china-mobile.md) |
| `china-unicom` | 中国联通采购与招标网 | JS 公告列表；公开详情支持数字 ID | 中 | adapter-implemented / fixture-tested / live-regression-pending | 否 | P0 | [查看](platforms/china-unicom.md) |
| `china-telecom` | 中国电信阳光采购网 | 待调查 | 中 | experimental | 否 | P1 | 待创建 |
| `china-tower-online` | 中国铁塔在线商务平台 | 待调查 | 高 | experimental | 否 | P1 | 待创建 |
| `china-tower-eproc` | 中国铁塔电子采购平台 | 公开分类列表、筛选和详情 URL 模式 | 中 | adapter-implemented / fixture-tested / live-regression-pending | 否 | P0 | [查看](platforms/china-tower-eproc.md) |
| `cebpubservice` | 中国招标投标公共服务平台 | 待调查 | 低 | experimental | 否 | P1 | 待创建 |
| `miit` | 工信部通信工程招投标管理平台 | 待调查 | 低 | experimental | 否 | P1 | 待创建 |
| `gd-gp` | 广东政府采购智慧云平台 | 待调查 | 低/中 | experimental | 否 | P1 | 待创建 |
| `gd-ggzy` | 广东省公共资源交易平台 | 待调查 | 低/中 | experimental | 否 | P1 | 待创建 |

## 当前实现顺序

1. 中国铁塔电子采购平台：Adapter 已实现并完成 Fixture/状态机测试，待真实浏览器回归；
2. 中国联通：Adapter 已实现并完成 Fixture/状态机测试，待真实浏览器回归；
3. 中国移动：先完成搜索结果流和详情 URL 侦察，再实现；
4. 其余平台按公开程度、业务优先级和登录风险依次推进。

## 单平台验证记录要求

每个平台档案至少包含：

- 官方入口和备用入口；
- 搜索页面 URL；
- 是否必须登录；
- 搜索字段和日期/类型筛选；
- 结果加载方式（服务端、XHR、JS）；
- 分页机制；
- 无结果页面指纹；
- 详情页与附件结构；
- 验证码/风控场景；
- 10+ 测试样例；
- 最近验证日期、Adapter 版本和负责人；
- 已知限制和回归截图。

## 启用门槛

`experimental` → `pilot`：完成至少 10 个真实样例和人工接管验证。  
`pilot` → `enabled`：连续 5 个工作日回归通过，状态准确率和证据完整率达到 PRD 指标。  
任何连续结构失败或合规风险：降级为 `disabled`。
