# Trade Lead Discovery

用公开网页和 LinkedIn 结果线索，找出第一批可继续进入线索整理的候选客户。

当前状态：可交付

## 开源权益默认包含什么

- 单独可运行的公开搜客能力
- 固定样例输入输出
- 可桥接到 `线索整理skill` 的标准输入
- 最小脚本入口

## 这个 Skill 解决什么问题

- 已经知道产品、市场和客户类型
- 但不会系统地搜第一批候选客户
- 需要保守、可复核的公开来源结果

## 职责边界

- 负责公开来源发现
- 负责候选公司线索生成
- 负责输出官网、电话、通用邮箱、LinkedIn 线索和来源链接
- 不负责标准化初筛
- 不负责深度客户背调
- 不负责开发信生成

## 当前默认能力

- 行业关键词搜客
- 公司级线索发现
- 展会入口定位
- 官网、电话、通用邮箱抓取
- LinkedIn 公司页和可见联系人线索补充

## 当前不默认承诺

- 精准个人邮箱稳定补齐
- 完整人物档案稳定补齐
- 没有公开来源时继续推进下游

## 输入输出

输入：

- 产品
- 市场
- 客户类型
- 关键词和约束

输出：

- 结构化候选客户清单
- 来源链接
- 可见联系人线索
- 补查建议
- 可桥接到 `线索整理skill` 的输入

## 依赖提醒

- `已安装` 不等于 `已可用`
- 搜索工具要区分 `已安装`、`已配置`、`已登录`、`已跑通`
- LinkedIn 类能力不是默认开箱即用
- 云端和本地环境可能不同

## Quick Start

```bash
python3 ./scripts/build_lead_discovery_report.py \
  --input-json ./examples/frozen-food-search.json \
  --markdown-out /tmp/lead-discovery.md \
  --json-out /tmp/lead-discovery.json
```

```bash
python3 ./scripts/build_lead_screening_input.py \
  --input-json ./examples/frozen-food-output.json \
  --json-out /tmp/lead-screening-input.json
```

## 增强权益入口

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
