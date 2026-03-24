# 线索整理 / 初筛 Skill for OpenClaw

当前状态：可演示

这个目录提供 OpenClaw-native 的最小包装版本。

定位：

- 假设搜索阶段已经由上游工作流完成
- 输入是一包候选线索 JSON
- 输出是可直接进入人工复核或客户背调的结构化结果

当前最小能力：

- 接收 `lead_candidates` 数组
- 转换成本地版标准输入
- 调用核心脚本生成初筛结果

## 快速运行

```bash
python3 ./scripts/build_lead_screening_from_openclaw.py \
  --input-json ./examples/sample-input.json
```

## 作者

半斤九两科技
