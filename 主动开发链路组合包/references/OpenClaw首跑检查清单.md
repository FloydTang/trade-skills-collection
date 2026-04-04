# OpenClaw 首跑检查清单

这份清单只服务一个目标：

- 提高 OpenClaw 第一次在飞书侧落地主动开发链路时的成功率，减少误建资产、重复建表和结构跑偏

## 开跑前先确认

1. 当前默认只使用一个主 Base，不为每个阶段分别创建新的多维表格
2. 当前所有“表格”默认都指飞书多维表格中的子表
3. 当前所有“文档”默认都指飞书云文档
4. `Lead Workflow Master` 是唯一总索引表
5. 单点运行也必须先接入主表

## 第一轮执行顺序

1. 查找是否已存在主 Base
2. 存在则复用，不存在才创建
3. 在同一个 Base 下检查以下子表：
- `Lead Workflow Master`
- `Lead Discovery Results`
- `Lead Screening Results`
4. 缺哪张补哪张，不创建第二个 Base
5. 查当前 lead 是否已存在主表记录
6. 找到原记录则更新，找不到再创建最小主记录

## 每个阶段的最小动作

### 客户搜索

- 结果写入 `Lead Discovery Results`
- 不单独新建新的多维表格
- 给每条候选分配稳定 `lead_id`

### 线索整理

- 结果写入 `Lead Screening Results`
- 回写 `recommended_next_action`
- 只有符合条件的 lead 才允许继续进入背调

### 客户背调

- 先定位主表里的原 lead 记录
- 已有客户背调文档则复用原文档
- 只追加版本，不新建平行文档

### 开发信

- 先定位主表里的原 lead 记录
- 已有开发信文档则复用原文档
- 只追加草稿版本，不新建平行文档

## 主表检查项

至少确认以下字段被正常维护：

- `workflow_id`
- `lead_id`
- `company_name`
- `current_stage`
- `current_status`
- `recommended_next_action`
- `combo_run_id`
- `asset_keys`
- `failure_reason`

当前首次试跑默认优先写以下文本字段：

- `search_asset_ref`
- `screening_asset_ref`
- `intel_asset_ref`
- `email_asset_ref`

说明：

- 不要把 URL 字段当成首次试跑的硬成功条件
- 如果 URL 写入失败，文本引用字段写成功即可

## 遇到失败时怎么做

如果某一步失败，不要直接放弃整条主记录。

至少执行：

1. 回写 `current_stage`
2. 回写 `current_status`
3. 回写 `failure_reason`
4. 回写 `last_updated_at`
5. 保留已成功创建的资产引用

## 明确禁止的行为

- 不为搜索结果新建一个 Base
- 不为线索整理结果再新建一个 Base
- 不因单点运行就绕过 `Lead Workflow Master`
- 不为同一 lead 建多个平行主记录
- 不因重跑就反复新建客户背调和开发信文档
- 不因 URL 字段失败就放弃主表回写

## 给 OpenClaw 的简版执行提示

可直接复用这段约束：

```text
当前飞书落地默认只允许使用一个主 Base。所有表格都应作为该 Base 下的子表创建或复用，不要为搜索结果、线索整理结果分别新建新的多维表格。Lead Workflow Master 是唯一总索引表。无论是全链路运行，还是单独跑客户背调或开发信，都必须先查主表并优先更新原 lead 记录，不新建平行 lead。客户背调文档和开发信文档默认优先复用旧文档并追加版本。若 URL 字段回写失败，改写文本 asset_ref 字段，并继续完成主表状态回写。
```

## 推荐阅读顺序

1. `OPENCLAW.md`
2. `主动开发链路组合包/README.md`
3. `主动开发链路组合包/references/飞书留痕字段映射.md`
4. `主动开发链路组合包/references/OpenClaw执行规范.md`
5. `主动开发链路组合包/outputs/demo-run/09-feishu-workflow-bundle.json`
6. `主动开发链路组合包/outputs/demo-run/09-feishu-workflow-bundle.json`
