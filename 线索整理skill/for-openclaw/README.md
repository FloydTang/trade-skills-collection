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

## Feishu 接入约束

当前这个 OpenClaw 变体如果要接飞书，默认必须复用同一个主 Base 和主表。

固定要求：

- 先查主 Base，再查 `Lead Workflow Master`
- 结果写入同一个 Base 下的 `Lead Screening Results`
- 同一 lead 优先更新原主记录，不新建平行 lead
- 如果 `recommended_next_action` 不是 `enter_customer_intel`，不自动创建客户背调文档
- 当前角色固定为 `stage_worker`
- `feishu_container_creation = forbidden`

推荐先读：

- `../../主动开发链路组合包/references/OpenClaw执行规范.md`
- `../../主动开发链路组合包/references/OpenClaw首跑检查清单.md`

补充一句固定口径：

- 这个目录是当前单节点的 OpenClaw 运行时变体，不是新的安装归口
- 飞书增强入口只认仓库根目录的 `README.md`、`OPENCLAW.md`、`当前推荐安装清单.md`

## 快速运行

```bash
python3 ./scripts/build_lead_screening_from_openclaw.py \
  --input-json ./examples/sample-input.json
```

## 作者

半斤九两科技
