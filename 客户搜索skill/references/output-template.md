# 输出模板

输出默认包含：

## search_strategy

- `strategy_summary`
- `query_plan`
- `exclude_terms`
- `must_include`
- `notes`

## summary

- `product_or_offer`
- `target_market`
- `customer_type`
- `queries`
- `raw_result_count`
- `candidate_count`

## candidates

每条候选至少包含：

- `candidate_id`
- `company_name`
- `company_website`
- `source_url`
- `linkedin_url`
- `country_or_market`
- `visible_contact_clues`
- `search_snippet`
- `search_query_used`
- `evidence_grade`
- `match_reason`
- `missing_fields`
- `evidence_summary`
- `next_action`
- `follow_up_suggestion`
- `source_type`

## lead_screening_input

必须兼容 `线索整理skill/` 输入字段：

- `company_name`
- `company_website`
- `person_name`
- `email`
- `country_or_market`
- `source_url`
- `linkedin_url`
- `notes`
- `evidence_grade`
- `match_reason`
- `evidence_summary`
- `discovery_missing_fields`
- `discovery_next_action`
- `source_type`
