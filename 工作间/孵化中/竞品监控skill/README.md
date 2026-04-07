# 竞品监控 Skill

当前状态：开发中

这个目录用于把“竞品官网、价格、上新和重点页面变化”整理成适合人工复核与业务讨论的变化汇总。

## 人话解释

如果不用技术词，这个 Skill 现在做的事情可以理解成三步：

1. 先挑 3 个最值得盯的竞品页面
2. 让 `changedetection.io` 帮我们盯着这些页面有没有变
3. 页面一变，我们再把变化翻译成“发生了什么、可能意味着什么、要不要人工去看”

你可以把它想成：

- `changedetection.io` 是“盯网页的人”
- 我们现在写的脚本，是“把网页变化翻译成人话的人”

所以我前面说的这些词，实际对应的是：

- `watch`
  就是“盯住一个页面”
- `watch seed`
  就是“先把这 3 个页面的盯法写成一份统一清单”
- `selector`
  就是“在一个网页里，到底只看哪一块内容”
- `summary script`
  就是“把变化整理成摘要的脚本”

## 现在做到哪一步了

目前已经做完的是：

- 选好了 3 个真实页面
- 定好了每个页面该看哪些高价值字段
- 做好了最小变化摘要脚本
- 做好了建 watch 用的种子配置
- 做好了最小样例输入和输出

目前还没做完的是：

- 还没在真实 `changedetection.io` 环境里把这 3 个 watch 全部验证一遍
- 还没把每个页面稳定可用的页面区域选择规则彻底确认下来

## 当前文档归属

为了避免后续线程继续按旧规则推进，这个方向现在固定按下面的方式落文档：

- 执行层文件、脚本、样例、运行输入输出：留在当前仓库
- 长期判断与人类阅读说明：沉淀到 `工作间/`
- 需要长期展示给课程、品牌、产品表达使用的说明：在 Obsidian `工具工作间/外贸skill` 有对应展现

当前对应的长期说明页是：

- `工作间/竞品监控-推进说明.md`

换句话说：

现在已经不是“空想阶段”了，已经有能跑的最小链路；
但还没有到“真实监控已经长期稳定”的阶段。

## 你现在最需要知道的结论

这轮工作的目标不是做一个复杂平台，而是先证明这件事能不能用最小方式跑通。

只要后面在真实 watch 里再确认一次：

- 页面能抓到
- 重点字段能看到
- 变化能被翻译成业务摘要

那这个 `竞品监控 Skill` 的首版就算真正立住了。

定位：

- 持续监控竞品官网、价格、上新和动态
- 输出适合人工复核和业务讨论的变化汇总

当前首版不从零重写监控底层，默认采用：

- `changedetection.io` 负责上游网页变化监控
- `竞品监控 Skill` 负责输入规范、关注字段说明、变化摘要输出、人工复核口径

## 当前首版演示对象

当前首版先锁定同一竞品的 3 个真实公开页面，优先把链路跑通：

1. 产品详情页：`https://www.allbirds.com/products/mens-tree-runners`
2. 新品集合页：`https://www.allbirds.com/collections/mens-new-arrivals`
3. 首页促销区：`https://www.allbirds.com/`

这样做的原因只有三个：

- 页面类型刚好覆盖首版最重要的 3 类监控对象
- 字段口径统一，便于讲清“为什么值得看”
- 后续替换成别的行业竞品时，只需要换输入，不需要重写脚本

## 当前建议阅读顺序

1. `立项方案.md`
2. `SKILL.md`
3. `references/首版接入方案.md`
4. `examples/minimal-monitoring-input.json`
5. `examples/sample-change-events.json`
6. `scripts/build_change_summary.py`
7. `scripts/build_watch_seed.py`
8. `examples/changedetection-watch-seed.json`
9. `references/changedetection-watch-落地口径.md`
10. `examples/minimal-monitoring-output.md`
11. `examples/minimal-monitoring-output.json`

## 首版范围

- 只监控少量竞品 URL
- 只关注价格、产品标题、上新、促销文案、核心 CTA 等可解释字段
- 只输出 Markdown / JSON 摘要
- 默认保留人工复核，不直接自动通知客户或自动改价

## 最小脚本入口

```bash
python3 '工作间/孵化中/竞品监控skill/scripts/build_change_summary.py' \
  --input-json '工作间/孵化中/竞品监控skill/examples/sample-change-events.json' \
  --markdown-out '工作间/孵化中/竞品监控skill/examples/minimal-monitoring-output.md' \
  --json-out '工作间/孵化中/竞品监控skill/examples/minimal-monitoring-output.json'
```

输入既可以是少量真实页面变化结果，也可以是当前仓库里的模拟变化样例。

## Watch 种子生成

```bash
python3 '工作间/孵化中/竞品监控skill/scripts/build_watch_seed.py' \
  --input-json '工作间/孵化中/竞品监控skill/examples/minimal-monitoring-input.json' \
  --json-out '工作间/孵化中/竞品监控skill/examples/changedetection-watch-seed.json'
```

这个输出不是伪装成“已验证选择器”的 API 成品，而是首版建 watch 时的统一种子配置。

## 当前不做

- 不先做大规模多站点部署
- 不先做复杂权限、账号体系或 SaaS 化界面
- 不先做完整历史数据库分析
- 不把 changedetection.io 重写成我们自己的底层系统
