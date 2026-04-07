---
name: trade-customer-intel
description: Build bilingual, evidence-backed customer intelligence reports for foreign-trade leads from a company name, contact name, email, or website. Use when Openclaw or a sales operator needs to research a prospect's company website, public web footprint, and social presence across LinkedIn, Facebook, Instagram, X/Twitter, YouTube, and general web results, then assemble a company/person profile, interest signals, sales angles, and a Low/Medium/High risk rating.
---

# Trade Customer Intel

## Overview

Use this skill to turn sparse lead data into a structured public-web due-diligence report for sales development. The output is bilingual where it matters: the analysis stays mainly in Chinese, while sales-facing angles include English wording your team can reuse externally.

角色定位：

- `客户情报分析员`
- 负责基于公开网页证据完成客户背调与风险判断
- 不负责批量搜客户，也不负责替代人工直接外发邮件

上下游关系：

- 上游：`线索整理skill/` 输出的 `customer_intel_input`，或人工提供的稀疏 lead 信息
- 下游：`开发信skill/`

当前最稳的是公司级背调主线。联系人、职位和个性化信号只作辅助，不应被包装成稳定的精准人物能力。

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
7. If public evidence is too thin, mark weak conclusions as limited evidence instead of forcing over-personalized content.

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
- Attach source URLs to every material claim when possible.
- Use `Low`, `Medium`, or `High` risk ratings only.
- If the person match is weak, say so explicitly instead of inventing a firm personal profile.
- Keep outreach personalization conservative. Do not invent private preferences or present weak inferences as facts.
- Do not replace `客户搜索skill/` or `线索整理skill/` as the lead-entry stage.
- Do not imply the final outreach draft can skip human review.
- Do not imply stable support for precise personal email discovery.

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

## Enhancement Entry

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
