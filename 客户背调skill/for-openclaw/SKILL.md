---
name: trade-customer-intel-for-openclaw
description: OpenClaw-native version of Trade Customer Intel. Use coze-web-search for search, scrapling-official for primary page extraction, and coze-web-fetch as fallback. Generate a bilingual, evidence-backed customer intelligence report from a structured evidence bundle.
openclaw_role: stage_worker
workspace_owner_skill: trade-active-outreach-combo
single_skill_policy: attach_only
feishu_container_creation: forbidden
requires_master_base: true
requires_master_record: true
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

## Feishu 回写规则（经验教训沉淀）

### 主表回写（Lead Workflow Master）

回挂主表时，至少更新以下 7 个字段：

| 字段 | 说明 |
|---|---|
| `intel_doc_ref` | 背调文档链接（URL 类型） |
| `risk_rating` | SingleSelect: low / medium / high / critical |
| `entity_confidence` | Number: 0-100 |
| `current_stage` | Text: intel_completed / hold / failed |
| `current_status` | SingleSelect: intel_completed 等 |
| `recommended_next_action` | Text: ready_for_email_draft / hold_for_manual_review |
| `last_updated_at` | DateTime: 当前时间戳（毫秒） |

### 背调结果表回写（Customer Intel Results）

回写字段：

| 字段 | 说明 |
|---|---|
| `线索编号 lead_id` | Text |
| `风险等级 risk_rating` | SingleSelect: low / medium / high / critical |
| `主体置信度 entity_confidence` | Number: 0-100 |
| `公司匹配状态 company_match_status` | SingleSelect: verified / partial / unverified / mismatch |
| `联系人匹配状态 person_match_status` | SingleSelect: verified / partial / unverified / not_applicable |
| `背调阶段结果 intel_result` | SingleSelect: intel_completed / intel_insufficient_evidence / intel_failed |
| `背调文档引用 intel_doc_ref` | URL: `{link, text}` 对象 |
| `中文摘要 summary_cn` | Text |
| `英文摘要 summary_en` | Text |
| `销售切入点 key_sales_angles` | Text |
| `关键风险 key_risks` | Text |
| `证据清单 evidence_list` | Text |

### Feishu API 注意点（踩坑记录）

1. **字段名必须完全匹配** — 飞书 API 字段名是「中文 英文」混合格式（如 `线索编号 lead_id`），带空格，必须精确一致。少一个空格或顺序颠倒都会报 `FieldNameNotFound`。
2. **URL 类型字段需要对象格式** — 不能用纯字符串 `"https://"`，必须用 `{"link": "https://...", "text": "显示文本"}`
3. **SingleSelect 字段用选项名** — 传 `"low"` 不是 `"optXXXX"` ID
4. **Number 字段传数字** — `95` 不是 `"95"`
5. **DateTime 字段传毫秒时间戳** — `1745570700000`
6. **分两步写入** — URL/SingleSelect 类字段和 Text/Number/DateTime 字段最好分两批写入。第一次 `create_record` 只写 Text/Number/SingleSelect，第二次 `update_record` 补 URL 字段。一次性大批量写入容易触发字段类型转换错误。
7. **文本内容不要过长** — 长文本（如 evidence_list）控制在 300 字以内，完整内容写入背调文档而非 table 字段。
8. **创建文档后回写 wikidoc_token** — 用 `feishu_wiki(action="create")` 创建文档后，记录 `obj_token`（doc_token），再用 `feishu_doc(action="write")` 写入内容。URL 拼接格式：`https://evenbetter.feishu.cn/wiki/{node_token}`。

### 背调文档标题规范

文档创建路径：`首页/` 下创建独立页面

命名格式：`{lead_id}_{公司简称}_背调报告`

文档内必须包含的章节（详见 report-template.md）：背调摘要（中英文）、身份快照、Intel Decision、公司画像、数字足迹、主题信号、销售切入点（≥3个）、风险评级、证据清单、需人工确认事项、推荐下一步。

### 搜索层注意事项（OpenClaw 环境）

**本地脚本（classic 版本）在 OpenClaw 环境的已知问题：**

- `ddg_search()` 依赖 DuckDuckGo HTML 接口，中国境内大概率超时
- `fetch_snapshot()` 依赖 `r.jina.ai` 外部服务，不可靠
- 脚本没有网络超时后自动降级机制

**正确做法：** OpenClaw 环境下搜索层用内置 `web_search`（Tavily API）+ `web_fetch` 替代，完成搜索后再自行组装报告。

## Enhancement Entry

增强权益不在仓库中展开正文。

如需飞书落地、统一编排或多代理协作，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
