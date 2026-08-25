# Trade Lead Discovery

用公开网页、LinkedIn 结果线索，以及用户授权的数据源，找出第一批可继续进入线索整理的候选客户。

> 唯一开发源是 [trade-skills-collection](https://github.com/FloydTang/trade-skills-collection)；[trade-lead-discovery](https://github.com/FloydTang/trade-lead-discovery) 是独立发行镜像。

当前状态：可交付

## 这个 Skill 解决什么问题

- 已经知道产品、市场和客户类型
- 但不会系统地搜第一批候选客户
- 需要保守、可复核的来源结果
- 希望把海关数据导出、展会名单、行业协会名单、企业 CRM / Excel 或历史成交数据接入同一套搜索流程

当前定位不是“精准客户机器”，而是“候选客户发现器”。

## 职责边界

- 负责公开来源发现
- 负责接入用户授权提供的数据源
- 负责候选公司线索生成
- 负责输出官网、电话、通用邮箱、LinkedIn 线索、来源链接、来源名称、匹配依据、新鲜度和可信度
- 不负责标准化初筛
- 不负责深度客户背调
- 不负责开发信生成

## 当前默认能力

- 搜索策略生成
- 行业关键词搜客
- 公司级线索发现
- 海关数据、展会名单、协会名单、CRM / Excel 等用户授权数据源归并
- 展会入口定位
- 官网、电话、通用邮箱抓取
- LinkedIn 公司页和可见联系人线索补充
- 候选证据分级与下一步建议
- 将卖方产品、目标客户、排除信号和行业视角原样传入初筛

## 当前不默认承诺

- 默认拥有海关数据账号、付费数据库或企业内部客户资料
- 精准个人邮箱稳定补齐
- 完整人物档案稳定补齐
- 没有公开来源时继续推进下游

## 最小输入输出

- 输入：产品、市场、客户类型、关键词和约束
- 输出：搜索策略、候选客户清单、来源链接、来源名称、匹配依据、新鲜度、可信度、联系人线索、证据等级、下一步动作、整理阶段桥接输入

## 数据源原则

同样的工具，企业自己的数据源越好，跑出来的候选客户就越快、越准。公开搜索只是默认保底；如果用户有更好的海关数据、行业名单、展会资料、老客户库或渠道名单，应优先接入并标清来源。

本 Skill 不默认拥有私有、付费或企业内部数据源，必须由用户提供或授权后使用。海关数据只能作为匹配依据之一，不能直接写成确定采购意向。

## 企业表格与规则沉淀

- 这是候选客户发现能力，不是固定表格模板。
- 企业已有表头优先沿用；没有可用表格时，再按产品、市场和搜索流程新建够用表。
- 用户确认新的搜索来源、数据源接入方式、关键词、排除词、线索分级或表头映射后，先追问：`是否更新到对应 Skill 以便下次自动复用`，授权后再写入 Skill。

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

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
