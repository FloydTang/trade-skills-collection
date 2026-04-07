# Codex 每日 GitHub 开源发现与筛选任务

> 版本：v3.1 | 更新日期：2026-03-29
> 前序版本：openclaw-daily-discovery-prompt.md（仅覆盖主动开发链路）
> 本版本保持三线覆盖与双轨筛选，并收敛到当前 `外贸skill` 分类的三层分工

## 一、任务目标

每天从 GitHub 上发现、筛选、评估与当前外贸 Skill 业务方向紧密相关的开源工具、Skill、脚本和工作流模板。

核心目的：让 Skill 生产从"完全内部从零开发"升级为"持续发现优质开源基础 + 在其上迭代"，降低研发成本，加速交付。

**不是做泛 AI 工具榜单，不是做收藏夹。**

顶级原则固定为：

`实事求是、简洁高效`

## 零、当前仓库分工

执行本任务前，先固定这 4 条，不要混淆：

1. 当前仓库是 `外贸skill` 这一分类的真实源仓库，不是整个工具工作间的真实源。
2. `../工作间/` 是当前 `外贸skill` 分类的长期记录层，对应 Obsidian `工具工作间/外贸skill`，不是 Obsidian 顶层“工具工作间”本身。
3. Obsidian `工具工作间/外贸skill` 是记录承接层，服务后续品牌、课程、产品表达，不承接执行层日报和脚本。
4. `skill需求池.md` 不是候选收集表，只有形成明确方向判断的项目才允许升级进入；半斤九两工具库 `外贸skill` 只接收已经验证、准备推荐的最终沉淀。

补充要求：

- 不再使用仓库内旧表述 `工具工作间/`
- 不新增平行主表、平行 backlog、平行决策页
- 日报属于执行层，长期判断只收敛到 `../工作间/`
- 不把执行层内容直接等同于 Obsidian 记录层或最终推荐层
- 一旦 `../工作间/` 或 `../skill需求池.md` 发生更新，当次流程必须把对应长期文档同步到 Obsidian 并核对结果

## 零点五、Obsidian 展现规则

凡是属于当前 `外贸skill` 分类、并且会被长期复用的记录型文档或说明型文档，都应在 Obsidian `工具工作间/外贸skill` 有对应展现。

默认应展现到 Obsidian 的内容：

- `../工作间/` 下的长期主表、路线映射、分类说明
- `../skill需求池.md` 中已经稳定的方向判断
- 各 Skill 的 README、立项方案、验收说明、接入说明等人类阅读文档

默认不直接展现到 Obsidian 的内容：

- `reports/` 每日日报和周汇总
- 脚本、样例、schema、运行产物、临时中间文件

补充要求：

- 仓库是真实源，Obsidian 是展现层
- Obsidian 中可以是镜像、摘要、索引或说明，不要求机械复制所有文件

## 二、搜索方向（双线覆盖）

### A 线：主动开发（Active Outreach）

围绕已有和规划中的主动开发链路：

- 客户搜索 / lead discovery / prospect finding
- 线索整理 / lead screening / lead qualification
- 客户背调 / customer intel / company research / due diligence
- 开发信 / outreach email / cold email / sales email
- 跟进优先级 / lightweight CRM / follow-up workflow / pipeline management
- 竞品监控 / website monitoring / change detection / price tracking

### B 线：被动营销（Passive Marketing / Inbound）

围绕内容驱动获客的完整链条：

- 内容制作 / content creation / AI copywriting / blog generation / product description
- 社媒运营 / social media management / social posting / content scheduling / social analytics
- 独立站搭建 / website builder / landing page / Shopify tools / WordPress automation
- SEO 工具 / SEO analysis / keyword research / backlink / SERP tracking
- 客户对接 / chatbot / live chat / inquiry management / customer engagement
- 视频/图片营销 / video generation / image generation / product photography AI
- 邮件营销 / email marketing / newsletter / drip campaign（区别于开发信，这里偏内容触达）

### C 线：基础设施与方法论

- OpenClaw / agent workflow / promptable skill packaging / Markdown-first automation
- Claude Code skill / MCP server / tool-use workflow
- AI agent framework / multi-agent / workflow orchestration（仅与外贸场景有交集时）

## 二点五、当前阶段优先级

虽然保持 A/B/C 三线覆盖，但当前优先级不是平均推进。

当前更高优先级：

- A 线里能直接增强现有主线节点的候选
- 竞品监控相关候选，尤其是网页变化监控、字段级抽取、变化摘要、人工复核口径相关工具
- 能服务当前 `竞品监控 Skill` 首版落地的轻量候选

当前更低优先级：

- 大而全平台
- 需要重型部署和大规模编排的系统
- 为了“看起来完整”而扩出来的复杂工作流
- 与当前外贸主线关系偏弱的泛 AI 工具

## 三、双轨筛选逻辑

每天的筛选结果必须分为两个轨道：

### 🚀 轨道一：新锐增速型（Rising Stars）

筛选标准：
- 创建时间在最近 6 个月内，或虽然更早但近 3 个月内出现明显增长拐点
- Star 数增速快（如周增 50+ 或月增 200+），或 npm/pip 下载量增速明显
- 社区讨论活跃（Issue/PR 频繁）
- 可能代表新趋势或新方法论
- 风险提示：需标注"尚未充分验证"

参考搜索策略：
- GitHub Trending（按语言/时间段筛选）
- GitHub Search 按 `created:>YYYY-MM-DD` + `stars:>50` + 关键词
- 关注 Hacker News、Product Hunt、Reddit 上被讨论的新项目
- npm/pip 近期发布且下载量异常增长的包

### 🏛️ 轨道二：成熟稳定型（Proven & Stable）

筛选标准：
- Star 数 500+，有持续维护记录（最近 3 个月有 commit）
- 文档完整，有 README、示例、API 文档
- 被其他项目依赖或被知名媒体/社区推荐
- 许可证清晰（MIT / Apache 2.0 / BSD 优先）
- 已经有真实用户反馈或案例
- 接入成本可控

参考搜索策略：
- GitHub Search 按 `stars:>500` + 关键词 + `pushed:>YYYY-MM-DD`（3 个月内有更新）
- Awesome Lists（awesome-cold-email, awesome-seo, awesome-marketing, awesome-ecommerce 等）
- GitHub Topics 浏览

## 四、每日执行动作

请每天按以下顺序执行：

1. **搜索**：按 A/B/C 三线方向，在 GitHub 上搜索相关开源项目
2. **去重**：优先排除已在 `../工作间/开源工具总表.md` 中记录过的项目
3. **初筛**：排除明显无关、长期不维护、文档极弱或许可证不清晰的项目
4. **分轨**：将候选分为"新锐增速型"和"成熟稳定型"
5. **精选**：每轨道选 2-3 个（共 4-6 个），给出结构化评价
6. **落地判断**：对每个候选判断它更适合"独立搭建新 Skill"还是"整合优化到现有 Skill"
7. **更新文档**：
   - 生成当日日报 → `reports/YYYY-MM-DD.md`
   - 将值得长期保留的候选更新到 `../工作间/开源工具总表.md`
   - 将值得长期保留的落地判断更新到 `../工作间/路线映射.md`
8. **谨慎升级**：
   - 只有已经形成明确业务挂靠、落地方式和下一步动作的项目，才建议升级进 `../skill需求池.md`
   - 如果只是“值得看”，但还没到方向判断阶段，就留在 `../工作间/`
9. **判断 Obsidian 展现**：
   - 如果某条记录或说明未来会被课程、品牌、产品表达反复引用，应明确标记它需要在 Obsidian `工具工作间/外贸skill` 可见
10. **执行同步与验收**：
   - 如果本轮更新了 `../工作间/` 或 `../skill需求池.md`，必须执行 `scripts/sync_obsidian_workspace.sh`
   - 至少核对以下 Obsidian 文件已刷新到最新版本：
     - `工具工作间/外贸skill/开源工具总表.md`
     - `工具工作间/外贸skill/路线映射.md`
     - `工具工作间/外贸skill/skill需求池.md`
   - 如果仓库版已更新而 Obsidian 版未更新，本轮不能算完整完成

补充要求：

- 不为过程留痕而留痕
- 没有复用价值的信息不要写入长期文档
- 不把日报整段复制进长期主表
- 不因为当前在做某个方向，就把所有相关重型系统都判成高优先级

## 五、每个候选必须输出的字段

对每个精选候选，至少输出：

| 字段 | 说明 |
|------|------|
| 项目名称 | - |
| GitHub 链接 | - |
| 所属轨道 | 🚀 新锐增速型 / 🏛️ 成熟稳定型 |
| 一句话定位 | - |
| 对应业务线 | A线（主动开发）/ B线（被动营销）/ C线（基础设施） |
| 对应具体方向 | 如：客户搜索、社媒运营、独立站搭建等 |
| 对应现有 Skill | 如果有直接关联的现有 Skill，标注名称 |
| 候选类型 | 可直接复用工具 / 可借鉴模块 / 可借鉴工作流 / 仅供参考 |
| 许可证情况 | - |
| Star 数 | - |
| Star 增速 | 近 7 天 / 近 30 天增量（如可查到） |
| 最近更新时间 | - |
| 文档与样例完整度 | 高 / 中 / 低 |
| 接入成本 | 低 / 中 / 高 |
| 相关性评分 | 1-5 |
| 课程表达价值 | 1-5 |
| 落地方式建议 | **独立搭建新 Skill** / **整合到现有 Skill（指明哪个）** / **作为参考不直接接入** |
| 落地方式原因 | 为什么建议这种方式 |
| 推荐动作 | 建议纳入工具库 / 建议进入需求池 / 建议继续观察 / 不建议处理 |
| 推荐原因 | - |
| 风险与不确定点 | - |
| 是否需要人工复核 | 是 / 否 |

## 六、落地方式判断规则

### 建议"独立搭建新 Skill"的情况：
- 该工具覆盖的业务方向在我们的需求池中还没有对应 Skill
- 该工具功能完整且独立，不需要依附现有 Skill 就能交付价值
- 该方向有独立的课程表达价值
- 该工具可以作为新节点插入我们的业务链路

### 建议"整合到现有 Skill"的情况：
- 该工具是现有 Skill 的某个能力增强（如更好的搜索源、更好的模板、更好的评分算法）
- 接入后能直接提升现有 Skill 的质量，不需要重新立项
- 该工具是一个模块/库，不是完整方案

### 建议"作为参考不直接接入"的情况：
- 方法论或工作流设计值得借鉴，但代码不适合直接用
- 技术栈与我们不兼容，但思路有价值
- 过于重型，但其中某个子模块思路可参考

### 对竞品监控方向的额外判断规则：
- 如果工具已经覆盖网页变化监控、页面 diff、定时检查等底层能力，优先判断为“优化现有 Skill”而不是“独立新 Skill”
- 如果工具主要价值在“如何把变化解释成业务动作”，优先看它是否能服务 `竞品监控 Skill` 的摘要层
- 当前 `changedetection.io` 已确认作为竞品监控首版上游底座，后续类似候选默认拿它做参照，不轻易重复立项
- 不把“可以做很多监控能力”当成当前就该接入的理由，首版仍以少量页面、少量字段、人工复核为准

## 七、筛选标准

### 优先保留：
- 与 A/B/C 三线方向直接相关
- 能增强现有节点 Skill 或填补空白方向
- 开源许可证清晰
- 最近仍有维护
- 有 README、样例或明确输入输出
- 具备课程表达价值
- 接入成本可控

### 优先排除：
- 大而全但和当前路线衔接弱
- 长期停更、文档薄弱、样例缺失
- 许可证风险不清楚
- 需要重型基础设施改造才有意义
- 更像行业新闻，而不是可落地工具资产
- 纯 SaaS 产品的开源壳（核心功能闭源）
- 与当前最小落地链路不匹配、明显会把项目带向重系统的候选

## 八、结论标签

每个候选必须只选一个标签：

- `建议纳入工具库`
- `建议进入需求池`
- `建议继续观察`
- `不建议处理`

## 九、人工复核边界

以下情况必须标记"需要人工复核"，不能直接判为 `建议纳入工具库`：

- 许可证不清晰
- 仓库活跃度异常（如疑似刷 Star）
- 与当前主路线关系不够直接
- 接入成本明显偏高
- 需要改动我们现有架构或发布策略
- 涉及被动营销方向的新立项（因为该方向尚未有成熟 Skill，需要人工确认优先级）

## 十、日报格式要求

当日日报必须固定包含以下部分：

```
# GitHub 开源发现日报 - YYYY-MM-DD

## 今日结论摘要
- 今日新增候选数
- 🚀 新锐增速型精选数
- 🏛️ 成熟稳定型精选数
- 覆盖业务线：A线 / B线 / C线
- 建议优先人工判断项目

## 🚀 新锐增速型精选（2-3 个）
[结构化评价]

## 🏛️ 成熟稳定型精选（2-3 个）
[结构化评价]

## 今日不推荐处理项目简表

## 工作间更新建议

## 落地方式建议汇总
| 项目 | 建议落地方式 | 对应方向 | 理由 |

## 建议今天优先人工判断的项目（1-3 个）

## 备注
```

如果今天没有高质量新发现，要明确写"今天无值得推进的新候选"，但仍需说明搜索了哪些方向。

## 十一、搜索关键词参考库

以下关键词仅供参考，可根据实际情况灵活组合：

**A线关键词：**
lead generation, lead discovery, prospect finder, email finder, cold outreach, sales automation, CRM lightweight, company research, competitor monitoring, price tracker, website change detection

**B线关键词：**
content marketing AI, social media automation, social media scheduler, SEO tool, keyword research, landing page builder, Shopify automation, WordPress AI, product description generator, email marketing, newsletter tool, chatbot, live chat, video marketing AI, AI copywriting, blog generator, social analytics

**C线关键词：**
claude code skill, MCP server, agent workflow, promptable skill, markdown automation, AI agent framework, tool-use, multi-agent

**组合修饰词：**
trade, export, B2B, cross-border, ecommerce, foreign trade

## 十二、每周汇总要求

每周日（或每 7 天），除了当日日报外，额外生成一份周汇总，放在 `reports/weekly-YYYY-WNN.md`，包含：

- 本周各轨道精选总数
- 本周各业务线覆盖情况
- 本周进入 `../工作间/开源工具总表.md` 的候选汇总
- 本周落地方式建议分布（独立搭建 vs 整合优化 vs 仅参考）
- 下周建议重点搜索方向
- 本周工作间变动

## 十三、与现有文档的衔接

- 发现的新方向如果不在 `skill需求池.md` 中，应在日报中建议是否值得新增
- 落地建议如果涉及现有 4 个已交付 Skill（客户搜索、线索整理、客户背调、开发信），需明确写出具体增强点
- 如果落地建议涉及 `竞品监控 Skill`，优先围绕“少量真实页面 + 关注字段 + 最小摘要链路”来判断，而不是扩成完整监控平台
- 被动营销方向的候选暂时归入"后续扩展方向"类别，但仍需正常评审和记录
- 长期状态统一写入 `../工作间/开源工具总表.md`
- 长期落地方式统一写入 `../工作间/路线映射.md`
- 只有形成明确方向判断时，才允许建议升级进 `../skill需求池.md`
