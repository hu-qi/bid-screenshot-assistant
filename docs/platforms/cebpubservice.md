# 中国招标投标公共服务平台档案

- Platform ID：`cebpubservice`
- 状态：`contract-candidate / implementation-in-progress`
- 当前 Adapter：`experimental / disabled`
- last_verified_at：2026-07-20
- 生产入口：`https://bulletin.cebpubservice.com/`
- 可检索测试环境：`https://testbulletin.cebpubservice.com/`

## 已核实公开能力

- 全文检索与高级搜索；
- 招标公告、资格预审公告、中标候选人公示、中标结果公示、更正公告公示；
- 发布时间、行业、地区、来源渠道和发布媒介筛选；
- 详情公开展示标题、发布日期、发布媒介、来源渠道、公告内容、监督部门和附件入口。

## 候选搜索契约

生产环境历史公开搜索路径：

```text
/xxfbcmses/search/bulletin.html?categoryId=88&dates=300&page=1&showStatus=1
```

`categoryId=88` 仅作为招标公告候选值；其他分类编码、关键词参数和分页必须通过真实 Chrome 回归确认。

## 候选详情契约

```text
/<bulletin-category>/<YYYY-MM-DD>/<32-hex-id>.html
```

已观察到的目录包括：

- `biddingBulletin`
- `changeBulletin`
- `candidateBulletin`
- `resultBulletin`
- `qualifyBulletin`

## 验证码与人工边界

平台可能在检索或反自动化场景显示验证码。Adapter 遇到验证码、滑块或短信校验时必须返回 `CAPTCHA_REQUIRED`，保存当前页面证据并停止；不得识别、破解或绕过。

详情页的“上链查证”短信验证码区域不是公告浏览所需能力，Adapter 不点击、不填写。

## 启用门槛

- 真实生产 Chrome 完成 10+ 样例；
- 搜索输入、按钮、结果容器、无结果文案和分页确认；
- 验证码人工接管流程验证；
- 详情正文与附件证据完整；
- 连续回归通过后才能升级为 `pilot`。
