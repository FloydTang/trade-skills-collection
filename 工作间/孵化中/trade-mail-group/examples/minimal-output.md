# trade-mail-group 最小模拟样例输出

## 一句话结论

这 5 个德国样例客户可以先分成 2 组：零售自用袋场景、企业礼品与活动周边场景。当前输出只支持人工复核和后续开发信草稿，不代表客户已经有采购意向。

## 输入质量检查

| 项目 | 判断 |
| --- | --- |
| 公司数量 | 5 个，满足最小样例 |
| 市场 | Germany，明确 |
| 产品 | recycled PET tote bags for retail and corporate gifting，明确 |
| 证据质量 | 全部为课程模拟备注，不是公开事实 |
| 主要缺口 | 缺少真实官网、联系人、采购记录、可持续材料偏好 |

## 分组总览

| group_id | 分组 | 公司 | 主要依据 | 触达优先级 |
| --- | --- | --- | --- | --- |
| G1 | Retail carry bag and reusable shopping context | Sample Retailer A, Sample Supermarket C, Sample Outdoor Shop E | 可复用购物、门店零售、配件类零售信号 | P1 |
| G2 | Corporate gift and event merchandise context | Sample Gift Agency B, Sample Brand Studio D | 企业礼品、定制品牌、活动周边信号 | P1 |

## G1: Retail carry bag and reusable shopping context

事实依据：

- Sample Retailer A 的模拟备注是 eco lifestyle retail，且有 sustainability positioning。
- Sample Supermarket C 的模拟备注提到 offline stores 和 reusable shopping habits。
- Sample Outdoor Shop E 的模拟备注是 outdoor retail，并有 retail accessory category 信号。

保守推断：

- 这些客户可能更关心耐用、可重复使用、门店展示和品牌一致性。
- 不能推断它们已经在找 recycled PET tote bags。

触达角度：

- 用"可复用零售袋 + 可持续材料故事 + 门店/会员活动场景"切入，而不是直接说对方需要换供应商。

英文标题候选：

1. Recycled PET tote option for reusable retail bag programs
2. A concise idea for your reusable shopping bag line
3. Retail tote bags with a clearer sustainability story

首封草稿：

```text
Hi {{first_name}},

I noticed that {{company_name}} is connected with retail and reusable shopping use cases.

We make recycled PET tote bags for retail and corporate gifting projects. This may be relevant if your team is reviewing reusable carry bags, seasonal store campaigns, or branded shopping accessories.

I do not want to assume you are sourcing this category now. If it is relevant, I can send a short material and customization overview for your review.

Best,
{{sender_name}}
```

第一次跟进节奏：

- 3-5 个工作日后跟进一次。
- 跟进只补一个具体信息点，例如材料、尺寸或定制方式。
- 不连续追问采购计划。

人工复核项：

- 是否有门店袋、会员袋、活动袋或购物袋页面。
- 是否已经公开展示现有袋类供应商或材料要求。
- 是否适合零售采购、市场部或品牌部门联系人。

## G2: Corporate gift and event merchandise context

事实依据：

- Sample Gift Agency B 的模拟备注是 corporate gifts，并有 custom branding service。
- Sample Brand Studio D 的模拟备注是 event merchandise。

保守推断：

- 这些客户可能更关心小批量定制、交期、打样、品牌视觉还原和活动交付。
- 不能推断它们有明确环保袋项目。

触达角度：

- 用"可定制礼品袋/活动周边袋"切入，强调可作为企业礼品和活动物料的一类选项。

英文标题候选：

1. Recycled PET tote bags for branded gift projects
2. Custom tote option for event merchandise briefs
3. A practical bag idea for corporate gifting programs

首封草稿：

```text
Hi {{first_name}},

I saw that {{company_name}} works around corporate gifts or branded event merchandise.

We produce recycled PET tote bags that can be used for employee gifts, event merchandise, retail campaigns, or client giveaway programs. The main value is a practical branded item with a clear recycled-material story.

If this category fits any upcoming brief, I can share a short overview with material options, common sizes, and customization notes.

Best,
{{sender_name}}
```

第一次跟进节奏：

- 4-6 个工作日后跟进一次。
- 跟进内容优先给 2-3 个适合礼品/活动场景的规格选项。
- 不承诺价格、交期或回复率，除非已有报价条件。

人工复核项：

- 是否有公开案例展示袋类或纺织配件。
- 是否需要按行业拆成礼品代理、品牌工作室、活动公司。
- 是否已有可对接的产品经理、采购或项目经理。

## 后续交接

- 交给 `客户背调skill`：补官网、联系人、现有产品线、可持续材料证据。
- 交给 `开发信skill`：只使用人工确认后的分组、角度和标题。
- 不进入发信系统，不自动发送。
