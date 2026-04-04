# 客户搜索 / 线索发现 Skill for OpenClaw

当前状态：可演示

这个目录提供 OpenClaw-native 的最小包装版本。

定位：

- 输入搜索意图和约束
- 调用核心脚本生成候选名单
- 输出给下游线索整理使用

## Feishu 接入约束

当前这个 OpenClaw 变体如果要接飞书，默认必须挂到同一个主 Base 下运行。

固定要求：

- 先查主 Base，再查 `Lead Workflow Master`
- 搜索结果默认写入同一个 Base 下的 `Lead Discovery Results`
- 不因为搜索阶段单独运行就新建一个新的多维表格
- 后续进入线索整理或其他节点时，继续复用原主记录和原工作容器
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
python3 ./scripts/build_lead_discovery_from_openclaw.py \
  --input-json ./examples/sample-input.json
```

## 作者

半斤九两科技
