# 开发信 Skill for OpenClaw

这是 `开发信 Skill` 的 OpenClaw-native 变体。

它不替换根目录下的本地版，而是单独维护一套更适合云端工作流的输入包装：

- 上游由 OpenClaw 先整理操作员输入
- 如有客户背调或公开资料摘要，也先由 OpenClaw 流程整理成结构化上下文
- Python 脚本只负责把这些上下文保守合并，再调用核心草稿生成逻辑

## Why This Exists

根目录版本更适合 Codex / 本地脚本直接调用。

OpenClaw 版的目标是：

- 保留相同的邮件输出结构
- 把上游上下文整理和邮件生成解耦
- 避免在 OpenClaw 版里重复维护一套完整草稿逻辑
- 继续坚持保守边界，不把上游推断直接写死到邮件中

补充一句固定口径：

- 这个目录是当前单节点的 OpenClaw 运行时变体，不是新的安装归口
- 增强权益不在仓库中展开正文
- 如需飞书落地、统一编排或多代理协作，请查看飞书文档入口

## Input Contract

OpenClaw 版接收一个包装后的 JSON：

```json
{
  "operator_input": {
    "email_type": "follow_up",
    "customer_name": "Nadia",
    "company_name": "Nordic Home Textile AB",
    "product_or_offer": "washed linen table textile collections",
    "goal": "follow up on our catalog sharing and ask whether selected fabric swatches would be useful for review",
    "country_or_market": "Sweden",
    "tone": "professional,warm",
    "sender_name": "Mia",
    "sender_company": "Hangzhou LinenCraft Textiles",
    "signature": "Best regards,\nMia\nHangzhou LinenCraft Textiles"
  },
  "public_context": {
    "customer_profile_summary": "Brand appears focused on Scandinavian home textile collections with natural material positioning.",
    "previous_contact_context": "We shared our digital catalog three days ago and mentioned low-MOQ support for seasonal collections.",
    "constraints": "Keep the follow-up soft and design-oriented.",
    "risk_rating": "Medium",
    "entity_confidence": "medium",
    "recommended_sales_angle_en": "Lead with a clean and design-oriented offer rather than a hard sell."
  }
}
```

## Run Locally

```bash
python3 ./for-openclaw/scripts/build_email_draft_from_openclaw.py \
  --input-json ./for-openclaw/examples/sample-input.json \
  --markdown-out /tmp/openclaw-email.md \
  --json-out /tmp/openclaw-email.json
```

## Runtime Rules

- `operator_input` 中的业务字段优先
- `public_context` 只作为保守补充，不应覆盖明确的操作员输入
- 如果 `risk_rating` 为 `High`，脚本会附加更强的人审约束
- 任何 `previous_contact_context` 仍然需要人工复核


## Relationship to the Classic Version

- 根目录脚本仍然是核心生成器
- `for-openclaw/` 只是 OpenClaw 适配层
- 两个版本应保持输出结构和保守边界一致
