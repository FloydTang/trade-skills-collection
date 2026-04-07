# Trade Customer Intel

中英双语的开源 Codex Skill，用公开网页线索为外贸销售和客户开发生成结构化客户情报报告。

## 这个 Skill 解决什么问题

- 只有公司名、联系人、邮箱或官网
- 公开信息分散、真假难辨
- 开发前需要先做保守的公司级背调

## 职责边界

- 负责公开网页证据收集
- 负责实体匹配、风险判断和报告生成
- 负责公司级背调主线
- 联系人和职位只作辅助匹配
- 不负责批量搜客户入口
- 不负责替代人工直接外发邮件

## 当前默认能力

- 公司级主体核验
- 官网、社媒、公开网页证据整理
- 双语结构化报告
- 保守的风险评级
- 基于证据的销售切入点建议

## 当前不默认承诺

- 精准个人邮箱稳定补齐
- 完整人物档案稳定补齐
- 完全自动化个性化触达
- 弱证据下强行生成个性化事实

## 输入输出

输入：

- 公司名
- 联系人名
- 邮箱
- 官网
- 市场信息

输出：

- 执行摘要
- 身份快照
- 公司画像
- 数字足迹
- 销售切入角度
- 风险评级
- 证据清单

## 依赖提醒

- 只用公开网络信息
- `已安装` 不等于 `已可用`
- 搜索工具要区分 `已安装`、`已配置`、`已跑通`
- LinkedIn 类能力不是默认开箱即用
- 云端和本地环境可能不同

## Quick Start

```bash
python3 ./scripts/build_customer_intel_report.py \
  --input-json ./examples/sample-input.json \
  --markdown-out /tmp/customer-intel.md \
  --json-out /tmp/customer-intel.json
```

## 增强权益入口

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
