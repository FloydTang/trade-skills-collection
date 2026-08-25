# Report Template（SIEGER 对齐版，2026-08-23）

Use this fixed structure when generating the final Markdown report.

总体口吻：中文业务顾问口吻，允许并鼓励下判断（可以有"我的解读"）。三条铁律不变：

1. 每个事实性声明必须能挂来源；推断必须明确标注"推断"。
2. 查不到就写"公开来源未覆盖"，禁止编造数字、近期动态和联系人信息。
3. 拦截机制不变：防务/出口管制敏感、证据过弱、实体未确认的客户，不出开发信，只出报告加拦截说明。

## Header

- Report timestamp
- Missing input fields
- Confidence note when evidence is sparse

## Verdict Card（结论先看）

报告开头固定给出评分卡，让业务员 10 秒内判断要不要继续看：

- 五维星评（★1-5）：客户成熟度 / 潜在采购能力 / 技术定制能力 / 合作价值 / 价格敏感度（用文字描述，如"中等偏高"）
- 综合开发价值：X/10
- 客户分级：A / B / C 级（含一句话理由）
- Intel Decision：`ready_for_email_draft` / `needs_manual_review` / `hold` + 需要人工复核的具体事项
- 一句话总评：这是谁、为什么值得或不值得开发

## Executive Summary

- `中文总结`：2-4 sentences, focus on who the lead likely is, what the company appears to do, and the most actionable sales angle.
- `English summary`：2-4 sentences, concise and outward-facing.

## Identity Snapshot

- Company name
- Contact name
- Email / domain
- Website
- Country / market
- Entity confidence
- Ambiguity notes

## Company Profile & Business Breakdown（业务拆解）

不止于"它是做什么的"，要拆到产品级：

- 逐条业务线列出：业务线名称、代表产品（挂来源）、面向的客户类型
- 公司概况事实：注册与实体信息、地址差异说明（注册地 vs 实际经营地）、厂房/研发设施、核心管理层及背景
- 最后必须给商业模式判断：它是制造商 / 贸易商 / 系统集成商 / 工程项目商，还是其中几种的组合，为什么

## Tech Capability & Procurement Concerns（技术能力与采购关注点）

- 推断其内部技术栈（机械/电气/PLC/软件/视觉等，标注"推断"及依据）
- 由技术栈推导：这家客户做采购决策时最可能关心什么——参数、寿命、可靠性、兼容性、交期、定制能力、认证、售后响应——并说明哪几点对我们最关键

## Scale & Financial Signals（规模与财务信号）

- 营收、员工数、经营趋势，来源优先级：工商/注册局 > 公开财务数据库 > 新闻报道
- 查不到就写"公开免费来源未覆盖"，并给出人工补查入口建议；禁止编造财务数字
- 有数据时必须给采购行为解读：价格敏感度、账期谈判倾向、降本压力、扩产/收缩信号

## Sales Model & Procurement Logic（销售模式与采购逻辑）

- 判断其销售模式（直销/渠道/项目制）与典型销售周期
- 由此推导：我们作为供应商最可能从哪个环节进入其采购链

## Competition Map（竞争对手图谱）

- 分业务线列出潜在竞争者（可含国际大牌与本地玩家）
- 注明是"潜在竞争集合"，不做一一对应宣称

## Digital Footprint

List one row per platform:

- Platform
- Handle or page
- Confidence (`high`, `medium`, `low`)
- Activity signal
- Key notes
- Source URL

## Interest & Topic Signals

List 3-8 signals:

- Signal title
- Why it matters commercially
- Evidence sources
- Confidence label

## Recent Customer Signals

List customer-side recent signals when evidence supports them:

- Signal type: expansion, hiring, funding, product_launch, channel_change, or other explicit category
- Signal title
- Source title and URL
- Observed date or period when visible
- Freshness
- Confidence label
- Why it matters commercially
- Product relevance

If no recent signal is confirmed, say so. Do not invent recency.

## Market & Compliance Signals

List target-market or industry environment signals when evidence supports them:

- Signal type: compliance, tariff, trade_policy, certification, or other explicit category
- Signal title
- Source title and URL
- Observed date or period when visible
- Freshness
- Confidence label
- Why it matters commercially
- Product relevance

These signals can support outreach context, but must not be presented as legal, customs, or compliance advice.

## Growth Opportunities（增长机会）

- 列出 2-3 条该客户所在市场的增长线，每条说清逻辑（为什么这条线会涨、它凭什么吃到）
- 标注哪些是我们的推断

## Sales Angles（切入策略）

每个 angle 必须包含：

- `中文建议` 与 `English angle`
- 对方现用品牌/部件的可核查线索；找不到线索时给明确标注的假设（"假设其 ASRS 线使用欧系减速电机"）
- 我方替代点：降本 / 缩短交期 / 定制化 / 认证 / 成套供应，必须落到具体一点
- 结合我方已授权企业资料的具体产品或能力（资料中心已授权目录内的条目）
- Why this angle fits
- Avoid / caution note if needed

优先建议"BOM 反拆"式切入：研究其现用的关键部件品牌（如 PLC、伺服、减速电机、传感器、导轨、气动件），以替代/降本/缩短交期作为突破口。

## Outreach Persona Card

- Phase 2 status: `skipped`, `generated`, or `limited_evidence`
- Public themes the lead or company appears to focus on
- Communication style clues
- Recommended outreach angles

## Personalized Outreach Pack

- 3-5 opening angles with evidence references
- 1-2 first-message English drafts
- 1-2 follow-up English drafts
- Avoid points / caution notes

## Risk Rating

- Rating: `Low`, `Medium`, or `High`
- Reasons
- Gaps that still require manual review

## 画像总结（收尾）

- 一段顾问式总结：这家公司本质上是什么、核心护城河是什么
- 综合开发价值评分（X/10）+ 最大机会 + 最大风险
- 策略一句话：不要用"产品目录+低价"开发的客户，写明应该用什么姿势

## Evidence

For every key claim, include:

- Title
- URL
- Source type
- Short note

## OpenClaw 文档规则

- OpenClaw 的搜索与抓取由 `coze-web-search`、`scrapling-official`、`coze-web-fetch` 负责；模板只规定报告结构，不改变证据来源契约。
- Feishu 文档标题仍使用 `{lead_id}_{公司简称}_背调报告`。
- `intel_decision`、`sales_angles`、`recent_signals`、`market_signals`、`evidence` 等既有字段必须保留；SIEGER 新字段为可选增强字段。
