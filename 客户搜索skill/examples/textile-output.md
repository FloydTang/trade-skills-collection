# Lead Discovery Package

## Summary
- Product/Offer: washed linen table textile
- Target Market: Germany
- Customer Type: brand
- Raw Result Count: 7
- Candidate Count: 4

## Search Strategy
- Strategy Summary: 先用产品 + 市场 + 客户类型构造主查询，再补角色词、LinkedIn 公司页线索和 must_include 限定词。
- Query Plan:
- washed linen table textile Germany brand
- table linen brand Germany importer distributor brand buyer
- site:linkedin.com/company washed linen table textile Germany brand
- washed linen table textile Germany brand "design"
- Must Include: design
- Exclude Terms: job, salary

## candidate-001
- Company: Atelier Loom GmbH
- Website: https://atelier-loom.de
- LinkedIn: https://www.linkedin.com/company/atelier-loom
- Source URL: https://atelier-loom.de
- Country/Market: Germany
- Source Type: web
- Evidence Grade: A
- Next Action: ready_for_screening
- Visible Contact Clues: Design, Mira Stein
- Search Snippet: Design-led table linen brand for premium home textile collections in Germany.
- Search Query Used: washed linen table textile Germany brand, table linen brand Germany importer distributor brand buyer, washed linen table textile Germany brand "design", site:linkedin.com/company washed linen table textile Germany brand
- Evidence Summary: 当前候选主要基于官网、LinkedIn、2 条可见联系人线索形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: (none)
- Follow-up Suggestion: 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。

## candidate-002
- Company: NordHaus marketplace profile
- Website: https://marketplace.example/nordhaus
- LinkedIn: (missing)
- Source URL: https://marketplace.example/nordhaus
- Country/Market: Germany
- Source Type: web
- Evidence Grade: B
- Next Action: ready_for_screening
- Visible Contact Clues: (none)
- Search Snippet: NordHaus Tableware sells premium table linen collections for retail buyers.
- Search Query Used: table linen brand Germany importer distributor brand buyer
- Evidence Summary: 当前候选主要基于官网形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: linkedin_url, visible_contact_clues
- Follow-up Suggestion: 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。

## candidate-003
- Company: NordHaus Tableware collection page
- Website: https://nordhaus-tableware.de
- LinkedIn: (missing)
- Source URL: https://nordhaus-tableware.de
- Country/Market: Germany
- Source Type: web
- Evidence Grade: B
- Next Action: ready_for_screening
- Visible Contact Clues: (none)
- Search Snippet: NordHaus presents natural table linen ranges for boutique home stores.
- Search Query Used: washed linen table textile Germany brand
- Evidence Summary: 当前候选主要基于官网形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: linkedin_url, visible_contact_clues
- Follow-up Suggestion: 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。

## candidate-004
- Company: NordHaus Tableware
- Website: (missing)
- LinkedIn: https://www.linkedin.com/company/nordhaus-tableware
- Source URL: https://www.linkedin.com/company/nordhaus-tableware
- Country/Market: Germany
- Source Type: linkedin
- Evidence Grade: B
- Next Action: ready_for_screening
- Visible Contact Clues: (none)
- Search Snippet: NordHaus Tableware focuses on home tabletop collections and design buyers.
- Search Query Used: site:linkedin.com/company washed linen table textile Germany brand
- Evidence Summary: 当前候选主要基于LinkedIn形成。 建议动作：ready_for_screening。
- Match Reason: 证据等级 B：有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。
- Missing Fields: company_website, visible_contact_clues
- Follow-up Suggestion: 先补官网或公司域名，再进入线索整理。

## Lead Screening Bridge
```json
{
  "default_country_or_market": "",
  "operator_notes": "Prefer companies with brand positioning and visible product presentation.",
  "leads": [
    {
      "company_name": "Atelier Loom GmbH",
      "company_website": "https://atelier-loom.de",
      "person_name": "Mira Stein",
      "email": "",
      "country_or_market": "Germany",
      "source_url": "https://atelier-loom.de",
      "linkedin_url": "https://www.linkedin.com/company/atelier-loom",
      "notes": "Prefer companies with brand positioning and visible product presentation. | Design-led table linen brand for premium home textile collections in Germany. | 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。",
      "evidence_grade": "A",
      "match_reason": "证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网、LinkedIn、2 条可见联系人线索形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web"
    },
    {
      "company_name": "NordHaus marketplace profile",
      "company_website": "https://marketplace.example/nordhaus",
      "person_name": "",
      "email": "",
      "country_or_market": "Germany",
      "source_url": "https://marketplace.example/nordhaus",
      "linkedin_url": "",
      "notes": "Prefer companies with brand positioning and visible product presentation. | NordHaus Tableware sells premium table linen collections for retail buyers. | 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。",
      "evidence_grade": "B",
      "match_reason": "证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [
        "linkedin_url",
        "visible_contact_clues"
      ],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web"
    },
    {
      "company_name": "NordHaus Tableware collection page",
      "company_website": "https://nordhaus-tableware.de",
      "person_name": "",
      "email": "",
      "country_or_market": "Germany",
      "source_url": "https://nordhaus-tableware.de",
      "linkedin_url": "",
      "notes": "Prefer companies with brand positioning and visible product presentation. | NordHaus presents natural table linen ranges for boutique home stores. | 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。",
      "evidence_grade": "B",
      "match_reason": "证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于官网形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [
        "linkedin_url",
        "visible_contact_clues"
      ],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "web"
    },
    {
      "company_name": "NordHaus Tableware",
      "company_website": "",
      "person_name": "",
      "email": "",
      "country_or_market": "Germany",
      "source_url": "https://www.linkedin.com/company/nordhaus-tableware",
      "linkedin_url": "https://www.linkedin.com/company/nordhaus-tableware",
      "notes": "Prefer companies with brand positioning and visible product presentation. | NordHaus Tableware focuses on home tabletop collections and design buyers. | 先补官网或公司域名，再进入线索整理。",
      "evidence_grade": "B",
      "match_reason": "证据等级 B：有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。",
      "evidence_summary": "当前候选主要基于LinkedIn形成。 建议动作：ready_for_screening。",
      "discovery_missing_fields": [
        "company_website",
        "visible_contact_clues"
      ],
      "discovery_next_action": "ready_for_screening",
      "product_keywords": "",
      "source_type": "linkedin"
    }
  ]
}
```
