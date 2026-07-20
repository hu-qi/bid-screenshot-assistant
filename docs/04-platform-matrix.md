# 平台矩阵与验证台账

- 状态：Draft / live verification in progress
- 日期：2026-07-20

> 本表是实施台账，不代表当前已经稳定抓取。平台启用前必须完成真实样例和回归。

| Platform ID | 平台 | 入口形态 | 当前阶段 | 优先级 | 平台档案 |
|---|---|---|---|---|---|
| `china-mobile` | 中国移动采购与招标网 | 公开首页、候选数字 ID 详情 | implemented / fixture-tested / live-regression-pending | P0 | [查看](platforms/china-mobile.md) |
| `china-unicom` | 中国联通采购与招标网 | JS 公告列表、数字 ID 详情 | implemented / fixture-tested / live-regression-pending | P0 | [查看](platforms/china-unicom.md) |
| `china-telecom` | 中国电信阳光采购网 | 候选公开查询 API 与详情路由，待真实浏览器确认 | candidate-api-discovered / live-contract-pending | P1 | [查看](platforms/china-telecom.md) |
| `china-tower-online` | 中国铁塔在线商务平台 | 待调查 | experimental | P1 | 待创建 |
| `china-tower-eproc` | 中国铁塔电子采购平台 | 公开分类列表与详情 | implemented / fixture-tested / live-regression-pending | P0 | [查看](platforms/china-tower-eproc.md) |
| `cebpubservice` | 中国招标投标公共服务平台 | 全文/高级检索、五类公告详情 | implemented / fixture-tested / production-live-regression-pending | P1 | [查看](platforms/cebpubservice.md) |
| `miit` | 工信部通信工程招投标管理平台 | 待调查 | experimental | P1 | 待创建 |
| `gd-gp` | 广东政府采购智慧云平台 | 公开全文检索/详情 API、门户详情候选路由 | implemented / fixture-tested / live-regression-pending | P1 | [查看](platforms/gd-gp.md) |
| `gd-ggzy` | 广东省公共资源交易平台 | 入口已确认，交易信息流待浏览器录制 | discovery-pending | P1 | [查看](platforms/gd-ggzy.md) |

## 当前实现状态

1. 中国移动、中国联通、中国铁塔电子采购平台：代码与 Fixture 完成，生产 Chrome 回归待补；
2. 中国招标投标公共服务平台：代码与 Fixture 完成，生产检索和人工处理流程待回归；
3. 广东政府采购智慧云平台：代码与 Fixture 完成，公开 API 和门户截图回归待补；
4. 中国电信已发现候选公开 API 和详情路由，待真实浏览器确认后编码；
5. 广东公共资源待真实页面录制；
6. 工信部与中国铁塔在线商务平台待调查。

## 验证记录要求

- 官方入口、搜索条件和分页；
- 无结果、登录和人工处理页面状态；
- 详情页与附件结构；
- 10+ 真实测试样例；
- Adapter 版本、验证日期、限制和回归证据。

## 启用门槛

`experimental` → `pilot`：完成真实样例、状态分类和人工处理验证。  
`pilot` → `enabled`：连续 5 个工作日回归通过并达到 PRD 指标。  
出现连续结构失败或合规风险时降级为 `disabled`。
