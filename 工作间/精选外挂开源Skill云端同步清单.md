---
title: 精选外部Skill云端同步清单
aliases:
  - 精选外挂开源 Skill 云端同步清单
  - 精选外挂开源Skill云端同步清单
type: index
status: draft
area: tool
updated: '2026-05-25'
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
# 精选外部Skill云端同步清单

更新日期：2026-05-25

## 这份文档解决什么

这份文档对应当前物理目录 `精选外挂开源Skill`，对外统一理解为 **精选外部Skill**。

它承接外贸Skill之外的第二大板块：

- 对课程工作间、作战台、品牌工作间、产品设计、知识库、自动化验证有帮助
- 但不是半斤九两自研或深度定制的外贸业务 Skill

它不是可有可无的附属，也不是旧工具垃圾桶。

外贸Skill 统一看：

- `../外贸业务主干Skill/外贸业务主干Skill云端同步清单.md`

## 课程工作间读取规则

精选外部Skill给课程工作间读取时按三类判断：

1. **可直接启用**：Codex / 本地环境已有稳定入口，可作为内部执行能力。
2. **POC 优先**：值得做最小样例验证，但还不能给用户默认启用。
3. **只保留参考**：适合学习方法、校准边界或作为上界样本，不进入当前课程库正文或作战台运行时。

硬边界：

- 不把精选外部Skill写成外贸业务 Skill。
- 不把重平台塞进主动开发主链路。
- 不把未跑样例的开源工具写成可交付能力。
- 不让设计、内容、知识库工具污染外贸业务主干入口。

## 承接范围

精选外部Skill用于承接：

- 外部开源工具和开源 Skill
- Codex / Claude / Agent 能力增强
- 龙虾系列升级、HomeMac、Mars / Hermes 相关增强
- 环境安装、自动化验证、知识库工具、视觉 / 视频辅助工具
- 对产品设计和本地作战台有启发的 POC

## 晋升通道

精选外部Skill要进入工具库，走固定六步：

```text
工具工作间候选
-> 本地 POC / 最小样例验证
-> 人工审核和脱敏
-> 半斤九两工具库落库
-> 课程工作间课程化
-> 半斤九两课程库
-> 作战台同步 / 飞书知识库同步
-> 论坛推广、讨论和反馈回流
```

当前作战台论坛已经支持 `scope=forum` 授权学习链接、Agent 读帖、草稿提交、待审核发布和 `forum_skill_requests`。这些能力适合推广、解释、讨论和反馈回流；不是工具库上游，也不自动决定工具库入库。作战台用户可见内容应来自课程工作间和课程库整理后的同步稿，不直接展示工具库原始目录。

进入 `半斤九两工具库/精选外挂开源Skill` 前，必须满足：

- 有来源和许可证或已装本地 Skill 来源。
- 有最小样例、输出结果和失败边界。
- 有隐私、账号、API Key、数据出境和误判风险说明。
- 能说清对外贸企业的帮助，不只是技术展示。
- 能说清适合放进哪一类课程场景、作业或飞书增强入口。
- 如果要在作战台里标为 Skill，必须先经过课程化表达，并有明确开源骨架、安装入口或 `skill.md`；否则只能标成描述词、工具参考或方法卡。

当前台账和详细 SOP 看内部维护：

- `内部维护/精选外部Skill候选验证台账.md`
- `内部维护/外挂Skill晋升通道与论坛同步流程_2026-05-19.md`

## 完整候选池口径

龙虾或 Mars 看到的 25 个左右，是云端同步清单里的精选可见层，不是完整候选池。

完整长期主表在 `内部维护/开源工具总表.md`。截至 2026-05-25，主表约有 98 个外部候选，另有 27 个本机已装或已验证可复用 Skill。对外展示只取其中能讲清业务价值、客户场景和使用边界的一小层。

读取顺序：

1. 客户 / 论坛可见层：本文件和 `Mars论坛每日发布队列.md`。
2. 当前验证动作：`内部维护/精选外部Skill候选验证台账.md`。
3. 历史来源和备用候选：`内部维护/开源工具总表.md`。

## A. 当前 Codex 已装高价值 Skill

| Skill / 工具 | 当前用途 | 课程化走向 | 边界 |
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

这些工具可以增强外贸Skill，但它们自身不是业务主干 Skill。

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
| `Understand-Anything` | <https://github.com/Lum1104/Understand-Anything> | 知识图谱 / 代码库与知识库理解 | 小范围 POC，辅助 README 路由说明图 | 不全库扫描 Vault；不默认给每个 README 加图；自动图不作为结构真相源 |
| `html-anything` | <https://github.com/nexu-io/html-anything> | HTML / PNG / 小红书 / 微信输出 | 品牌发布链 POC | 要改成半斤九两品牌视觉 |
| `wechat-publish-template` | <https://github.com/limin112/wechat-publish-template> | 公众号排版模板 | 公众号输出链参考 | 原风格不直接采用 |
| `open-design` | <https://github.com/nexu-io/open-design> | 设计实验室 | Codex 旁路设计实验 | 不进用户端 V1 运行时 |
| `12-factor-agents` | <https://github.com/humanlayer/12-factor-agents> | Agent 功能上架检查 | 转成作战台 Agent 上架 gate | 不作为运行时依赖 |
| `learn-harness-engineering` | <https://github.com/walkinglabs/learn-harness-engineering> | Harness Engineering / Agent治理 / 体系治理方法 | 只作治理方法参考 | 不安装、不克隆、不写成业务 Skill |
| `CLI-Anything` | <https://github.com/HKUDS/CLI-Anything> | CLI 化和 harness 方法 | 只挑相关方法参考 | 不全量安装 |
| `chatwoot` | <https://github.com/chatwoot/chatwoot> | 询盘承接 / 客服上界 | 后续询盘承接样本 | 当前太重，不进主线 |

## D. 2026-05-21 新工具分流

这些是 Twitter 手动发现的新候选。当前只进入验证、设计或案例层，不进入作战台主页面。

| 工具 | 来源 | 可服务方向 | 当前走向 | 边界 |
| --- | --- | --- | --- | --- |
| Codex Subagents | <https://developers.openai.com/codex/subagents> | Codex 长任务、多 Agent 派工、本地作战台任务拆解 | 先整理使用模板和本地配置建议 | 只有明确要并行/分派时才开；会增加 token 和管理成本 |
| Multica | <https://github.com/multica-ai/multica> | 本地作战台 agent team 面板 | 本地作战台 POC 参考 | 不替换 Hermes / OpenClaw / Codex，只借鉴派工、进度、技能沉淀 |
| Nuwa Skill | <https://github.com/alchaincyf/nuwa-skill> | 人物 / 岗位 / 自我分身蒸馏 | Codex / Hermes 分身候选 | 必须写明公开资料快照和诚实边界，不能冒充本人私密想法 |
| Flowboard | <https://github.com/crisng95/flowboard> | TikTok / 产品视频节点流 | 作为外贸Skill内容营销 / TikTok 陪跑分支参考 | 不直接让普通用户学 Google Flow / Claude CLI / 复杂视频工程 |
| Voicebox | <https://github.com/jamiepine/voicebox> | 本地语音输入输出、AI 分身播报 | 本地实验和 Hermes 语音能力参考 | 声音克隆必须有授权，不进作战台前台 |
| OpenHuman | <https://github.com/tinyhumansai/openhuman> | 私有个人 AI / agent 交互 | 观察结构 | early beta，不替换 Hermes |
| OpenStock | <https://github.com/Open-Dev-Society/OpenStock> | Watchlist、提醒、行情面板 | `trade-market-pulse` / 竞品监控 UI 参考 | 不做股票投资模块，不给金融建议 |
| WebToApp | <https://github.com/shiahonb777/web-to-app> | 作战台移动入口封装 | 仅作安全模式参考 | 强权限、反调试、强制运行类能力不纳入 |
| ERPNext | <https://github.com/frappe/erpnext> | ERP / 内部 CRM 上界 | 客户经营工作台参考 | 不进入 `trade.tang92.com` 外贸作战台 |
| Rerun | <https://rerun.io/> | 物理 AI 数据层、互动主页表达 | 产品设计参考 | 暂无外贸业务动作，不立项 |
| ziwei-doushu | <https://github.com/Renhuai123/ziwei-doushu> | 垂直知识库 + 算法 + 语料案例 | Skill 化案例参考 | 不进外贸主链路 |
| Amp GPT-5.5 | <https://ampcode.com/models/gpt-5.5> | Codex 使用策略 | 内部提示词和模型策略参考 | 第三方评测，只做辅助口径 |

## E. 2026-05-24 新工具分流

这些是新补充的精选外部 Skill / 工具。当前只进入候选池、论坛方法帖或内部 POC，不直接进入作战台主页面。

| 工具 | 来源 | 可服务方向 | 当前走向 | 边界 |
| --- | --- | --- | --- | --- |
| Humanize Text | <https://github.com/lynote-ai/humanize-text> | AI 文本改写 / 合规边界 | 只保留风险参考 | 项目主打绕过 AI 检测，不能作为客户推荐工具；只参考多轮改写和翻译链路的风格变化风险 |
| browse.sh | <https://browse.sh/> | 浏览器自动化 / Web Skill Catalog | Codex / 本地作战台 POC 参考 | 不替代现有 `web-access` / Browser 插件；先研究站点技能封装、选择器和 XHR 抽取降本 |
| Multica | <https://github.com/multica-ai/multica> | 本地作战台 agent team 面板 | 已在 2026-05-21 候选中，维持 POC 参考 | 不重复立项，不替换 Hermes / OpenClaw / Codex |
| awesome-gpt-image-2 | <https://github.com/freestylefly/awesome-gpt-image-2> | 图像提示词 / 内容营销视觉 | 内容营销视觉模板 POC | 只转译结构和方法，不原样搬运案例；注意版权、品牌视觉和平台模型差异 |
| LongLive | <https://github.com/NVlabs/LongLive> | 长视频生成基础设施 | 视频链路上界样本 | NVIDIA 研究 / GPU 基础设施太重，不进客户默认工具或本地作战台 V1 |
| Agent Light | <https://github.com/eternityspring/agent-light> | Claude Code 状态灯 / 物理反馈 | Codex / HomeMac 体验参考 | 需要 Arduino 硬件，客户价值弱，不进论坛主推 |
| CC Note Ops | <https://github.com/SIXIANGGUO/cc-note-ops> | Obsidian 内容工作台 / Claude Code 笔记操作 | Vault / 品牌发布链 / 课程工作间 POC | 先在测试 Vault 验证，不直接装进主 Vault；注意插件权限、备份和脚本执行边界 |

## 当前 Codex 已处理

- 已安装 `huashu-nuwa`：用于人物、岗位、自我分身和 Hermes / Codex 视角蒸馏。
- 已开启 Codex multi-agent，并配置 `tool_researcher`、`skill_distiller`、`workbench_planner` 三个自定义 subagents。
- 暂不安装 Multica、Flowboard、Voicebox、OpenHuman、OpenStock、WebToApp、ERPNext；它们先作为参考或 POC，不进入 Codex 默认运行环境。

## 客户 / 论坛推荐分层

| 分层 | 工具 | 推荐场景 | 处理口径 |
| --- | --- | --- | --- |
| 已可发论坛 | `12-factor-agents`、`changedetection.io`、`llm_wiki`、`Sherlock / Maigret` | Agent 上架检查、竞品监控、本地知识库、社媒账号候选发现 | 进入 Mars P1 队列，写成方法参考帖或工具分享帖 |
| 建议补进队列 | `AfterShip/email-verifier + mailchecker`、`firecrawl`、HTML 输出链 | 邮箱质量补查、网页抽取、公众号 / 小绿书 / 报告输出 | 可给客户讲，但必须强调误判、成本、人工复核和品牌视觉改造 |
| 观察型方法帖 | Codex Subagents、Flowboard、Understand-Anything、`browser-use / workflow-use`、browse.sh、Multica、CC Note Ops、awesome-gpt-image-2 | Codex 长任务、TikTok 节点流、知识图谱、浏览器自动化、多 Agent 面板、Obsidian 内容工作台、图像提示词模板 | 适合论坛讨论和内部规划，不写成默认交付能力 |
| 仅内部参考 | Open Design、`CLI-Anything`、`learn-harness-engineering`、LongLive、Agent Light | 设计实验、CLI 化方法、Agent 治理、长视频上界、物理状态反馈 | 不安装到默认环境，不直接给客户作为现成功能 |
| 不推荐默认给客户 | Chatwoot / CRM / ERP / 重营销平台、`remove-ai-watermarks`、OSIRIS、Humanize Text | 询盘承接上界、客户经营上界、合规边界、内容诚信风险 | 只做上界或风险参考，不进作战台默认入口 |

## 当前推荐推进顺序

1. Codex Subagents：先整理使用模板，服务 Codex 长任务和本地作战台多 Agent 派工。
2. Multica：作为本地作战台 agent team 面板参考，先 POC 不替换现有运行栈。
3. Flowboard：拆给外贸Skill的内容营销 / TikTok 陪跑分支，优先反哺账号调研、视频选题库和脚本任务包。
4. Nuwa Skill：做人物 / 岗位 / 自我分身蒸馏边界模板，先服务 Hermes / Codex 内部。
5. `changedetection.io`：继续推进 `竞品监控skill` 最小样例。
6. `firecrawl`：评估能否作为客户搜索、背调和竞品监控的网页抽取底座。
7. `llm_wiki`：做本地作战台企业知识库 POC。
8. `Understand-Anything`：先对 `体系治理/` 或 `产品工作间/92code/` 做小范围知识图谱 POC，再决定是否产出 README 路由说明图。
9. `AfterShip/email-verifier` + `mailchecker`：做邮箱质量补查样例。
10. `sherlock` / `maigret`：为社媒账号初筛做误报验证。
11. HTML 输出链：验证公众号、小绿书和报告输出样例。
12. browse.sh：评估浏览器技能封装和 XHR 抽取方法是否能反哺本地作战台。
13. CC Note Ops：只在测试 Vault 做 Obsidian 内容工作台 POC。
14. awesome-gpt-image-2：抽取 3 个内容营销视觉模板，转成半斤九两风格提示词。

## 不进入当前默认入口

- 完整 CRM 平台
- 完整邮件营销平台
- 重型客服系统
- 未验证的社媒群控或批量抓取工具
- 只能展示技术能力、但不能形成明确业务动作的工具

这些可以保留为方法参考或上界样本，但不进入课程库正文或云端作战台默认能力。

## 内部维护入口

内部维护文档不作为课程库或作战台默认读取入口，只用于追溯和继续验证：

- `内部维护/README.md`
- `内部维护/精选外部Skill候选验证台账.md`
- `内部维护/开源工具总表.md`
- `内部维护/路线映射.md`
- `内部维护/外挂Skill晋升通道与论坛同步流程_2026-05-19.md`

日期型候选清单、POC 推进清单和路线图已经降权为过程证据，当前推进顺序以 `内部维护/精选外部Skill候选验证台账.md` 为准。
