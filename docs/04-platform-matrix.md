# 平台矩阵与验证台账

- 状态：Draft / requires live verification
- 日期：2026-07-20

> 本表是实施台账，不代表当前已经稳定抓取。每个平台启用前必须补齐真实入口、样例、登录方式、页面指纹和回归时间。

| Platform ID | 平台 | 初始类型判断 | 登录风险 | 当前阶段 | MVP 优先级 |
|---|---|---|---|---|---|
| `china-mobile` | 中国移动采购与招标网 | 公开检索 + 可能登录详情 | 中 | experimental | P0 |
| `china-unicom` | 中国联通采购与招标网 | JS 强交互公开检索 | 中 | experimental | P0 |
| `china-telecom` | 中国电信阳光采购网 | 公开检索 + 账号体系 | 中 | experimental | P1 |
| `china-tower-online` | 中国铁塔在线商务平台 | 登录/供应商业务为主 | 高 | experimental | P1 |
| `china-tower-eproc` | 中国铁塔电子采购平台 | 公开栏目 + 电子采购流程 | 中 | experimental | P0 |
| `cebpubservice` | 中国招标投标公共服务平台 | 公开检索 | 低 | experimental | P1 |
| `miit` | 工信部通信工程招投标管理平台 | 公开栏目检索 | 低 | experimental | P1 |
| `gd-gp` | 广东政府采购智慧云平台 | 公开采购公告检索 | 低/中 | experimental | P1 |
| `gd-ggzy` | 广东省公共资源交易平台 | 公开交易信息检索 | 低/中 | experimental | P1 |

## 单平台验证记录模板

每个平台建立 `docs/platforms/<platform-id>.md`，至少包含：

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

`experimental` → `pilot`：完成 10 个样例和人工接管。  
`pilot` → `enabled`：连续 5 个工作日回归通过，状态准确率和证据完整率达到 PRD 指标。  
任何连续结构失败或合规风险：降级为 `disabled`。
