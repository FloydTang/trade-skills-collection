# Lead Screening Package

## Summary
- Total Leads: 3
- Ready for Customer Intel: 2
- Needs Enrichment: 0
- Manual Review: 1
- Operator Notes: Prioritize leads that can move into customer intel without additional web search.

## lead-001
- Company: Nordic Home Textile AB
- Person: Nadia
- Email: (missing)
- Website: https://www.nordichometextile.example
- Country/Market: Sweden
- Lead Bucket: website_company_partial_contact
- Evidence Grade: B
- Discovery Next Action: ready_for_screening
- Recommended Next Action: ready_for_customer_intel
- Legacy Recommended Next Action: enter_customer_intel
- Missing Fields: email
- Discovery Missing Fields: linkedin_url, visible_contact_clues
- Evidence Summary: 当前候选主要基于官网和公开网页来源形成。建议动作：ready_for_screening。
- Match Reason: 证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。
- Manual Review Reasons: (none)
- Follow-up Suggestions:
  - 如后续要开发信，可优先补公司邮箱或联系人邮箱。
- Customer Intel Input:
```json
{
  "company_name": "Nordic Home Textile AB",
  "person_name": "Nadia",
  "email": "",
  "company_website": "https://www.nordichometextile.example",
  "country_or_market": "Sweden",
  "notes": "Found via home textile search results | Evidence Summary: 当前候选主要基于官网和公开网页来源形成。建议动作：ready_for_screening。 | Match Reason: 证据等级 B：有官网主体线索；命中当前搜索策略中的目标关键词组合。 | Source URL: https://www.linkedin.com/company/nordic-home-textile-ab"
}
```

## lead-002
- Company: (missing)
- Person: (missing)
- Email: purchasing@acme-industrial.com
- Website: (missing)
- Country/Market: United States
- Lead Bucket: email_only_clue
- Evidence Grade: D
- Discovery Next Action: reject_low_evidence
- Recommended Next Action: hold_for_manual_review
- Legacy Recommended Next Action: hold_for_manual_review
- Missing Fields: company_name, company_website, person_name
- Discovery Missing Fields: company_name, company_website, linkedin_url, visible_contact_clues
- Evidence Summary: 当前候选主要基于弱网页片段形成。建议动作：reject_low_evidence。
- Match Reason: 证据等级 D：当前只有弱目录片段，尚不能稳定证明主体。
- Manual Review Reasons:
  - 当前只有邮箱线索，建议先补公司名或官网再进入客户背调。
  - 搜索阶段已判定为低证据候选，不建议直接推进。
- Follow-up Suggestions:
  - 补公司正式名称或官网标题。
  - 先根据邮箱域名确认官网是否存在。
  - 先处理人工复核项，再决定是否进入客户背调。
  - 优先补官网、LinkedIn 或主体可验证字段，再进入客户背调。
- Customer Intel Input:
```json
{
  "company_name": "",
  "person_name": "",
  "email": "purchasing@acme-industrial.com",
  "company_website": "",
  "country_or_market": "United States",
  "notes": "Email collected from directory page | Evidence Summary: 当前候选主要基于弱网页片段形成。建议动作：reject_low_evidence。 | Match Reason: 证据等级 D：当前只有弱目录片段，尚不能稳定证明主体。 | Source URL: https://example.com/acme | Review: 当前只有邮箱线索，建议先补公司名或官网再进入客户背调。；搜索阶段已判定为低证据候选，不建议直接推进。"
}
```

## lead-003
- Company: GreenHarvest Foods
- Person: Anna
- Email: anna@greenharvestfoods.com
- Website: https://greenharvestfoods.com
- Country/Market: Poland
- Lead Bucket: website_company_full_contact
- Evidence Grade: A
- Discovery Next Action: ready_for_screening
- Recommended Next Action: ready_for_customer_intel
- Legacy Recommended Next Action: enter_customer_intel
- Missing Fields: (none)
- Discovery Missing Fields: (none)
- Evidence Summary: 当前候选主要基于官网、LinkedIn、1 条可见联系人线索形成。建议动作：ready_for_screening。
- Match Reason: 证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索。
- Manual Review Reasons: (none)
- Follow-up Suggestions:
  - 可直接进入客户背调，并在背调阶段继续核对实体匹配。
- Customer Intel Input:
```json
{
  "company_name": "GreenHarvest Foods",
  "person_name": "Anna",
  "email": "anna@greenharvestfoods.com",
  "company_website": "https://greenharvestfoods.com",
  "country_or_market": "Poland",
  "notes": "Looks ready for background research. | Evidence Summary: 当前候选主要基于官网、LinkedIn、1 条可见联系人线索形成。建议动作：ready_for_screening。 | Match Reason: 证据等级 A：有官网主体线索；有 LinkedIn 公司页线索；搜索结果出现可见联系人或角色线索。 | Source URL: https://greenharvestfoods.com/contact | LinkedIn URL: https://www.linkedin.com/company/greenharvestfoods"
}
```
