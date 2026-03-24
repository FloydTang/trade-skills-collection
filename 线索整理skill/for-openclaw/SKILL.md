---
name: trade-lead-screening-openclaw
description: Normalize an OpenClaw lead bundle into a conservative lead-screening package with missing-field warnings, manual-review reasons, and customer-intel-ready payloads.
---

# 线索整理 / 初筛 Skill for OpenClaw

## Overview

这个变体假设搜索和抓取已经由 OpenClaw 工作流完成。

Python 层只负责：

- 接收线索包
- 统一字段
- 给出初筛提示
- 桥接客户背调输入

## Expected Input

```json
{
  "country_or_market": "Germany",
  "operator_notes": "Use conservative screening.",
  "lead_candidates": [
    {
      "company_name": "Atelier Loom GmbH",
      "company_website": "atelier-loom.de",
      "person_name": "Mira Stein",
      "email": "mira@atelier-loom.de",
      "source_url": "https://atelier-loom.de/about",
      "notes": "Premium table textile positioning."
    }
  ]
}
```
