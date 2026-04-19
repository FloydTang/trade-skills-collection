# 主动开发最小闭环链路组合包

当前状态：可演示

这个目录是默认主入口，用来把以下 4 个已完成节点串成一个最小开源闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

当前默认按两种模式理解：

- `课堂稳定模式`：固定样例、固定桥接、稳定演示
- `真实业务模式`：真实输入，结果受公开数据质量和关键词配置影响

## 当前开源范围

开源版当前提供：

- 固定样例入口
- 最小串联脚本
- 阶段化中间产物
- 可重复运行的 demo 输出
- 4 个子 skill 的开源衔接样板

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
- 中间产物必须人工复核，不默认自动外发

## 数据容器方案

- 保底容器：`JSON / Markdown / CSV`
- 课堂标准沙盘：`Feishu Sandbox Adapter`
- 企业真实容器：`CRM / ERP / 邮箱草稿箱`，当前只留扩展位

## Quick Start

运行最小 demo：

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
- 负责最小闭环，不负责自动发信
- 负责开源演示，不负责在仓库里展开增强正文
- 负责输出中立容器 bundle，不把飞书写死成唯一容器
