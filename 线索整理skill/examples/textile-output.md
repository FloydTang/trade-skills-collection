# Lead Screening Package

## Summary
- Total Leads: 2
- Ready for Customer Intel: 1
- Needs Enrichment: 1
- Manual Review: 0
- Operator Notes: Use conservative review flags before passing to outreach.

## lead-001
- Company: Atelier Loom GmbH
- Person: Mira Stein
- Email: mira@atelier-loom.de
- Website: https://atelier-loom.de
- Country/Market: Germany
- Lead Bucket: website_company_full_contact
- Evidence Grade: A
- Discovery Next Action: ready_for_screening
- Recommended Next Action: ready_for_customer_intel
- Legacy Recommended Next Action: enter_customer_intel
- Missing Fields: (none)
- Discovery Missing Fields: (none)
- Evidence Summary: 当前候选主要基于官网、LinkedIn 和公开网页来源形成。建议动作：ready_for_screening。
- Match Reason: 证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。
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
  "notes": "Premium table textile positioning. | Evidence Summary: 当前候选主要基于官网、LinkedIn 和公开网页来源形成。建议动作：ready_for_screening。 | Match Reason: 证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；命中当前搜索策略中的目标关键词组合。 | Source URL: https://atelier-loom.de/about | LinkedIn URL: https://www.linkedin.com/company/atelier-loom"
}
```

## lead-002
- Company: NordHaus Tableware
- Person: (missing)
- Email: hello@gmail.com
- Website: https://nordhaus-tableware.de
- Country/Market: Germany
- Lead Bucket: website_company_partial_contact
- Evidence Grade: C
- Discovery Next Action: needs_enrichment
- Recommended Next Action: needs_enrichment
- Legacy Recommended Next Action: enrich_then_customer_intel
- Missing Fields: person_name
- Discovery Missing Fields: person_name, linkedin_url, visible_contact_clues
- Evidence Summary: 当前候选主要基于官网和市场目录来源形成。建议动作：needs_enrichment。
- Match Reason: 证据等级 C：有官网主体线索，但缺少 LinkedIn 和稳定联系人补强。
- Manual Review Reasons:
  - 邮箱使用公共域名，不能直接当作企业身份强证据。
  - 邮箱域名与官网域名不一致，需确认是否同一主体。
- Follow-up Suggestions:
  - 先处理人工复核项，再决定是否进入客户背调。
  - 优先补官网、LinkedIn 或主体可验证字段，再进入客户背调。
- Customer Intel Input:
```json
{
  "company_name": "NordHaus Tableware",
  "person_name": "",
  "email": "hello@gmail.com",
  "company_website": "https://nordhaus-tableware.de",
  "country_or_market": "Germany",
  "notes": "Marketplace listing only, no confirmed buyer contact yet. | Evidence Summary: 当前候选主要基于官网和市场目录来源形成。建议动作：needs_enrichment。 | Match Reason: 证据等级 C：有官网主体线索，但缺少 LinkedIn 和稳定联系人补强。 | Source URL: https://marketplace.example/nordhaus | Review: 邮箱使用公共域名，不能直接当作企业身份强证据。；邮箱域名与官网域名不一致，需确认是否同一主体。"
}
```
