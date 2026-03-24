# Lead Screening Package

## Summary
- Total Leads: 3
- Ready for Customer Intel: 2
- Need Enrichment: 1
- Manual Review: 0
- Operator Notes: Prioritize leads that can move into customer intel without additional web search.

## lead-001
- Company: Nordic Home Textile AB
- Person: Nadia
- Email: (missing)
- Website: https://www.nordichometextile.example
- Country/Market: Sweden
- Lead Bucket: website_company_partial_contact
- Recommended Next Action: enter_customer_intel
- Missing Fields: email
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
  "notes": "Found via home textile search results | Source URL: https://www.linkedin.com/company/nordic-home-textile-ab"
}
```

## lead-002
- Company: (missing)
- Person: (missing)
- Email: purchasing@acme-industrial.com
- Website: (missing)
- Country/Market: United States
- Lead Bucket: email_only_clue
- Recommended Next Action: enrich_then_customer_intel
- Missing Fields: company_name, company_website, person_name
- Manual Review Reasons:
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
  "email": "purchasing@acme-industrial.com",
  "company_website": "",
  "country_or_market": "United States",
  "notes": "Email collected from directory page | Source URL: https://example.com/acme | Review: 当前只有邮箱线索，建议先补公司名或官网再进入客户背调。"
}
```

## lead-003
- Company: GreenHarvest Foods
- Person: Anna
- Email: anna@greenharvestfoods.com
- Website: https://greenharvestfoods.com
- Country/Market: Poland
- Lead Bucket: website_company_full_contact
- Recommended Next Action: enter_customer_intel
- Missing Fields: (none)
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
  "notes": "Looks ready for background research. | Source URL: https://greenharvestfoods.com/contact | LinkedIn URL: https://www.linkedin.com/company/greenharvestfoods"
}
```
