# 固定样例说明

这个目录只放组合包首版需要自己维护的演示样例。

当前首版策略不是复制四个节点的全部 examples，而是只保留两类内容：

- 组合包自己的最小搜索输入
- 下游固定背调报告 fixture

其余中间产物由组合包脚本运行时生成，或者直接复用四个节点各自已有的稳定样例。

## 当前样例清单

### 1. `fixed-search-brief.json`

作用：

- 作为组合包自己的固定入口输入
- 用于说明“主动开发从什么业务问题开始”

当前对应主题：

- 波兰市场冷冻蔬菜 / private label 场景

### 2. `reviewed-customer-intel-report.json`

作用：

- 作为首版稳定背调 fixture
- 代表“某一条线索已经过人工复核并完成背调”

当前用途：

- 保证组合包在不依赖实时联网的情况下，也能稳定演示到开发信阶段

## 当前复用的外部样例

组合包当前直接复用以下现有样例：

- `客户搜索skill/examples/frozen-food-output.json`
- `线索整理skill/examples/sample-output.json` 的结构约定
- `开发信skill/examples/customer-intel-bridged-email-input.json` 的桥接形状

说明：

- 组合包以“复用”为优先，不维护一套重复样例库
- 只有当组合包需要自己的稳定入口或稳定下游 fixture 时，才在这里单独保留文件
