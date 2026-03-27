# 主动开发最小闭环链路组合包

当前状态：设计中，已具备最小可演示骨架

这个目录用于把以下 4 个已可用节点，组织成一个可演示、可复用、可作为会员权益交付的最小主动开发闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

它不是新的大而全 Skill，也不是总编排器，而是母目录第二层的链路组合包。

## 当前重点说明

当前这个组合包只围绕下面 4 个已完成节点展开：

- `客户搜索skill`
- `线索整理skill`
- `客户背调skill`
- `开发信skill`

当前不把母目录里其他占位目录视为本组合包的一部分，也不建议 agent 在首版运行时主动扩展到其他未完成 Skill。

## 当前定位

- 服务课程演示，让学员看到“从搜客户到出开发信”的最小业务闭环
- 服务公开分发，让用户拿到比单节点更接近真实业务动作的开源组合包
- 服务业务闭环验证，先把输入输出衔接、人工复核点和固定样例做稳定
- 服务后续自动化，为未来轻量自动化和总编排器提供基线

## 首版原则

- 只复用现有 4 个节点 Skill 的稳定能力
- 不重写搜索、整理、背调、开发信的内部逻辑
- 中间产物必须可见、可保存、可人工复核
- 首版验收不依赖实时联网结果数量
- 必须明确哪些步骤先人工复核，哪些步骤后续再自动化

## 当前目录结构

```text
.
├── README.md
├── 立项方案.md
├── examples/
│   ├── README.md
│   ├── fixed-search-brief.json
│   └── reviewed-customer-intel-report.json
├── references/
│   ├── 固定样例方案.md
│   ├── 课程演示路径.md
│   ├── 运行与安装.md
│   ├── 会员交付清单.md
│   ├── 验收与边界.md
│   └── 目录与命名约定.md
└── scripts/
    └── run_minimal_demo.py
```

说明：

- `examples/` 放组合包自己的固定演示输入和下游稳定 fixture
- `references/` 放课程表达、验收规则、命名规范和固定样例说明
- `scripts/` 只放串联脚本，不复制四个节点的内部实现

## 当前推进结论

截至当前版本，这个组合包已经完成：

- 固定样例入口
- 稳定背调 fixture
- 最小串联脚本
- 统一阶段命名
- 本地可重复生成的 demo 输出目录

但还没有宣称完成：

- 完整会员发放流程
- OpenClaw 变体
- 实时联网稳定验收
- 总编排器级自动化

## 首版固定样例

首版固定样例采用“波兰冷冻食品主动开发”演示路径，原因是当前四个节点已经有较完整的 frozen food 样例链路，复用成本最低。

首版默认样例包含：

- 搜索输入：`examples/fixed-search-brief.json`
- 搜索固定输出：复用 `客户搜索skill/examples/frozen-food-output.json`
- 线索整理桥接：由 `客户搜索skill/scripts/build_lead_screening_input.py` 生成
- 线索整理结果：由 `线索整理skill/scripts/build_lead_screening_report.py` 生成
- 背调批量输入：由 `线索整理skill/scripts/build_customer_intel_batch_input.py` 生成
- 固定背调报告：`examples/reviewed-customer-intel-report.json`
- 开发信桥接输入：由 `开发信skill/scripts/build_email_input_from_customer_intel.py` 生成
- 开发信草稿：由 `开发信skill/scripts/build_email_draft.py` 生成

## 推荐演示流程

### 阶段 1：客户搜索

输入：

- 搜索条件 JSON

输出：

- 候选客户清单 `01-lead-discovery-output.json`
- 候选客户说明 `01-lead-discovery-output.md`

当前首版策略：

- 演示时优先使用固定输出，不把实时联网结果作为验收依据
- 课程里可以解释真实联网入口，但首版演示以稳定样例为准

### 阶段 2：线索整理

输入：

- 搜索结果 JSON

输出：

- 线索整理输入 `02-lead-screening-input.json`
- 线索整理结果 `03-lead-screening-output.json`
- 线索整理说明 `03-lead-screening-output.md`

这里的核心价值：

- 把候选客户变成标准字段
- 明确缺失项和推荐动作
- 把“能直接进入背调”的线索筛出来

### 阶段 3：客户背调准备

输入：

- 线索整理结果 JSON

输出：

- 可进入背调的批量输入 `04-customer-intel-batch.json`
- 本轮选择进入演示的单条线索 `05-selected-customer-intel-input.json`

当前默认人工复核点：

- 必须先人工选定本轮演示要进入背调的 lead
- 如果线索字段缺失或 `recommended_next_action` 不是 `enter_customer_intel`，不能直接往下走

### 阶段 4：客户背调

输入：

- 已人工确认的单条背调输入

输出：

- 客户情报报告 `06-customer-intel-report.json`

首版策略：

- 默认使用固定背调报告 fixture 演示
- 可选再切到真实脚本运行，但不把实时联网成功当成当前组合包的必要验收条件

### 阶段 5：开发信

输入：

- 客户情报报告 JSON

输出：

- 开发信桥接输入 `07-email-input.json`
- 开发信草稿包 `08-email-draft.json`
- 开发信 Markdown `08-email-draft.md`

当前默认人工复核点：

- `product_or_offer`
- `sender_name`
- `sender_company`
- 邮件中所有涉及客户事实的句子

## 中间产物命名建议

建议组合包统一用“阶段编号 + 动作名”的方式保存中间产物：

- `01-lead-discovery-output.json`
- `02-lead-screening-input.json`
- `03-lead-screening-output.json`
- `04-customer-intel-batch.json`
- `05-selected-customer-intel-input.json`
- `06-customer-intel-report.json`
- `07-email-input.json`
- `08-email-draft.json`
- `08-email-draft.md`

这样做的目的：

- 课程演示时容易讲清每一步
- 会员用户容易看懂先后顺序
- 出问题时容易快速定位在哪一阶段

## 最小串联脚本

当前提供：

- `scripts/run_minimal_demo.py`
- `scripts/export_feishu_workflow_bundle.py`

这个脚本的职责是：

- 复用四个节点现有脚本串起最小演示流程
- 默认使用固定搜索输出和固定背调报告
- 生成一个完整的 demo 输出目录

这个脚本当前不负责：

- 重写搜索逻辑
- 做复杂多代理编排
- 自动发信
- 自动回写 CRM

`scripts/export_feishu_workflow_bundle.py` 的职责是：

- 读取已经生成好的阶段产物
- 输出 `09-feishu-workflow-bundle.json`
- 把主表 schema、阶段资产 payload、主表回写记录和重跑规则打包给 OpenClaw

## 本地运行方式

### 运行前提

- 当前母目录下四个单节点 Skill 已存在
- 本地可用 `python3`
- 当前只验证“固定样例模式”，不要求联网搜索稳定可用

### 推荐命令

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py
```

如果希望把结果输出到单独目录：

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py \
  --output-dir ./主动开发链路组合包/outputs/demo-20260325
```

## 飞书 / OpenClaw 落地入口

当前推荐入口不是让 OpenClaw 自己重新理解整条链路，而是：

1. 先运行 `scripts/run_minimal_demo.py`
2. 再读取 `outputs/.../09-feishu-workflow-bundle.json`
3. 严格按 bundle 中的：
   - `master_table_schema`
   - `stage_assets`
   - `master_records`
   去创建飞书资产和回写状态

当前载体约定：

- 所有结构化“表”默认都用飞书多维表格
- 所有长文本“文档”默认都用飞书云文档

## 单点使用如何融合

虽然这个组合包默认展示全链路，但飞书主表并不要求每条 lead 都必须从搜索阶段开始。

下面这些入口都允许直接融合到同一张主表：

- 外部导入客户名单
- 人工录入一条 lead
- 只单独跑客户背调
- 只单独跑开发信

融合原则：

- 主表是总索引，不是只服务组合包
- 同一 lead 优先复用已有主记录
- 单点 Skill 也要回写 `current_stage`、`current_status` 和资产链接

举例：

- 如果只跑客户背调，就从 `customer_intel` 阶段切入主表
- 如果只跑开发信，就从 `outreach_email` 阶段切入主表
- 如果后续再补跑前序步骤，不是新建 lead，而是补齐同一条主记录

如果希望替换邮件阶段的产品和发件信息：

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py \
  --product-or-offer "frozen broccoli and mixed vegetables" \
  --sender-name "Leo" \
  --sender-company "Ningbo FreshGrow Foods"
```

更完整说明见 `references/运行与安装.md`。

## 当前已验证的输出

当前版本已本地验证可以稳定生成以下文件：

- `01-lead-discovery-output.json`
- `02-lead-screening-input.json`
- `03-lead-screening-output.json`
- `03-lead-screening-output.md`
- `04-customer-intel-batch.json`
- `05-selected-customer-intel-input.json`
- `06-customer-intel-report.json`
- `07-email-input.json`
- `08-email-draft.json`
- `08-email-draft.md`

这些文件当前默认输出到：

- `主动开发链路组合包/outputs/demo-run/`

## 哪些步骤必须人工复核

首版必须人工复核：

- 从线索整理结果中决定哪一条进入本轮背调演示
- 任何证据弱、字段缺失或实体歧义较高的线索
- 客户背调报告里的风险评级、身份匹配和销售切入角度
- 开发信里的产品、语气和所有未确认事实

首版可后续自动化但暂不强推：

- 从线索整理结果自动挑选“最适合演示”的 lead
- 批量逐条调用客户背调
- 根据风险等级自动切换不同邮件模板
- 输出统一 ZIP 包和发放清单

## 可演示与可交付的边界

达到“可演示”至少需要：

- 文档能讲清链路定位
- 固定样例能稳定跑出完整中间产物
- 串联脚本可跑
- 人工复核点明确

达到“可交付”还需要：

- 有稳定的组合包目录和样例说明
- 有安装与运行说明
- 有课程演示路径
- 有会员交付时的最小打包范围说明
- 至少一套稳定输出可重复复现

## 课程演示路径

推荐课程内按以下顺序讲：

1. 先讲为什么不能一上来就做总编排器
2. 再讲四个单节点分别解决什么问题
3. 再展示组合包如何保留中间产物和人工复核点
4. 最后演示从固定样例到开发信草稿的完整跑通

更具体的话术和节奏见 `references/课程演示路径.md`。

## 当前公开分发最小内容范围

首版建议公开仓库至少包含：

- 组合包 README
- 固定样例输入
- 固定背调报告 fixture
- 最小串联脚本
- 命名与目录规范
- 课程演示路径说明
- 运行与安装说明
- 公开分发清单
- 验收与边界说明

首版暂不要求：

- 网站后台
- 自动会员鉴权
- 私有下载系统
- 复杂配置中心

建议分发说明见 `references/会员交付清单.md`。

## 与现有仓库的关系

- 单节点 Skill 继续作为公开可用和独立发布的最小单元
- 这个组合包主要服务母目录第二层：链路组合包
- 面向会员的打包交付应优先和会员权益说明联动
- 这个组合包的价值在于“串联与复用”，不是替代单节点仓库

作者：半斤九两科技
