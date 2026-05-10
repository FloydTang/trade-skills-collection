# 输出模板

输出默认包含两层：

1. `summary`
2. `leads`

## summary

- `total_leads`
- `ready_for_customer_intel`
- `need_enrichment`
- `manual_review`
- `operator_notes`

## leads

每条线索至少包含：

- `lead_id`
- `normalized_company_name`
- `normalized_person_name`
- `email`
- `email_domain_clue`
- `company_website`
- `country_or_market`
- `evidence_grade`
- `source_type`
- `source_name`
- `source_url_or_note`
- `freshness`
- `confidence`
- `match_basis`
- `discovery_next_action`
- `lead_bucket`
- `missing_fields`
- `manual_review_reasons`
- `recommended_next_action`
- `legacy_recommended_next_action`
- `follow_up_suggestions`
- `customer_intel_input`

其中 `customer_intel_input` 必须兼容 `客户背调skill/` 当前标准输入：

- `company_name`
- `person_name`
- `email`
- `company_website`
- `country_or_market`
- `notes`

`notes` 中应保留来源摘要、匹配依据、新鲜度和可信度，方便客户背调阶段继续判断证据强弱。
