---
name: trade-customer-intel
description: Build bilingual, evidence-backed customer intelligence reports for foreign-trade leads from a company name, contact name, email, or website. Use when Openclaw or a sales operator needs to research a prospect's company website, public web footprint, and social presence across LinkedIn, Facebook, Instagram, X/Twitter, YouTube, and general web results, then assemble a company/person profile, interest signals, sales angles, and a Low/Medium/High risk rating.
---

# Trade Customer Intel

## Overview

Use this skill to turn sparse lead data into a structured public-web due-diligence report for sales development. The output is bilingual where it matters: the analysis stays mainly in Chinese, while sales-facing angles include English wording your team can reuse externally.

This skill now supports a second-stage outreach layer. When a lead is rated `Low` or `Medium`, it should continue from background verification into conservative outreach personalization using public content from LinkedIn, Instagram, X/Twitter, and the company website.

## Workflow

1. Normalize input into the standard shape:

```json
{
  "company_name": "",
  "person_name": "",
  "email": "",
  "company_website": "",
  "country_or_market": "",
  "notes": ""
}
```

2. If only an email is present, extract the email domain and treat it as the first company clue.
3. Search in this order:
   - Official website and domain evidence
   - LinkedIn company page and personal profile
   - Facebook and Instagram
   - X/Twitter and YouTube
   - General web search and news
4. Resolve identities conservatively:
   - Prefer direct identifiers over inference.
   - Do not merge ambiguous people or companies unless multiple signals line up.
   - Mark weak conclusions as inference, not fact.
5. Assemble a report using the format in [report-template.md](./references/report-template.md).
6. Score risk conservatively using [source-playbook.md](./references/source-playbook.md).
7. If the lead is not `High` risk and there is enough public evidence, generate:
   - an outreach persona card
   - a light-weight English outreach pack
8. If public evidence is too thin, mark phase 2 as `limited_evidence` instead of forcing over-personalized content.

## Main Script

Use [build_customer_intel_report.py](./scripts/build_customer_intel_report.py) as the default entrypoint.

### Example run

```bash
python3 ./scripts/build_customer_intel_report.py --input-json /path/to/input.json --markdown-out /tmp/customer-intel.md --json-out /tmp/customer-intel.json
```

Or pipe JSON directly:

```bash
cat <<'EOF' | python3 ./scripts/build_customer_intel_report.py
{
  "company_name": "Acme Industrial",
  "person_name": "Jane Smith",
  "email": "jane@acme-industrial.com",
  "country_or_market": "United States"
}
EOF
```

### Script behavior

- If `tvly` is installed, the script uses it first for web search.
- If `tvly` is not installed, the script falls back to DuckDuckGo HTML search.
- Page text fetching uses `r.jina.ai` snapshots where possible.
- If evidence is sparse, the script still produces a report and explicitly flags low confidence.

## Output Requirements

- Keep the report structured and CRM-friendly.
- Keep core analysis in Chinese.
- Include English wording in the `Executive Summary` and `Sales Angles` sections.
- For `Low` and `Medium` leads, include `Outreach Persona Card` and `Personalized Outreach Pack` when evidence supports it.
- Attach source URLs to every material claim when possible.
- Use `Low`, `Medium`, or `High` risk ratings only.
- If the person match is weak, say so explicitly instead of inventing a firm personal profile.
- Keep outreach personalization conservative. Do not invent private preferences or present weak inferences as facts.

## Openclaw Integration Notes

- Manual trigger: accept direct lead fields from an operator and generate the report.
- Automated trigger: map inquiry/order data into the standard JSON shape above, then call the script.
- Missing fields are allowed; the report header must list what was missing.
- The first version only uses public internet sources. Do not imply private-data access.

## References

- Read [report-template.md](./references/report-template.md) before changing the output shape.
- Read [source-playbook.md](./references/source-playbook.md) before changing search order, confidence rules, or risk scoring.

## Defaults

- Standard depth, not exhaustive crawling.
- Public web only.
- Conservative entity matching.
- Conservative risk scoring.
- Phase 2 personalization defaults to LinkedIn + Instagram + X/Twitter + website.
