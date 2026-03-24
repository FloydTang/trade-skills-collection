# 输入字段说明

## 必填字段

- `product_or_offer`
- `target_market`
- `customer_type`
- `search_keywords`

## 可选字段

- `must_include`
- `exclude_terms`
- `max_results`
- `notes`

## 默认行为

- `search_keywords` 可以是字符串数组，也可以是逗号分隔字符串
- `max_results` 默认 6
- `must_include` 和 `exclude_terms` 只影响查询词拼接与结果过滤，不做复杂语义约束
