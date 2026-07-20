# 中国移动公开公告 Adapter 实现报告

- 日期：2026-07-20
- Platform ID：`china-mobile`
- 状态：`implemented / fixture-tested / live-regression-pending`
- 关联 Issue：#4

## 1. 实施目标

在不进入供应商登录和电子投标系统的前提下，为中国移动采购与招标网公开首页建立证据优先的实验 Adapter，并解决首页初始“无匹配数据”容易被误判为真实未命中的问题。

## 2. 实现结构

```text
src/bid_screenshot_assistant/adapters/china_mobile/
├── __init__.py
├── adapter.py       # 业务状态机与证据写入
├── driver.py        # Playwright 导航、搜索和完成信号
├── models.py        # 页面快照、列表候选和详情模型
└── parser.py        # 列表/详情/日期/公告类型/附件解析
```

## 3. 页面契约

### 公开入口

- `https://b2b.10086.cn/`
- 搜索占位文案：`请输入公告标题包含的关键字`
- 首页指纹：`招标采购公告`

### 候选详情 URL

```text
/b2b/main/viewNoticeContent.html?noticeBean.id=<numeric-id>
/b2b/main/viewVendorNoticeContent.html?noticeBean.id=<numeric-id>
```

这些形态有历史采集实现和近期公开资料引用支撑，但本报告不将其表述为已经完成 2026 年真实站内回放。

## 4. 搜索完成证明

Driver 不使用“页面出现无匹配数据”作为唯一完成信号。搜索完成至少需要以下之一：

- 页面 URL 发生变化；
- 合法详情链接数量发生变化；
- 官方域名产生包含 notice/search/list 的 XHR、Fetch 或 Document 响应；
- 原页面没有的查询词进入结果区域。

未获得这些信号时，即使页面出现“无匹配数据”，也返回 `PAGE_CHANGED`。

## 5. 证据

每个执行项生成：

- `result-page.png`；
- `search-signals.json`；
- `detail-NNN.png`；
- `detail-NNN.json`；
- 可选 `detail-errors.json`；
- 汇总、manifest、报告和 ZIP。

所有真实页面文件均标记 `simulation=false`，运行模式为 `experimental-live`。

## 6. 安全控制

- HTTPS 和官方域名白名单；
- 详情 URL 正则白名单；
- 外部详情和外部附件过滤；
- 不进入 `es.b2b.10086.cn/newbid/`；
- 不执行登录、CA、报名、购标、付款、递交或投标；
- 搜索需显式 `--acknowledge-experimental`。

## 7. 自动测试

解析器测试：

- 合法详情解析；
- 日期和公告类型；
- 同域附件；
- 外链过滤；
- 非法详情 URL 拒绝。

状态机测试：

- `FOUND`；
- 搜索完成后的 `NOT_FOUND`；
- 首页初始空状态 → `PAGE_CHANGED`；
- 详情失败 → `PARTIAL`；
- 完成但无结果标记/候选 → `PAGE_CHANGED`。

## 8. 当前限制

- 没有当前真实 Chrome 录制；
- 搜索结果容器和分页未被真实回放确认；
- 候选详情 URL 尚未完成当前站内搜索链接验证；
- 未下载附件；
- 未实现公告分类选择；
- 未形成 8 个以上真实测试样例和 Trace。

因此 Adapter 继续保持默认关闭。
