---
name: trade-lead-screening-openclaw
description: Normalize an OpenClaw lead bundle into a conservative lead-screening package with missing-field warnings, manual-review reasons, and customer-intel-ready payloads.
openclaw_role: stage_worker
workspace_owner_skill: trade-active-outreach-combo
single_skill_policy: attach_only
feishu_container_creation: forbidden
requires_master_base: true
requires_master_record: true
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

## Enhancement Entry

增强权益不在仓库中展开正文。

如需飞书落地、统一编排或多代理协作，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
