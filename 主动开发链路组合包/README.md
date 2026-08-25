# 主动开发工作流组合包

当前状态：可交付

这个目录是默认主入口，用来把以下 4 个节点串成可暂停、可续跑、可审计的主动开发工作流：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

当前提供两个入口：

- `scripts/run_workflow.py`：系统管道入口，使用显式配置、稳定运行目录和机器可读 manifest
- `scripts/run_minimal_demo.py`：固定课堂样例与回归兼容入口

当前落地时不建议把“组合包”当成执念。组合包的价值是让主代理少切换、能安排、能收口；真实执行仍然建议一个节点一个节点跑稳：

1. 先用 1 个已知客户跑背调，建立判断信任
2. 再用 3-5 条候选客户跑搜索和线索整理
3. 最后只把通过质量门槛的对象交给开发信节点

主代理可以一次性声明 4 个子代理和统一工作区，但不应该强迫每条线索都跑满四阶段。证据不足时要暂停、补证据或人工复核。

当前链路里，客户背调是核心判断层：搜索找候选，整理做标准化，背调负责近期客户信号、市场/合规信号、风险判断和销售角度，开发信只调用这些信号生成可复核草稿。

## 可交付能力

开源版当前提供：

- 真实输入与固定回归两种运行方式
- 从客户搜索开始，或从现成客户背调证据包开始
- 阶段化中间产物
- `00-run-manifest.json` 运行状态、失败阶段、下一步和产物哈希
- 人工审批暂停与 `--resume` 续跑
- 销售角度审批绑定被审阅报告的 SHA-256、审核人和审核时间
- 每次续跑先校验 manifest 已登记产物的 SHA-256；文件缺失或被修改时拒绝继续
- `follow_up` 模式要求在配置中提供真实的 `previous_contact_context`
- 预期等待、业务拦截、配置错误和执行失败使用不同退出码
- 阶段输出先写临时文件，再原子替换正式产物
- 4 个子 skill 的开源衔接样板
- 企业表格适配与 Skill 规则沉淀契约
- 背调到开发信的近期信号和销售角度桥接样板

课程里已经讲过全景图和增强落地逻辑，这里不重复。当前不在仓库中展开：

- 飞书表结构细节
- 统一数据写回协议
- 多代理编排契约
- 给龙虾的增强流程描述词

如需这些增强内容，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>

## 当前能力边界

- 当前最稳的是公司级线索主线
- 人名职位级是辅助补全
- 精准邮箱级仍不足
- 没有真实公开来源，不应推进下一步
- 开发信节点不自行查事实，必须消费背调节点输出的近期信号、市场信号和销售角度
- 中间产物必须人工复核，不默认自动外发

## 数据容器方案

- 保底容器：`JSON / Markdown / CSV`
- 课堂标准沙盘：`Feishu Sandbox Adapter`
- 企业真实容器：`CRM / ERP / 邮箱草稿箱`，当前只留扩展位

## 企业表格与规则沉淀

- 组合包输出的是标准化能力和 `ContainerBundle`，不是固定表格模板。
- 企业已有表头优先沿用；没有可用表格时，龙虾按企业产品、市场和流程新建够用表。
- 课堂标准沙盘只提供参考映射，不能当作企业落地强制前置。
- 用户确认新字段、客户分级、背调规则、开发信风格、禁用表达或行业习惯后，必须追问：`是否更新到对应 Skill 以便下次自动复用`。真实写入必须得到用户授权。

详细契约见根目录：

- `企业表格适配与Skill沉淀规则.md`

## Quick Start

运行生产工作流：

```bash
python3 ./主动开发链路组合包/scripts/run_workflow.py \
  --config /path/to/workflow.json \
  --output-dir /path/to/runs/customer-001
```

当退出码为 `10` 时，读取 `00-run-manifest.json` 和 `06-customer-intel-report.json`。人工确认销售角度后续跑：

```bash
python3 ./主动开发链路组合包/scripts/run_workflow.py \
  --config /path/to/workflow.json \
  --output-dir /path/to/runs/customer-001 \
  --resume \
  --approved-sales-angle-id ANGLE-01 \
  --reviewer reviewer-name
```

工作流配置契约见 `schemas/workflow-contract.schema.json`。稳定退出码：

- `0`：完成
- `10`：等待人工批准销售角度
- `11`：业务门槛未通过，等待补证据或人工复核
- `2`：配置或审批输入错误
- `3`：阶段执行失败，可按 manifest 修复后续跑

跟进邮件在 `outreach` 中使用：

```json
{
  "email_type": "follow_up",
  "previous_contact_context": "We shared a short product overview on 2026-08-20.",
  "sender_company": "Your Company"
}
```

运行固定 demo：

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py
```

运行回归检查：

```bash
python3 ./主动开发链路组合包/scripts/run_regression_checks.py
```

## 推荐查看的输出

- `outputs/demo-run/09-container-bundle.json`
- `outputs/demo-run/10-container-bundle.md`
- `outputs/demo-run/11-lead-workflow.csv`
- `outputs/demo-run/12-feishu-sandbox-bundle.json`

## 组合包职责边界

- 负责串联，不负责重写
- 负责减少上下文切换，不负责催每条线索硬跑完整链路
- 负责闭环运行和失败收口，不负责自动发信
- 负责可交付系统入口，不负责在仓库里展开企业私有增强正文
- 负责输出中立容器 bundle，不把飞书写死成唯一容器
- 负责提供表头映射和规则沉淀契约，不负责替企业强制迁移到固定表格形态
