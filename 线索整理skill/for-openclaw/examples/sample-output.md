# Lead Screening Package

## Summary
- Total Leads: 2
- Ready for Customer Intel: 0
- Needs Enrichment: 1
- Manual Review: 1
- Operator Notes: Use conservative screening before sending any textile lead into customer intel.

## lead-001
- Company: Atelier Loom GmbH
- Person: Mira Stein
- Email: mira@atelier-loom.de
- Website: https://atelier-loom.de
- Country/Market: Germany
- Lead Bucket: website_company_full_contact
- Evidence Grade: C
- Business Fit: high
- Discovery Next Action: (missing)
- Recommended Next Action: needs_enrichment
- Legacy Recommended Next Action: enrich_then_customer_intel
- Missing Fields: (none)
- Discovery Missing Fields: (none)
- Business Fit Reason: 候选公开描述与目标上下文匹配：washed linen table textile, washed linen tablecloths
- Source Type: website
- Manual Review Reasons: (none)
- Follow-up Suggestions:
  - 可直接进入客户背调，并在背调阶段继续核对实体匹配。
- Customer Intel Input:
```json
{
  "company_name": "Atelier Loom GmbH",
  "person_name": "Mira Stein",
  "email": "mira@atelier-loom.de",
  "company_website": "https://atelier-loom.de",
  "country_or_market": "Germany",
  "product_or_offer": "washed linen table textile",
  "industry_lens": "consumer",
  "seller_context": {
    "company_name": "",
    "product_or_offer": "washed linen table textile",
    "product_categories": [
      "washed linen tablecloths",
      "linen napkins"
    ],
    "target_customer_types": [
      "design-led home textile brands with private-label collections"
    ],
    "target_industries": [],
    "value_propositions": [
      "small-batch sampling",
      "custom colors",
      "washed linen production"
    ],
    "certifications": [],
    "proof_points": [],
    "authorized_materials": [],
    "excluded_customer_signals": [
      "consumer-only retailer with no private-label activity"
    ],
    "forbidden_claims": []
  },
  "screening_context": {
    "business_fit": {
      "rating": "high",
      "context_present": true,
      "matched_terms": [
        "washed linen table textile",
        "washed linen tablecloths"
      ],
      "reasons": [
        "候选公开描述与目标上下文匹配：washed linen table textile, washed linen tablecloths"
      ]
    },
    "evidence_grade": "C",
    "recommended_next_action": "needs_enrichment"
  },
  "notes": "Premium table textile positioning. | Source URL: https://atelier-loom.de/about | Source Type: website | LinkedIn URL: https://www.linkedin.com/company/atelier-loom"
}
```

## lead-002
- Company: (missing)
- Person: (missing)
- Email: hello@gmail.com
- Website: (missing)
- Country/Market: Germany
- Lead Bucket: email_only_clue
- Evidence Grade: C
- Business Fit: high
- Discovery Next Action: (missing)
- Recommended Next Action: hold_for_manual_review
- Legacy Recommended Next Action: hold_for_manual_review
- Missing Fields: company_name, company_website, person_name
- Discovery Missing Fields: (none)
- Business Fit Reason: 候选公开描述与目标上下文匹配：washed linen table textile
- Source Type: marketplace
- Manual Review Reasons:
  - 邮箱使用公共域名，不能直接当作企业身份强证据。
  - 当前只有邮箱线索，建议先补公司名或官网再进入客户背调。
- Follow-up Suggestions:
  - 补公司正式名称或官网标题。
  - 先根据邮箱域名确认官网是否存在。
  - 先处理人工复核项，再决定是否进入客户背调。
- Customer Intel Input:
```json
{
  "company_name": "",
  "person_name": "",
  "email": "hello@gmail.com",
  "company_website": "",
  "country_or_market": "Germany",
  "product_or_offer": "washed linen table textile",
  "industry_lens": "consumer",
  "seller_context": {
    "company_name": "",
    "product_or_offer": "washed linen table textile",
    "product_categories": [
      "washed linen tablecloths",
      "linen napkins"
    ],
    "target_customer_types": [
      "design-led home textile brands with private-label collections"
    ],
    "target_industries": [],
    "value_propositions": [
      "small-batch sampling",
      "custom colors",
      "washed linen production"
    ],
    "certifications": [],
    "proof_points": [],
    "authorized_materials": [],
    "excluded_customer_signals": [
      "consumer-only retailer with no private-label activity"
    ],
    "forbidden_claims": []
  },
  "screening_context": {
    "business_fit": {
      "rating": "high",
      "context_present": true,
      "matched_terms": [
        "washed linen table textile"
      ],
      "reasons": [
        "候选公开描述与目标上下文匹配：washed linen table textile"
      ]
    },
    "evidence_grade": "C",
    "recommended_next_action": "hold_for_manual_review"
  },
  "notes": "Marketplace listing only. | Source URL: https://marketplace.example/nordhaus | Source Type: marketplace | Review: 邮箱使用公共域名，不能直接当作企业身份强证据。；当前只有邮箱线索，建议先补公司名或官网再进入客户背调。"
}
```
