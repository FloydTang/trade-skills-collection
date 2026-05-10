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
- `source_name`
- `source_url_or_note`
- `freshness`
- `confidence`
- `match_basis`

来源字段用于承接客户搜索 Skill 的数据源适配层。海关数据、展会名单、协会名单、CRM / Excel 或历史成交数据进入整理阶段后，应继续保留来源名称、匹配依据、新鲜度和可信度，不能只保留公司名。

## 最小可执行要求

每条线索至少提供以下任一字段：

- `company_name`
- `company_website`
- `email`
- `person_name`

如果完全为空，脚本应直接报错。
