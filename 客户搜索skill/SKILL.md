---
name: trade-lead-discovery
description: Find the first batch of foreign-trade prospect companies from public web and LinkedIn result clues, then output a conservative, structured candidate list ready for lead screening. Use when an operator knows the product, market, and customer type but needs reproducible search queries, source links, visible contact clues, and follow-up suggestions.
---

# 客户搜索 / 线索发现 Skill

## Overview

用这个 Skill 把“知道大概要找哪类客户，但不会系统搜客户”的问题，变成可复用的公开搜索流程。

首版重点：

- 用通用网页搜索发现官网、目录页、展会页和 B2B 结果
- 用 LinkedIn 结果线索补公司页与可见联系人线索
- 输出结构化候选名单
- 给出补查建议
- 生成可直接进入 `线索整理skill/` 的标准输入

## Standard Input

输入统一为 JSON：

```json
{
  "product_or_offer": "frozen mixed vegetables",
  "target_market": "Poland",
  "customer_type": "importer",
  "search_keywords": [
    "frozen food importer",
    "private label frozen vegetables"
  ],
  "must_include": [
    "retail"
  ],
  "exclude_terms": [
    "job",
    "recruitment"
  ],
  "max_results": 6,
  "notes": ""
}
```

## Workflow

1. Normalize search inputs and build a fixed set of search queries.
2. Search public-web results and LinkedIn company-result clues.
3. Dedupe raw search results by URL.
4. Group results into candidate companies using website, LinkedIn URL, or normalized company name.
5. Build a structured candidate list with source links, visible contact clues, and follow-up suggestions.
6. Generate a lead-screening bridge payload for downstream use.

## Output Requirements

- 必须包含查询摘要
- 必须包含结构化候选名单
- 必须包含来源链接
- 必须包含至少官网或 LinkedIn 线索字段
- 必须包含 `follow_up_suggestion`
- 必须包含可桥接到 `线索整理skill/` 的输出
- 不能把搜索结果写成客户价值判断

## Main Scripts

- [build_lead_discovery_report.py](./scripts/build_lead_discovery_report.py)
- [build_lead_screening_input.py](./scripts/build_lead_screening_input.py)

### Example

```bash
python3 ./scripts/build_lead_discovery_report.py --input-json ./examples/frozen-food-search.json
```

```bash
python3 ./scripts/build_lead_screening_input.py --input-json ./examples/frozen-food-output.json
```

```bash
python3 ./scripts/run_regression_checks.py
```

## Defaults

- 首版允许联网
- 首版只用公开结果，不用登录态
- 首版只做候选发现，不做深度背调
- 首版输出优先衔接线索整理 Skill
