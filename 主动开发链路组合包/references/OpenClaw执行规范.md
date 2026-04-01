# OpenClaw 执行规范

这份规范只服务一个目标：

- 让 OpenClaw 第一次试跑时，优先复用同一个飞书工作容器，而不是分散创建多个多维表格或平行 lead

## 工作容器规则

当前主动开发链路在飞书侧默认只使用一个主 Base。

建议固定名称：

- `Trade Lead Workflow Hub`

这个主 Base 是整条链路的唯一工作容器。

OpenClaw 执行时必须遵守：

1. 先查是否已存在主 Base
2. 已存在则直接复用
3. 不存在才创建一个新的主 Base
4. 不允许因为缺少某张子表就再创建第二个 Base
5. 只有 `主动开发链路组合包` 允许声明或初始化这个主 Base

## Base 内固定资产

同一个 Base 下默认维护以下子表：

- `Lead Workflow Master`
- `Lead Discovery Results`
- `Lead Screening Results`

同一个工作空间下默认维护以下文档分区：

- `Customer Intel Docs`
- `Outreach Email Docs`
- `Run Logs`
- `Failure Notes`

说明：

- 子表缺失时补建子表
- 文档分区缺失时补建分区
- 不因为单个阶段缺资产而另起一个新 Base

## 安装角色分工

当前 OpenClaw 固定按两层角色理解：

- `workflow_owner`：`主动开发链路组合包`
- `stage_worker`：`客户搜索skill`、`线索整理skill`、`客户背调skill`、`开发信skill`

固定规则：

1. `workflow_owner` 才允许 bootstrap 飞书工作容器
2. `stage_worker` 只允许 attach 到现有主 Base 和主记录
3. 单节点 Skill 不允许单独声明 Base、主表或平行工作容器

## 执行顺序

OpenClaw 默认按以下顺序执行：

1. 查找或创建主 Base
2. 校验或补齐固定子表
3. 查找或创建 `Lead Workflow Master`
4. 查找当前 lead 是否已存在主表记录
5. 先写搜索结果子表
6. 再写线索整理子表
7. 只有满足条件时才创建或更新客户背调文档
8. 只有客户背调完成后才创建或更新开发信文档
9. 最后统一回写主表状态

## 主表唯一规则

`Lead Workflow Master` 是整条链路的唯一总索引表。

不论是全链路运行，还是单独运行某一个节点，都必须先接入这张主表。

固定规则：

1. 单点跑客户背调时，先查主表，再决定是否创建或更新主记录
2. 单点跑开发信时，先查主表，再决定是否创建或更新主记录
3. 同一 lead 后续补跑其他节点时，优先更新原主记录
4. 不为同一 lead 新建平行主记录

## lead 去重规则

主记录定位采用两层判断：

1. 第一优先级：`lead_id`
2. 第二优先级：`company_name + company_website/domain + email`

仅当两层判断都不能匹配现有记录时，才允许新建 lead。

如果主体匹配仍有歧义：

- 先写 `failure_reason` 或人工复核说明
- 主表状态保持 `waiting_selection`、`hold` 或 `failed`
- 不直接创建下游文档

## 单点接入规则

单独使用 `客户背调skill` 或 `开发信skill` 时，必须补齐以下动作：

1. 查主 Base
2. 查 `Lead Workflow Master`
3. 定位原 lead 记录
4. 找到原记录则继续更新
5. 找不到原记录时，才创建最小主记录

这里的“最小主记录”至少包含：

- `workflow_id`
- `lead_id`
- `company_name`
- `current_stage`
- `current_status`
- `combo_run_id`
- `asset_keys`

## 文档复用规则

客户背调和开发信默认都按“复用旧文档，再追加版本”的方式处理。

固定规则：

- 已存在客户背调文档：复用原文档，追加版本区块
- 已存在开发信文档：复用原文档，追加草稿版本区块
- 不允许每次重跑都新建一篇新文档

推荐命名：

- `客户背调 | {company_name}`
- `开发信 | {company_name}`

## 子表写入规则

当前默认子表写入规则如下：

- `Lead Discovery Results`：按 `combo_run_id + lead_id` upsert
- `Lead Screening Results`：按 `combo_run_id + lead_id` upsert

说明：

- 同一轮 demo 或批处理内，避免重复插入
- 后续如升级到长期运营模式，可再切到“主表记录 ID + stage_name”维度

## 主表回写规则

至少遵守以下规则：

1. 搜索完成后，可以先写搜索和初筛子表
2. `master_records` 是主表最终回写依据
3. 仅当 `recommended_next_action=enter_customer_intel` 且该 lead 被本轮选中时，才创建客户背调文档
4. 客户背调完成后，才允许创建或更新开发信文档
5. 开发信完成后，主表更新为 `current_stage=outreach_email`、`current_status=draft_ready`

## 链接字段规则

主表里默认优先写“文本引用字段”，不把 URL 字段当成首次试跑的必备能力。

当前建议字段：

- `search_asset_ref`
- `screening_asset_ref`
- `intel_asset_ref`
- `email_asset_ref`

原因：

- 飞书 URL 字段在 update 时格式约束更严格
- 首次试跑优先保证稳定写入
- 文本字段已经足够保存跳转链接、record URL、doc URL 或 token

如果后续确认某个飞书环境的 URL 字段稳定可写，再把文本引用同步映射到 URL 字段，不影响当前主流程。

## 失败处理规则

任何阶段失败时，都不要因为单步异常而放弃主表回写。

最少要回写：

- `current_stage`
- `current_status`
- `failure_reason`
- `last_updated_at`

如果文档或子表写入部分失败：

- 已成功创建的资产继续保留
- `asset_keys` 保留已成功部分
- `failure_reason` 写明失败步骤和错误码
- 下次补跑时优先从当前主记录继续

## 不允许的行为

- 不允许为搜索结果、线索整理结果分别创建新的 Base
- 不允许因为单点运行就绕过主表
- 不允许同一 lead 重复创建平行主记录
- 不允许每次重跑都新建客户背调和开发信文档
- 不允许因为 URL 字段写入失败就放弃整条主表回写
