# GitHub 开源发现自动化

这个目录用于持续发现、筛选和初步评估与当前外贸 Skill 主路线直接相关的 GitHub 开源工具、Skill、脚本和工作流模板。

它不是新的业务节点 Skill，也不是新的对外发布包。

它的定位已经收敛为“执行层”：

- 服务现有外贸 Skill 主路线的持续增强
- 为 Codex 提供固定的每日 GitHub 发现入口
- 只保留执行当日真正需要的最小留痕
- 不承担长期沉淀主阵地职责

这里服务的是当前 `外贸skill` 分类，不是未来所有 Skill 分类的总执行层。

## 顶级原则

这条工作流的顶级原则固定为：

`实事求是、简洁高效`

执行要求只保留 4 条：

- 不重复建表，能并表就并表
- 不为过程留痕而留痕，只保留后续判断会复用的内容
- 不把推断写成结论，证据不足就明确标不确定
- 不把每日日报直接堆进 `skill需求池.md`

新增一条执行闭环要求：

- 更新 `工作间/` 或 `skill需求池.md` 后，必须同步到 Obsidian `工具工作间/外贸skill` 并做一次结果核对

## 当前目标（v3.0 - 2026-03-29 更新）

当前围绕以下三线方向做 GitHub 开源发现：

### A线：主动开发（Active Outreach）
- 客户搜索 / lead discovery
- 线索整理 / lead screening
- 客户背调 / customer intel
- 开发信 / outreach email
- 跟进优先级 / lightweight CRM / follow-up workflow
- 竞品监控 / website monitoring / change detection

### B线：被动营销（Passive Marketing / Inbound）
- 内容制作 / content creation / AI copywriting / blog generation
- 社媒运营 / social media management / social posting / content scheduling
- 独立站搭建 / website builder / landing page / Shopify tools
- SEO 工具 / SEO analysis / keyword research / SERP tracking
- 客户对接 / chatbot / live chat / inquiry management
- 视频/图片营销 / video generation / product photography AI
- 邮件营销 / email marketing / newsletter / drip campaign

### C线：基础设施与方法论
- OpenClaw / agent workflow / promptable skill packaging / Markdown-first automation
- Claude Code skill / MCP server / tool-use workflow
- AI agent framework（仅与外贸场景有交集时）

### 双轨筛选逻辑
- 🚀 **新锐增速型**：近期创建或增长拐点明显，Star/下载量增速快
- 🏛️ **成熟稳定型**：Star 500+，持续维护，文档完整，有真实用户验证

默认不做泛 AI 工具榜单，也不做泛销售 SaaS 收集。

## 目录结构

```text
工作间/GitHub开源发现自动化/
├── README.md
├── prompts/
│   ├── openclaw-daily-discovery-prompt.md    # v1.0（仅主动开发，已归档）
│   ├── discovery-rules.md                    # 规则母版
│   └── automation-entry.md                   # Automation 执行入口
├── reports/
│   ├── YYYY-MM-DD.md                         # 每日日报
│   └── weekly-YYYY-WNN.md                    # 周汇总（如需要）
├── scripts/
│   ├── init_daily_discovery.py
│   └── sync_obsidian_workspace.sh
├── github-watchlist.md                       # 已迁移入口说明
├── tool-adoption-backlog.md                  # 已迁移入口说明
├── tool-adoption-decisions.md                # 已迁移入口说明
└── templates/
    ├── daily-report-template.md              # v1.0 模板（归档）
    ├── daily-report-template-v2.md           # v2.0 双轨日报模板
    ├── weekly-summary-template.md            # 周汇总模板
    ├── watchlist-template.md
    ├── adoption-backlog-template.md
    └── decision-log-template.md
```

## 固定职责

### Codex（执行层）

- GitHub 搜索（A/B/C 三线方向）
- 初筛、去重、分轨（新锐增速型 / 成熟稳定型）
- 证据整理与结构化评价
- 相关性评分与落地方式初判
- 生成每日日报（v2.0 双轨格式）
- 把真正值得长期保留的结论同步到 `../工作间/`
- 把需要长期可见的记录同步到 Obsidian `工具工作间/外贸skill`

### 人工复核（Floyd）

- 审阅日报中"建议优先人工判断"的项目
- 确认被动营销方向候选的优先级
- 与 Codex 一起维护 `../工作间/开源工具总表.md`
- 与 Codex 一起维护 `../工作间/路线映射.md`

## 文档分工

- `reports/`：只保留执行层日报与周汇总
- `../工作间/开源工具总表.md`：当前 `外贸skill` 分类的唯一长期主表，合并观察、候选、决策状态；对应 Obsidian `工具工作间/外贸skill`
- `../工作间/路线映射.md`：当前 `外贸skill` 分类的唯一长期判断页，负责和 `../skill需求池.md` 衔接
- `scripts/sync_obsidian_workspace.sh`：把需要长期可见的文档镜像到 Obsidian `工具工作间/外贸skill`
- 本目录下旧的 `github-watchlist.md`、`tool-adoption-backlog.md`、`tool-adoption-decisions.md` 仅保留迁移说明，不再作为主维护阵地

补充规则：

- `reports/` 属于执行层，不要求直接进入 Obsidian
- 只有从日报中沉淀出来、会被长期复用的判断，才进入 `../工作间/`
- 进入 `../工作间/` 后，如未来会被课程、品牌、产品表达引用，应在 Obsidian `工具工作间/外贸skill` 有对应展现
- 这一步默认通过 `scripts/sync_obsidian_workspace.sh` 执行，不再只停留在口头要求

## 结论标签

每个候选都必须归入以下 4 个标签之一：

- `建议纳入工具库`
- `建议进入需求池`
- `建议继续观察`
- `不建议处理`

## 使用方式

### 自动执行（推荐）

Codex 定时任务应以 `prompts/discovery-rules.md` 作为规则母版，并通过 `prompts/automation-entry.md` 作为 automation 执行入口，完成：

- 搜索与初筛
- 生成当日日报
- 更新 `../工作间/开源工具总表.md`
- 更新 `../工作间/路线映射.md`
- 如有变动，运行 `scripts/sync_obsidian_workspace.sh`
- 验证 Obsidian `工具工作间/外贸skill` 对应文件已刷新

### 手动触发

如需手动执行，先看当天日报，再把需要长期保留的结论同步进仓库内 `工作间/`，最后执行：

```bash
./工作间/GitHub开源发现自动化/scripts/sync_obsidian_workspace.sh
```

### 旧方式（已归档）

首次初始化或生成当天日报：

```bash
python3 ./工作间/GitHub开源发现自动化/scripts/init_daily_discovery.py
```

旧版 prompt 位于 `prompts/openclaw-daily-discovery-prompt.md`，仅覆盖主动开发方向，已被 v2.0 替代。

## 人工复核边界

以下情况不能直接判为 `建议纳入工具库`：

- 许可证风险不清晰
- 仓库活跃度存疑
- 与当前业务主路线关系偏弱
- 接入成本明显过高
- 需要重工程改造才能接入

## 验收重点

- 连续多天运行后，不重复把同一仓库写成”新发现”
- 每天精选 4-6 个候选（每轨道 2-3 个）
- 每个候选都有证据、落地方式建议和推荐动作
- 双轨分类清晰：🚀 新锐增速型 vs 🏛️ 成熟稳定型
- 三线覆盖均衡：不能长期只搜 A 线而忽略 B/C 线
- 长期有效内容最终都收敛到 `../工作间/开源工具总表.md`
- Obsidian 镜像与仓库长期文档不再允许长期漂移；发现漂移即视为流程未完成
- `../skill需求池.md` 只接收已经形成明确方向判断的条目
