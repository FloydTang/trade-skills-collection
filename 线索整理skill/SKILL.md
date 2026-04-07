---
name: trade-lead-screening
description: Normalize and screen scattered foreign-trade leads into a conservative, structured lead pool that can flow into customer-intel research. Use when an operator has company names, websites, emails, or contact clues from search results and needs a standardized output with missing-field warnings, review flags, next-step suggestions, and customer-intel-ready JSON.
---

# 线索整理 / 初筛 Skill

## Overview

用这个 Skill 把搜索阶段拿到的零散线索整理成统一格式，降低后续进入客户背调前的判断成本。

角色定位：

- `线索初筛员`
- 负责把零散线索整理成可继续处理的标准输入
- 不负责公开网页深度背调，也不负责输出外发邮件

上下游关系：

- 上游：`客户搜索skill/` 或人工整理的候选线索
- 下游：`客户背调skill/`

首版重点不是“自动判断客户值不值得做”，而是：

- 统一字段
- 标记缺失项
- 给出初步分类
- 提示人工复核点
- 生成兼容 `客户背调skill/` 的标准输入
- 当前最稳的是公司级主线索，不是精准邮箱线索

## Standard Input

输入统一为 JSON：

```json
{
  "default_country_or_market": "",
  "operator_notes": "",
  "leads": [
    {
      "company_name": "Nordic Home Textile AB",
      "company_website": "https://www.nordichometextile.example",
      "person_name": "Nadia",
      "email": "",
      "country_or_market": "Sweden",
      "source_url": "https://www.linkedin.com/company/nordic-home-textile-ab",
      "linkedin_url": "",
      "notes": "Found via home textile search results",
      "product_keywords": "linen table textile",
      "source_type": "linkedin"
    }
  ]
}
```

## Workflow

1. Normalize each lead field into a stable shape.
2. Detect obvious missing fields and risky inconsistencies.
3. Classify the lead into a conservative bucket.
4. Suggest the next action:
   - `enter_customer_intel`
   - `enrich_then_customer_intel`
   - `hold_for_manual_review`
5. Build a `customer_intel_input` payload for downstream use.
6. Output the result in JSON and optionally Markdown.

## Output Requirements

- 必须包含汇总统计
- 必须包含每条线索的标准化字段
- 必须包含缺失项
- 必须包含人工复核原因
- 必须包含下一步动作建议
- 必须包含兼容客户背调 Skill 的桥接字段
- 不能把推断写成事实
- 不能越权替代 `客户背调skill/` 输出客户情报报告
- 不能越权替代 `开发信skill/` 生成触达文案
- 没有真实公开来源时，不能强行推进下一步

## Main Scripts

默认脚本入口：

- [build_lead_screening_report.py](./scripts/build_lead_screening_report.py)
- [build_customer_intel_batch_input.py](./scripts/build_customer_intel_batch_input.py)

### Example

```bash
python3 ./scripts/build_lead_screening_report.py --input-json ./examples/sample-leads.json
```

```bash
python3 ./scripts/build_customer_intel_batch_input.py --input-json ./examples/sample-output.json
```

```bash
python3 ./scripts/run_regression_checks.py
```

## Defaults

- 首版优先本地运行
- 首版不强依赖联网
- 输出偏保守
- 初筛结果只作辅助，不替代人工判断
- 默认优先衔接客户背调 Skill

## Enhancement Entry

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
