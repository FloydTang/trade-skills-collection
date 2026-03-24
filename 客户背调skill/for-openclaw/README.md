# Trade Customer Intel for OpenClaw

OpenClaw-native variant of `trade-customer-intel`.

这个版本专门为云端 OpenClaw 设计，不替换仓库根目录的 `classic` 版本，而是单独维护一套运行时边界：

- 搜索由 `coze-web-search` 执行
- 页面抓取优先走 `scrapling-official`
- 抓取失败时降级到 `coze-web-fetch`
- Python 脚本只负责从结构化证据包生成报告

## Why This Exists

原版 `classic` 更适合 Codex / 本地 Python 直跑，内置了 Tavily、DuckDuckGo HTML 和 `r.jina.ai` 风格的执行假设。

OpenClaw 版的目标不同：

- 适应云端工具调用方式
- 避免把搜索/抓取逻辑硬编码在 Python 里
- 优先保证失败可降级、输出可持续生成
- 继续保留原版报告结构和保守风控原则

## Runtime Model

OpenClaw 版采用“两段式”流程：

1. OpenClaw Skill 负责搜索和抓取
2. Python 汇总器负责实体判断、信号提取、风险评分和报告渲染

也就是说，这里的 Python 脚本默认接收的是：

- `lead`
- `evidence_bundle`

而不是直接自己联网检索。

## Directory Layout

```text
for-openclaw/
├── SKILL.md
├── README.md
├── examples/
│   └── sample-input.json
├── references/
│   ├── report-template.md
│   └── source-playbook.md
├── schemas/
│   ├── lead-input.json
│   └── evidence-bundle.json
└── scripts/
    └── build_customer_intel_report_from_evidence.py
```

## Input Contract

The report builder expects a single JSON payload:

```json
{
  "lead": {
    "company_name": "Acme Industrial",
    "person_name": "Jane Smith",
    "email": "jane@acme-industrial.com",
    "company_website": "",
    "country_or_market": "United States",
    "notes": ""
  },
  "evidence_bundle": {
    "search_results": [],
    "page_snapshots": [],
    "search_runs": [],
    "errors": []
  }
}
```

## Run Locally

```bash
python3 ./for-openclaw/scripts/build_customer_intel_report_from_evidence.py \
  --input-json ./for-openclaw/examples/sample-input.json \
  --markdown-out /tmp/customer-intel-openclaw.md \
  --json-out /tmp/customer-intel-openclaw.json
```

## OpenClaw Search Order

The OpenClaw skill should search in this order:

1. Official website and domain clues
2. LinkedIn company page and personal profile
3. Facebook and Instagram
4. X / Twitter and YouTube
5. General web search and news

## Failure Strategy

- Search failures do not block report generation
- Fetch failures do not block report generation
- Missing full-page text is acceptable; snippet-only analysis is allowed
- LinkedIn failures should be recorded, not treated as overall fatal errors
- Weak evidence must remain weak in the report

## Output Contract

This variant preserves the original report contract:

- Bilingual executive summary
- Structured identity snapshot
- Digital footprint summary
- Conservative risk rating
- Outreach persona and outreach pack only when evidence supports them

## Relationship to the Classic Version

- Root `SKILL.md` and `scripts/build_customer_intel_report.py` remain the baseline
- `for-openclaw/` is a separate implementation track
- Both versions should stay conceptually aligned on output shape and scoring philosophy
