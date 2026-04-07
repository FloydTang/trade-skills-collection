# 主动开发最小闭环链路组合包

当前状态：可演示

这个目录用于把以下 4 个已完成节点串成一个最小开源闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

## 当前定位

- 这是当前仓库的默认主入口
- 负责演示 4 个子 skill 如何串起来
- 负责保留中间产物，方便复核和排错
- 不负责重写 4 个子 skill 的内部逻辑

## 当前开源范围

开源版当前提供：

- 固定样例入口
- 最小串联脚本
- 阶段化中间产物
- 可重复运行的 demo 输出
- 4 个子 skill 的开源衔接样板

当前不在仓库中展开：

- 飞书表结构细节
- 统一数据写回协议
- 多代理编排契约
- 给龙虾的增强流程描述词

如需这些增强内容，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>

## 开源权益默认包含什么

- 一个默认主入口
- 一条最小可复现链路
- 一套固定样例
- 一套可直接查看的阶段输出
- 一套最小回归检查

## 当前能力边界

- 当前最稳的是公司级线索主线
- 人名职位级是辅助补全
- 精准邮箱级仍不足
- 没有真实公开来源，不应推进下一步
- 中间产物必须人工复核，不默认自动外发

## 当前目录结构

```text
.
├── README.md
├── SKILL.md
├── examples/
├── outputs/
├── references/
└── scripts/
```

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

- `outputs/demo-run/03-lead-screening-output.md`
- `outputs/demo-run/05-selected-customer-intel-input.json`
- `outputs/demo-run/06-customer-intel-report.json`
- `outputs/demo-run/08-email-draft.md`

## 组合包职责边界

- 负责串联，不负责重写
- 负责保留中间产物，不负责自动发信
- 负责展示最小闭环，不负责在仓库里展开增强落地正文
