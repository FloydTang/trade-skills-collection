# 客户搜索 / 线索发现 Skill for OpenClaw

当前状态：可演示

这个目录提供 OpenClaw-native 的最小包装版本。

定位：

- 输入搜索意图和约束
- 调用核心脚本生成候选名单
- 输出给下游线索整理使用

补充固定口径：

- 这个目录是当前单节点的 OpenClaw 运行时变体，不是新的安装归口
- 增强权益不在仓库中展开正文
- 如需飞书落地、统一编排或多代理协作，请查看飞书文档入口

## 快速运行

```bash
python3 ./scripts/build_lead_discovery_from_openclaw.py \
  --input-json ./examples/sample-input.json
```

## 作者

半斤九两科技
