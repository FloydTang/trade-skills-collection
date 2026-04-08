# 外贸主动开发开源仓库

这个仓库当前只服务一条公开主线，不是泛 Skill 合集：

- `主动开发链路组合包`
- `客户搜索skill`
- `线索整理skill`
- `客户背调skill`
- `开发信skill`

如果你来自线上课：

- 课程里已经讲过全景图、数据资产框架和增强执行逻辑
- 仓库这里不重复讲课
- 仓库只保留最小使用入口、边界和脚本

## 当前推荐安装范围

当前只建议优先使用这 5 项：

- `主动开发链路组合包`
- `客户搜索skill`
- `线索整理skill`
- `客户背调skill`
- `开发信skill`

根目录里看到的其他目录，当前主要用于内部工作间；未发布方向已收进 `工作间/孵化中/`，都不属于默认安装范围。

## 权益入口

- 开源权益：当前 GitHub 仓库
- 增强权益：飞书增强执行词复制入口
- 增强入口：<https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>

## 先看什么

建议按这个顺序：

1. `OPENCLAW.md`
2. `当前推荐安装清单.md`
3. `主动开发链路组合包/README.md`
4. 对应子 skill 的 `README.md`

龙虾 / OpenClaw 直接读取这个仓库时，默认只认上面这些入口文件，不要按根目录枚举全部文件夹后自行推断安装范围。

## Quick Start

先跑最小闭环：

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py
```

先看关键输出：

- `主动开发链路组合包/outputs/demo-run/03-lead-screening-output.md`
- `主动开发链路组合包/outputs/demo-run/05-selected-customer-intel-input.json`
- `主动开发链路组合包/outputs/demo-run/06-customer-intel-report.json`
- `主动开发链路组合包/outputs/demo-run/08-email-draft.md`

如需自检：

```bash
python3 ./主动开发链路组合包/scripts/run_regression_checks.py
```

## 固定边界

当前最稳的定位是：

- 公司级可用
- 人名职位级基本可用
- 精准邮箱级仍不足

固定提醒：

- 没有真实公开来源，不应强行推进下一步
- “skill 已安装” 不等于 “能力已可用”
- 工具依赖要区分已安装、已配置、已登录、已跑通
- LinkedIn 类能力不是默认开箱即用
- 云端和本地环境可能存在差异

## OpenClaw 默认理解

- 默认主入口：`主动开发链路组合包`
- 4 个单节点是阶段能力，不是 4 个平级主入口
- 仓库负责开源说明
- 增强事项直接看飞书入口，不在仓库里继续展开
