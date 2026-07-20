# 广东政府采购智慧云平台运行手册

## 实验运行

```bash
bid-screenshot gd-gp \
  --acknowledge-experimental \
  --query "项目名称" \
  --headed
```

## 结果判断

- `FOUND`：API 与门户截图均完成；
- `PARTIAL`：至少一个官方公告命中，但详情 API 或门户截图有失败；
- `NOT_FOUND`：官方搜索 API 明确返回空 rows；
- `PAGE_CHANGED`：响应结构或 URL 契约不符合预期；
- `TIMEOUT` / `PLATFORM_ERROR`：技术异常。

## 故障排查

1. 查看 `capture-errors.json`；
2. 判断失败发生在 search API、detail API 还是 portal；
3. 核对 `summary.json` 和 manifest；
4. 门户 403 时不要改成绕过逻辑，先验证站内导航；
5. API 非 200 时保存响应并暂停 Adapter；
6. 更新 Fixture、平台档案和实现报告后再恢复。
