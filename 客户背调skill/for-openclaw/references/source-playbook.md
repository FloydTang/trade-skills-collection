# Source Playbook

## Priority Order

1. Official website and domain-level evidence
2. LinkedIn company page and personal profile
3. Facebook and Instagram
4. X and YouTube
5. General web search results and news pages

## Entity Resolution Rules

- Prefer direct identifiers over inferred ones: explicit website > email domain > search result guess.
- Do not merge two entities unless at least two signals align, such as company name plus matching domain or company name plus matching geography.
- When a person name is common, keep the person section tentative unless the profile clearly matches company, title, or market.

## Evidence Rules

- Attach a source URL to every material claim when possible.
- Mark a statement as inference when it is derived from patterns rather than stated directly.
- If website text and social text conflict, call out the conflict instead of choosing one silently.
- If only one weak source exists, keep confidence low and avoid firm wording.

## Deduping Rules

- Keep the highest-confidence URL per platform.
- Collapse mirrored URLs that point to the same page.
- Prefer official brand accounts over reseller, fan, or employee reposts.
- Prefer recent evidence when two sources say similar things.

## Risk Heuristics

### Low

- Website, domain, company naming, and social identity line up.
- Multiple public traces exist.
- No strong contradictions or suspicious patterns appear.

### Medium

- Public presence is thin or stale.
- Some company facts are unclear, but nothing is obviously wrong.
- Contact identity is partially matched rather than strongly verified.

### High

- Contact or company identity conflicts across sources.
- Website is missing, broken, placeholder-like, or inconsistent with the business claim.
- Email domain does not align with claimed company.
- There are strong signs of copied content, fake scale, or almost no public footprint.

## Recommended Search Patterns

- `"<company>" official website`
- `site:linkedin.com/company "<company>"`
- `site:linkedin.com/in "<person>" "<company>"`
- `site:facebook.com "<company>"`
- `site:instagram.com "<company>"`
- `site:x.com "<company>" OR site:twitter.com "<company>"`
- `site:youtube.com "<company>"`
- `"<email-domain>" company`

## Output Discipline

- Keep analysis in Chinese by default.
- Keep sales-facing angles bilingual.
- Keep risk scoring conservative.
- End with concrete next steps if evidence is weak.
