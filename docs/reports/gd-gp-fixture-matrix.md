# 广东政府采购智慧云平台 Fixture 矩阵

| Fixture / 测试 | 场景 | 预期状态或断言 |
|---|---|---|
| `search_found.json` | 官方检索命中，标题含高亮标签 | 还原标题、生成 API/门户 URL |
| `search_not_found.json` | `code=200` 且 `rows=[]` | `NOT_FOUND` |
| `detail_found.json` | 正文、采购人、项目编号、预算和附件 | 字段完整、外部附件过滤 |
| `test_adapter_found_writes_api_and_portal_evidence` | API 与门户均成功 | `FOUND` |
| `test_portal_capture_failure_is_partial_not_found` | API 成功、门户 403/失败 | `PARTIAL` |
| `test_invalid_search_contract_is_page_changed` | 非成功响应 | `PAGE_CHANGED` |

生产回归还需增加：分页、地区筛选、时间筛选、不同公告类型、门户站内点击、附件下载和限流场景。
