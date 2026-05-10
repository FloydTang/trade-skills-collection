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
- `data_sources`

## 数据源字段

`data_sources` 用于接入用户授权提供的更高质量来源，例如海关数据导出、展会名单、行业协会名单、同行内推清单、企业 CRM / Excel 或历史成交数据。

每个数据源建议包含：

- `source_type`：`web`、`linkedin`、`customs`、`trade_show`、`association`、`crm`、`referral`、`manual_import` 等。
- `source_name`：数据源名称，例如“2025 波兰冷冻食品海关数据导出”。
- `authorization_status`：`user_provided`、`authorized` 或 `public`。私有或付费数据必须由用户提供或授权。
- `source_url_or_note`：来源链接、账号说明、文件名或导出说明。
- `field_mapping`：企业原始字段到标准字段的映射。
- `records`：实际记录数组。

海关数据记录可包含 `importer_name`、`exporter_name`、`hs_code`、`product_keywords`、`trade_partner`、`trade_period`、`shipment_date` 等字段。脚本只把这些字段作为匹配依据，不把贸易记录直接等同为采购意向。

## 默认行为

- `search_keywords` 可以是字符串数组，也可以是逗号分隔字符串
- `max_results` 默认 6
- `must_include` 和 `exclude_terms` 只影响查询词拼接与结果过滤，不做复杂语义约束
- 未提供 `data_sources` 时，继续走公开网页和 LinkedIn 线索发现。
