---
name: trade-outreach-email
description: Generate conservative, editable English outreach drafts for foreign-trade sales from structured lead inputs. Use when an operator needs a first-touch or follow-up email draft with subject options, review notes, and explicit reminders not to present unconfirmed facts as facts.
---

# 开发信 Skill

## Overview

用这个 Skill 把结构化客户信息转换成可人工修改后发送的英文邮件草稿。

角色定位：

- `开发信策略员`
- 上游：人工整理输入，或 `客户背调skill/` 输出的桥接结果
- 下游：人工复核与实际发送动作
- 不负责自动发送，也不负责替代上游做搜索、初筛和背调

当前只覆盖两个场景：

- `first_touch`：首轮开发信
- `follow_up`：跟进邮件

它不是自动发送工具。目标是把零散输入整理成更稳定、更易复核的英文草稿。

## Standard Input

输入统一为 JSON：

```json
{
  "email_type": "first_touch",
  "customer_name": "Anna",
  "company_name": "Acme Foods",
  "product_or_offer": "frozen mixed vegetables",
  "goal": "introduce our factory and ask whether they are open to new suppliers",
  "country_or_market": "Poland",
  "customer_profile_summary": "Company website shows private-label frozen food focus in EU retail.",
  "previous_contact_context": "",
  "tone": "professional,warm",
  "sender_name": "Leo",
  "sender_company": "Ningbo FreshGrow Foods",
  "signature": "",
  "constraints": ""
}
```

## Workflow

1. Normalize the input fields.
2. Validate the input against the local JSON schema and confirm `email_type` is `first_touch` or `follow_up`.
3. Build subject options based on scenario, product, and company name.
4. Generate one main draft and one lighter alternative draft.
5. Attach review notes for any claim that depends on summary, historical context, pricing, capability, or other unconfirmed details.
6. Output in the structure defined in [output-template.md](./references/output-template.md).

## Output Requirements

- 必须包含邮件类型
- 必须包含 2 个标题候选
- 必须包含至少 1 个英文正文草稿
- 必须包含中文复核提示
- 必须回显关键输入依据
- 不能把不确定信息写成确定事实
- 不能越权替代人工执行发送
- 不能越权替代 `客户背调skill/` 编造客户事实
- 不能把弱证据包装成个性化事实

## Main Script

默认脚本入口是 [build_email_draft.py](./scripts/build_email_draft.py)。

### Example

```bash
python3 ./scripts/build_email_draft.py --input-json ./examples/first-touch.json
```

```bash
python3 ./scripts/run_regression_checks.py
```

## Defaults

- 本地模板生成优先
- 不强依赖联网
- 输出默认偏保守
- 不覆盖报价邮件
- 发送前必须人工复核

## Enhancement Entry

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
