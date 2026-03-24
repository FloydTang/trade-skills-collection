---
name: trade-customer-intel-for-openclaw
description: OpenClaw-native version of Trade Customer Intel. Use coze-web-search for search, scrapling-official for primary page extraction, and coze-web-fetch as fallback. Generate a bilingual, evidence-backed customer intelligence report from a structured evidence bundle.
---

# Trade Customer Intel for OpenClaw

## Overview

This skill is the OpenClaw-native companion to the repository's classic version.

It is designed for cloud OpenClaw environments where search and page retrieval are performed by platform tools first, and a Python report builder then turns the resulting evidence bundle into a structured bilingual report.

## Inputs

Normalize operator input into this lead shape:

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

The final report-builder input must wrap that lead together with an evidence bundle:

```json
{
  "lead": {},
  "evidence_bundle": {
    "search_results": [],
    "page_snapshots": [],
    "search_runs": [],
    "errors": []
  }
}
```

## Tooling Rules

- Search tool: `coze-web-search`
- Primary fetch tool: `scrapling-official`
- Fallback fetch tool: `coze-web-fetch`

Do not use Tavily, DuckDuckGo HTML scraping, or `r.jina.ai` in this variant.

## Search Order

Search in this fixed order:

1. Official website and domain evidence
2. LinkedIn company page and personal profile
3. Facebook and Instagram
4. X / Twitter and YouTube
5. General web search and news

## Search Execution Rules

- Keep query budgets small and deterministic
- Prefer direct identifiers over broad inference
- Stop expanding official website candidates once a high-confidence official domain is identified
- Keep only a small number of representative results per platform
- Do not fail the overall task just because one platform is weak or blocked

## Fetch Rules

- Use `scrapling-official` first for page text extraction
- If `scrapling-official` fails, retry with `coze-web-fetch`
- If full-page content is unavailable, keep the search result snippet and continue
- Record fetch failures into `evidence_bundle.errors`

## Entity Resolution Rules

- Prefer official website over search guess
- Do not treat public email domains as company-domain proof
- Do not merge ambiguous people and companies unless multiple signals align
- Mark weak conclusions as inference
- If LinkedIn evidence is missing, keep person matching conservative

## Output Requirements

Follow [report-template.md](./references/report-template.md) and [source-playbook.md](./references/source-playbook.md).

- Keep analysis mainly in Chinese
- Keep sales-facing content bilingual
- Keep risk scoring conservative
- Preserve `Low`, `Medium`, `High` ratings only
- Generate outreach persona and outreach pack only when public evidence supports them
- If evidence is thin, use `limited_evidence` instead of forcing personalization

## Main Script

Use [build_customer_intel_report_from_evidence.py](./scripts/build_customer_intel_report_from_evidence.py) as the report-builder entrypoint.

### Example run

```bash
python3 ./scripts/build_customer_intel_report_from_evidence.py \
  --input-json /path/to/openclaw-customer-intel.json \
  --markdown-out /tmp/customer-intel-openclaw.md \
  --json-out /tmp/customer-intel-openclaw.json
```

## Notes

- This skill is parallel to the classic version; it does not replace it
- The classic version remains the baseline for comparison
- This version optimizes for cloud stability and controlled tool orchestration
