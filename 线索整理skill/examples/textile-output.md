# Lead Screening Package

## Summary
- Total Leads: 2
- Ready for Customer Intel: 1
- Need Enrichment: 1
- Manual Review: 0
- Operator Notes: Use conservative review flags before passing to outreach.

## lead-001
- Company: Atelier Loom GmbH
- Person: Mira Stein
- Email: mira@atelier-loom.de
- Website: https://atelier-loom.de
- Country/Market: Germany
- Lead Bucket: website_company_full_contact
- Recommended Next Action: enter_customer_intel
- Missing Fields: (none)
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
  "notes": "Premium table textile positioning. | Source URL: https://atelier-loom.de/about | LinkedIn URL: https://www.linkedin.com/company/atelier-loom"
}
```

## lead-002
- Company: NordHaus Tableware
- Person: (missing)
- Email: hello@gmail.com
- Website: https://nordhaus-tableware.de
- Country/Market: Germany
- Lead Bucket: website_company_partial_contact
- Recommended Next Action: enrich_then_customer_intel
- Missing Fields: person_name
- Manual Review Reasons:
  - 邮箱使用公共域名，不能直接当作企业身份强证据。
  - 邮箱域名与官网域名不一致，需确认是否同一主体。
- Follow-up Suggestions:
  - 先处理人工复核项，再决定是否进入客户背调。
- Customer Intel Input:
```json
{
  "company_name": "NordHaus Tableware",
  "person_name": "",
  "email": "hello@gmail.com",
  "company_website": "https://nordhaus-tableware.de",
  "country_or_market": "Germany",
  "notes": "Marketplace listing only, no confirmed buyer contact yet. | Source URL: https://marketplace.example/nordhaus | Review: 邮箱使用公共域名，不能直接当作企业身份强证据。；邮箱域名与官网域名不一致，需确认是否同一主体。"
}
```
