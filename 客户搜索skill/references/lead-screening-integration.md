# 与线索整理 Skill 的衔接说明

这个 Skill 的输出不是最终线索池，而是候选发现结果。

## 推荐流程

1. 先运行客户搜索 / 线索发现 Skill
2. 将候选名单桥接成 `线索整理skill/` 输入
3. 用线索整理 Skill 做字段统一、缺失提示和初筛
4. 再进入客户背调

## 默认桥接字段

- `company_name`
- `company_website`
- `person_name`
- `email`
- `country_or_market`
- `source_url`
- `linkedin_url`
- `notes`
- `source_type`

## 设计原则

- 搜索节点只产出保守候选，不提前判断客户价值
- 联系人线索只写“可见联系人线索”，不强行判定职位真实性
