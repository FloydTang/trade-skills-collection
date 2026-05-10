# 搜索规则

## 查询策略

公开搜索默认使用三类查询：

1. `product_or_offer + target_market + customer_type`
2. `product_or_offer + target_market + importer/distributor/brand/buyer`
3. `site:linkedin.com/company ...`

## 搜索边界

- 默认只用公开网页结果
- 用户提供或授权数据源后，可合并海关数据导出、展会名单、行业协会名单、企业 CRM / Excel、历史成交数据等
- 不做未授权登录态抓取
- 不承诺完整名单
- 不做大规模爬取
- 不默认拥有私有、付费或企业内部数据

## 结果处理

- 先按 URL 去重
- 再按官网优先、LinkedIn 次之、公司名再次去重
- 搜索节点只做候选发现，不做价值评分
- 每条候选必须保留 `source_type`、`source_name`、`match_basis`、`freshness` 和 `confidence`
- 海关数据只能作为匹配依据之一，不能直接写成确定采购意向
