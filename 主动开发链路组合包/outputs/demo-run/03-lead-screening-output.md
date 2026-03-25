# Lead Screening Package

## Summary
- Total Leads: 3
- Ready for Customer Intel: 2
- Need Enrichment: 1
- Manual Review: 0
- Operator Notes: Prefer companies that look ready for private-label frozen food sourcing.

## lead-001
- Company: Baltic Frozen Trade
- Person: (missing)
- Email: (missing)
- Website: https://balticfrozentrade.pl
- Country/Market: Poland
- Lead Bucket: website_company_basic
- Recommended Next Action: enrich_then_customer_intel
- Missing Fields: person_name, email
- Manual Review Reasons: (none)
- Follow-up Suggestions:
  - 如后续要开发信，可优先补公司邮箱或联系人邮箱。
- Customer Intel Input:
```json
{
  "company_name": "Baltic Frozen Trade",
  "person_name": "",
  "email": "",
  "company_website": "https://balticfrozentrade.pl",
  "country_or_market": "Poland",
  "notes": "Prefer companies that look ready for private-label frozen food sourcing. | Supplier and importer of frozen vegetables and fruit for private label retail in Poland. | 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。 | Source URL: https://balticfrozentrade.pl | LinkedIn URL: https://www.linkedin.com/company/baltic-frozen-trade"
}
```

## lead-002
- Company: GreenHarvest Foods
- Person: (missing)
- Email: anna@greenharvestfoods.com
- Website: https://greenharvestfoods.com
- Country/Market: Poland
- Lead Bucket: website_company_partial_contact
- Recommended Next Action: enter_customer_intel
- Missing Fields: person_name
- Manual Review Reasons: (none)
- Follow-up Suggestions:
  - 可直接进入客户背调，并在背调阶段继续核对实体匹配。
- Customer Intel Input:
```json
{
  "company_name": "GreenHarvest Foods",
  "person_name": "",
  "email": "anna@greenharvestfoods.com",
  "company_website": "https://greenharvestfoods.com",
  "country_or_market": "Poland",
  "notes": "Prefer companies that look ready for private-label frozen food sourcing. | GreenHarvest Foods imports frozen vegetables for retail and private label programs in Poland. | 先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。 | Source URL: https://greenharvestfoods.com | LinkedIn URL: https://www.linkedin.com/company/greenharvestfoods"
}
```

## lead-003
- Company: PolFood Sourcing directory profile
- Person: Anna Kowalska
- Email: (missing)
- Website: https://directory.example/polfood-sourcing
- Country/Market: Poland
- Lead Bucket: website_company_partial_contact
- Recommended Next Action: enter_customer_intel
- Missing Fields: email
- Manual Review Reasons:
  - 公司名与官网域名对应关系较弱，建议人工确认主体匹配。
- Follow-up Suggestions:
  - 如后续要开发信，可优先补公司邮箱或联系人邮箱。
  - 先处理人工复核项，再决定是否进入客户背调。
- Customer Intel Input:
```json
{
  "company_name": "PolFood Sourcing directory profile",
  "person_name": "Anna Kowalska",
  "email": "",
  "company_website": "https://directory.example/polfood-sourcing",
  "country_or_market": "Poland",
  "notes": "Prefer companies that look ready for private-label frozen food sourcing. | Importer and distributor of frozen food products in Warsaw. Contact Anna Kowalska for sourcing inquiries. | 先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。 | Source URL: https://directory.example/polfood-sourcing | Review: 公司名与官网域名对应关系较弱，建议人工确认主体匹配。"
}
```
