# 与客户背调 Skill 的衔接说明

这个衔接层的目标不是“把背调报告整份塞进邮件”，而是只提取适合进入开发信的保守字段。

## 推荐映射

从客户背调 Skill JSON 报告中优先提取：

- `identity_snapshot.person_name` -> `customer_name`
- `identity_snapshot.company_name` -> `company_name`
- `identity_snapshot.country_or_market` -> `country_or_market`
- `company_profile.apparent_business` -> `customer_profile_summary`
- `sales_angles[0].en` 或 `summary_en` -> `goal` 的保守参考

## 不直接写入邮件正文的内容

以下内容可以作为人工参考，但不建议自动写进邮件正文：

- `risk_rating`
- `risk_reasons`
- 弱置信度的 `interest_signals`
- `outreach_persona_card` 中带明显推断色彩的主题
- `personalized_outreach_pack` 中任何过强个性化表达

## 推荐流程

1. 先运行客户背调 Skill，导出 JSON 报告
2. 用桥接脚本生成开发信 Skill 输入
3. 人工补充 `product_or_offer`，并按需要补 `sender_name`、`sender_company`
4. 再运行开发信脚本生成邮件草稿

## 边界

- 如果背调结果中联系人或公司主体仍有歧义，不应直接推进为强个性化开发信
- 如果 `risk_rating` 为 `High`，建议先人工判断是否继续触达
- 桥接脚本默认只做字段提取和轻量改写，不做事实增强
- `product_or_offer` 属于销售方自有输入，不从背调报告自动推断
