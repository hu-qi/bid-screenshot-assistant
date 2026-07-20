# CEB Fixture 验证矩阵

| 场景 | 预期状态 | 证据要求 |
|---|---|---|
| 标题命中且详情可读 | FOUND | 搜索页、详情页、详情 metadata |
| 搜索完成且明确空结果 | NOT_FOUND | 搜索页、search-signals |
| 搜索完成无法证明 | PAGE_CHANGED | 搜索页、诊断信息 |
| 搜索或详情出现安全验证 | CAPTCHA_REQUIRED | 当前页面证据，停止执行 |
| 列表命中但详情失败 | PARTIAL | 列表命中、detail-errors |
| 外部详情或附件 | 忽略 | 不导航、不下载 |

该矩阵只证明离线契约和状态机，不代表生产站点已回归通过。
