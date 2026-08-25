# Lead Discovery Package

## Summary
- Product/Offer: frozen mixed vegetables
- Target Market: Poland
- Customer Type: importer
- Raw Result Count: 7
- Candidate Count: 3
- Data Sources: 0

## Search Strategy
- Strategy Summary: 先用产品 + 市场 + 客户类型构造主查询，再补角色词、LinkedIn 公司页线索和 must_include 限定词。如用户提供海关数据、展会名单、行业协会名单或企业自有表格，则作为授权数据源同步归并。
- Query Plan:
- frozen mixed vegetables Poland importer
- frozen food importer Poland importer distributor brand buyer
- site:linkedin.com/company frozen mixed vegetables Poland importer
- frozen mixed vegetables Poland importer "retail"
- Must Include: retail
- Exclude Terms: job, recruitment

## candidate-001
- Company: Baltic Frozen Trade
- Website: https://balticfrozentrade.pl
- LinkedIn: https://www.linkedin.com/company/baltic-frozen-trade
- Source URL: https://balticfrozentrade.pl
- Country/Market: Poland
- Source Type: web
- Source Name: fixture
- Source URL/Note: https://balticfrozentrade.pl
- Freshness: unknown
- Confidence: medium
- Match Basis: 命中搜索查询：frozen food importer Poland importer distributor brand buyer
- Evidence Grade: A
- Next Action: ready_for_screening
- Visible Contact Clues: (none)
- Search Snippet: Supplier and importer of frozen vegetables and fruit for private label retail in Poland.
- Search Query Used: frozen food importer Poland importer distributor brand buyer, site:linkedin.com/company frozen mixed vegetables Poland importer
- Evidence Summary: 当前候选主要基于官网、LinkedIn、数据源 fixture形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 A：来源：fixture；命中搜索查询：frozen food importer Poland importer distributor brand buyer；有官网主体线索；有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: visible_contact_clues
- Follow-up Suggestion: 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。

## candidate-002
- Company: GreenHarvest Foods
- Website: https://greenharvestfoods.com
- LinkedIn: https://www.linkedin.com/company/greenharvestfoods
- Source URL: https://greenharvestfoods.com
- Country/Market: Poland
- Source Type: web
- Source Name: fixture
- Source URL/Note: https://greenharvestfoods.com
- Freshness: unknown
- Confidence: medium
- Match Basis: 命中搜索查询：frozen mixed vegetables Poland importer
- Evidence Grade: A
- Next Action: ready_for_screening
- Visible Contact Clues: anna@greenharvestfoods.com, Retail
- Search Snippet: GreenHarvest Foods imports frozen vegetables for retail and private label programs in Poland.
- Search Query Used: frozen mixed vegetables Poland importer, frozen food importer Poland importer distributor brand buyer, frozen mixed vegetables Poland importer "retail", site:linkedin.com/company frozen mixed vegetables Poland importer
- Evidence Summary: 当前候选主要基于官网、LinkedIn、2 条可见联系人线索、数据源 fixture形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 A：来源：fixture；命中搜索查询：frozen mixed vegetables Poland importer；有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: (none)
- Follow-up Suggestion: 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。

## candidate-003
- Company: PolFood Sourcing directory profile
- Website: https://directory.example/polfood-sourcing
- LinkedIn: (missing)
- Source URL: https://directory.example/polfood-sourcing
- Country/Market: Poland
- Source Type: web
- Source Name: fixture
- Source URL/Note: https://directory.example/polfood-sourcing
- Freshness: unknown
- Confidence: medium
- Match Basis: 命中搜索查询：frozen mixed vegetables Poland importer
- Evidence Grade: B
- Next Action: ready_for_screening
- Visible Contact Clues: Anna Kowalska, Importer
- Search Snippet: Importer and distributor of frozen food products in Warsaw. Contact Anna Kowalska for sourcing inquiries.
- Search Query Used: frozen mixed vegetables Poland importer
- Evidence Summary: 当前候选主要基于官网、2 条可见联系人线索、数据源 fixture形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 B：来源：fixture；命中搜索查询：frozen mixed vegetables Poland importer；有官网主体线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: linkedin_url
- Follow-up Suggestion: 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。

## Lead Screening Bridge
```json
{
  "default_country_or_market": "Poland",
  "operator_notes": "Prefer companies that look ready for private-label frozen food sourcing.",
  "product_or_offer": "frozen mixed vegetables",
  "target_customer_type": "importer",
  "industry_lens": "food",
  "seller_context": {
    "company_name": "Ningbo FreshGrow Foods",
    "product_or_offer": "frozen mixed vegetables",
    "product_categories": [
      "frozen vegetables",
      "private-label frozen food"
    ],
    "target_customer_types": [
      "importer",
      "private-label buyer"
    ],
    "target_industries": [
      "frozen food",
      "retail food"
    ],
    "value_propositions": [
      "stable specifications",
      "packaging coordination",
      "supply reliability"
    ],
    "certifications": [],
    "proof_points": [
      "Fixture-only proof point; replace with authorized company evidence in real use."
    ],
    "authorized_materials": [
      "test-fixture:frozen-food-capability-sheet"
    ],
    "excluded_customer_signals": [],
    "forbidden_claims": [
      "Do not claim confirmed purchase intent."
    ]
  },
  "leads": [
    {
      "company_name": "Baltic Frozen Trade",
      "company_website": "https://balticfrozentrade.pl",
      "person_name": "",
      "email": "",
      "country_or_market": "Poland",
      "source_url": "https://balticfrozentrade.pl",
      "linkedin_url": "https://www.linkedin.com/company/baltic-frozen-trade",
      "notes": "Prefer companies that look ready for private-label frozen food sourcing. | Supplier and importer of frozen vegetables and fruit for private label retail in Poland. | 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。",
      "evidence_grade": "A",
      "match_reason": "证据等级 A：来源：fixture；命中搜索查询：frozen food importer Poland importer distributor brand buyer；有官网主体线索；有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网、LinkedIn、数据源 fixture形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [
        "visible_contact_clues"
      ],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web",
      "source_name": "fixture",
      "source_url_or_note": "https://balticfrozentrade.pl",
      "freshness": "unknown",
      "confidence": "medium",
      "match_basis": "命中搜索查询：frozen food importer Poland importer distributor brand buyer"
    },
    {
      "company_name": "GreenHarvest Foods",
      "company_website": "https://greenharvestfoods.com",
      "person_name": "",
      "email": "anna@greenharvestfoods.com",
      "country_or_market": "Poland",
      "source_url": "https://greenharvestfoods.com",
      "linkedin_url": "https://www.linkedin.com/company/greenharvestfoods",
      "notes": "Prefer companies that look ready for private-label frozen food sourcing. | GreenHarvest Foods imports frozen vegetables for retail and private label programs in Poland. | 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。",
      "evidence_grade": "A",
      "match_reason": "证据等级 A：来源：fixture；命中搜索查询：frozen mixed vegetables Poland importer；有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网、LinkedIn、2 条可见联系人线索、数据源 fixture形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web",
      "source_name": "fixture",
      "source_url_or_note": "https://greenharvestfoods.com",
      "freshness": "unknown",
      "confidence": "medium",
      "match_basis": "命中搜索查询：frozen mixed vegetables Poland importer"
    },
    {
      "company_name": "PolFood Sourcing directory profile",
      "company_website": "https://directory.example/polfood-sourcing",
      "person_name": "Anna Kowalska",
      "email": "",
      "country_or_market": "Poland",
      "source_url": "https://directory.example/polfood-sourcing",
      "linkedin_url": "",
      "notes": "Prefer companies that look ready for private-label frozen food sourcing. | Importer and distributor of frozen food products in Warsaw. Contact Anna Kowalska for sourcing inquiries. | 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。",
      "evidence_grade": "B",
      "match_reason": "证据等级 B：来源：fixture；命中搜索查询：frozen mixed vegetables Poland importer；有官网主体线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网、2 条可见联系人线索、数据源 fixture形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [
        "linkedin_url"
      ],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web",
      "source_name": "fixture",
      "source_url_or_note": "https://directory.example/polfood-sourcing",
      "freshness": "unknown",
      "confidence": "medium",
      "match_basis": "命中搜索查询：frozen mixed vegetables Poland importer"
    }
  ]
}
```
