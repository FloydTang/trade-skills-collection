# 输入字段说明

## 顶层字段

- `default_country_or_market`
  用于给未单独填写国家市场的线索补默认值。
- `operator_notes`
  整批线索的补充说明，可进入输出摘要。
- `leads`
  线索数组。每条线索至少提供一个有效线索字段。

## 单条线索字段

- `company_name`
- `company_website`
- `person_name`
- `email`
- `country_or_market`
- `source_url`
- `linkedin_url`
- `notes`
- `product_keywords`
- `source_type`

## 最小可执行要求

每条线索至少提供以下任一字段：

- `company_name`
- `company_website`
- `email`
- `person_name`

如果完全为空，脚本应直接报错。
