---
title: 精选外挂开源 Skill 云端同步清单
aliases: []
type: index
status: draft
area: tool
updated: '2026-05-19'
tags:
- 主题/AI外贸
- 主题/工具系统
- 资产/总览
- 工作流/Skill开发
- 主题/B2B营销
- 主题/内容营销
- 主题/知识库
- 主题/课程交付
related:
- "[[路线映射]]"
business_scenes:
- 外贸主动开发
- 竞品监控与市场情报
- 内容营销
- 知识库与资料承接
- 工具评估与Agent治理
- 课程与交付
---
# 精选外挂开源 Skill 云端同步清单

更新日期：2026-05-19

## 这份文档解决什么

这份文档只放“外挂能力”：

- 对作战台、课程中心、品牌工作间、产品设计、知识库、自动化验证有帮助
- 但不是半斤九两定制的外贸业务主干 Skill

外贸业务主干 Skill 统一看：

- `外贸业务主干Skill云端同步清单.md`

## 作战台读取规则

外挂能力按三类展示：

1. **可直接启用**：Codex / 本地环境已有稳定入口，可作为内部执行能力。
2. **POC 优先**：值得做最小样例验证，但还不能给用户默认启用。
3. **只保留参考**：适合学习方法、校准边界或作为上界样本，不进入当前作战台运行时。

硬边界：

- 不把外挂工具写成外贸业务 Skill。
- 不把重平台塞进主动开发主链路。
- 不把未跑样例的开源工具写成可交付能力。
- 不让设计、内容、知识库工具污染外贸业务主干入口。

## 晋升通道

外挂 Skill / 工具要进入工具库，走固定六步：

```text
工具工作间候选
-> 本地 POC / 最小样例验证
-> 论坛试运行与反馈
-> 人工审核和脱敏
-> 半斤九两工具库落库
-> 作战台弹药库 / 论坛 Skill / 课程中心按权限同步
```

当前作战台论坛已经支持 `scope=forum` 授权学习链接、Agent 读帖、草稿提交、待审核发布和 `forum_skill_requests`。这些能力适合做“试运行和反馈”，但不等于自动发布。

进入 `半斤九两工具库/外贸skill` 前，必须满足：

- 有来源和许可证或已装本地 Skill 来源。
- 有最小样例、输出结果和失败边界。
- 有隐私、账号、API Key、数据出境和误判风险说明。
- 能说清对外贸企业的帮助，不只是技术展示。
- 如果要在作战台里标为 Skill，必须有明确开源骨架、安装入口或 `skill.md`；否则只能标成描述词、工具参考或方法卡。

详细 SOP 看内部维护：

- `内部维护/精选外挂开源/外挂Skill晋升通道与论坛同步流程_2026-05-19.md`

## A. 当前 Codex 已装高价值 Skill

| Skill / 工具 | 当前用途 | 作战台走向 | 边界 |
| --- | --- | --- | --- |
| `web-access` | 联网核验、网页读取、浏览器操作 | 内部核验底座 | 不替代用户授权数据源 |
| `defuddle` | 网页正文清洗成 Markdown | 内容入库和网页摘要辅助 | 只做清洗，不保证事实完整 |
| `obsidian-markdown / obsidian-cli / obsidian-bases / json-canvas` | Vault 和 Obsidian 知识库工作流 | 内部资料治理 | 不作为用户业务 Skill |
| `frontend-design / design-taste-frontend / ui-animation` | 作战台 demo、产品 UI、交互动效 | 设计与产品原型辅助 | 不变成外贸业务节点 |
| `smart-explore / mem-search / knowledge-agent / timeline-report` | 长期工程维护、记忆、知识沉淀 | 内部研发与复盘 | 不直接给用户默认展示 |
| `92ppt` | 半斤九两课程 deck 输出 | 课程中心辅助 | 只服务课程内容生产 |
| `trade-ai-talking-head-video` | 外贸短视频输出 | 品牌工作间外挂 | 不进入主动开发默认链路 |
| `hyperframes / remotion / ffmpeg / snapdom` | 视频、HTML 卡片、DOM 转图 | 内容成品输出链 | 先用于内部生产 |
| `systematic-debugging / verification-before-completion` | 排障和完成前验证 | 内部质检规范 | 不做用户功能入口 |
| `aihot` | AI 资讯和热点方法参考 | market pulse 方法参考 | 不是外贸市场事实源 |

## B. 外贸业务增强候选工具

这些工具可以增强外贸业务主干 Skill，但它们自身不是业务主干 Skill。

| 工具 | 来源 | 可服务方向 | 当前走向 | 边界 |
| --- | --- | --- | --- | --- |
| `changedetection.io` | <https://github.com/dgtlmoon/changedetection.io> | 竞品监控 | 优先作为 `竞品监控skill` 首版上游底座 | 页面变化只做信号，不直接解释战略 |
| `EdJoPaTo/website-stalker` | <https://github.com/EdJoPaTo/website-stalker> | 网站变化监控 / Git 留痕 | 竞品监控轻量补充样本 | 先验证字段清洗和复核成本 |
| `AfterShip/email-verifier` | <https://github.com/AfterShip/email-verifier> | 邮箱验证 / 联系方式补查 | 客户搜索、线索整理增强候选 | SMTP 误判和网络策略需验证 |
| `FGRibreau/mailchecker` | <https://github.com/FGRibreau/mailchecker> | 临时邮箱识别 | 邮箱质量轻量增强候选 | 不等于邮箱真实可达 |
| `firecrawl/firecrawl` | <https://github.com/firecrawl/firecrawl> | 网页抽取底座 | 搜索、背调、竞品监控增强候选 | 外部 API 和成本边界需看清 |
| `sherlock-project/sherlock` | <https://github.com/sherlock-project/sherlock> | 社媒账号初步发现 | `trade-social-account-scan` 候选增强 | username 命中不等于官方账号 |
| `soxoj/maigret` | <https://github.com/soxoj/maigret> | 社媒账号足迹枚举 | 与 Sherlock 横向验证 | 结果噪音可能高 |
| `browser-use / workflow-use` | <https://github.com/browser-use/browser-use> / <https://github.com/browser-use/workflow-use> | 浏览器动作自动化 | 方法层参考 | 当前不作为稳定默认底座 |

## C. 知识库、设计、内容输出候选

| 工具 | 来源 | 可服务方向 | 当前走向 | 边界 |
| --- | --- | --- | --- | --- |
| `llm_wiki` | <https://github.com/nashsu/llm_wiki> | 本地企业知识库 / Obsidian-compatible | 本地作战台企业知识库 POC 优先 | 不替代飞书增强入口 |
| `html-anything` | <https://github.com/nexu-io/html-anything> | HTML / PNG / 小红书 / 微信输出 | 品牌发布链 POC | 要改成半斤九两品牌视觉 |
| `wechat-publish-template` | <https://github.com/limin112/wechat-publish-template> | 公众号排版模板 | 公众号输出链参考 | 原风格不直接采用 |
| `open-design` | <https://github.com/nexu-io/open-design> | 设计实验室 | Codex 旁路设计实验 | 不进用户端 V1 运行时 |
| `12-factor-agents` | <https://github.com/humanlayer/12-factor-agents> | Agent 功能上架检查 | 转成作战台 Agent 上架 gate | 不作为运行时依赖 |
| `CLI-Anything` | <https://github.com/HKUDS/CLI-Anything> | CLI 化和 harness 方法 | 只挑相关方法参考 | 不全量安装 |
| `chatwoot` | <https://github.com/chatwoot/chatwoot> | 询盘承接 / 客服上界 | 后续询盘承接样本 | 当前太重，不进主线 |

## 当前推荐推进顺序

1. `changedetection.io`：继续推进 `竞品监控skill` 最小样例。
2. `llm_wiki`：做本地作战台企业知识库 POC。
3. `AfterShip/email-verifier` + `mailchecker`：做邮箱质量补查样例。
4. `sherlock` / `maigret`：为社媒账号初筛做误报验证。
5. `html-anything` / `wechat-publish-template` / `snapdom`：品牌内容输出链 POC。
6. `12-factor-agents`：整理成作战台 Agent 上架检查清单。

## 不进入当前默认入口

- 完整 CRM 平台
- 完整邮件营销平台
- 重型客服系统
- 未验证的社媒群控或批量抓取工具
- 只能展示技术能力、但不能形成明确业务动作的工具

这些可以保留为方法参考或上界样本，但不进入云端作战台默认能力。

## 内部维护入口

内部维护文档不作为云端默认读取入口，只用于追溯和继续验证：

- `内部维护/精选外挂开源/开源工具总表.md`
- `内部维护/精选外挂开源/路线映射.md`
- `内部维护/精选外挂开源/优质外挂工具与Skill候选清单_2026-05-19.md`
- `内部维护/精选外挂开源/外挂工具POC推进清单_2026-05-19.md`
- `内部维护/精选外挂开源/外挂工具后续推进路线图_2026-05-19.md`
