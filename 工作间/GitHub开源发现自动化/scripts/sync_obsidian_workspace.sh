#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VAULT_ROOT="/Users/evenbetter/Downloads/半斤九两/Obsidian Vault/工具工作间/02_场景拆解/外贸skill"
MAIN_MAINT_ROOT="$VAULT_ROOT/内部维护/外贸业务主干"
ADDON_MAINT_ROOT="$VAULT_ROOT/内部维护/精选外挂开源"
WIP_ROOT="$VAULT_ROOT/制作中/外贸业务主干"

mkdir -p "$VAULT_ROOT"

copy_file() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "synced: $dst"
}

sync_incubating_skill_docs() {
  local skill="$1"
  local doc
  for doc in README.md 立项方案.md 验收清单.md; do
    if [ -f "$REPO_ROOT/工作间/孵化中/$skill/$doc" ]; then
      copy_file "$REPO_ROOT/工作间/孵化中/$skill/$doc" "$WIP_ROOT/$skill/$doc"
    fi
  done
}

# Rebuild the human-facing Obsidian layer into three buckets:
# root = only cloud sync entrances; 内部维护 = tracking docs; 制作中 = incubating skills.
rm -f "$VAULT_ROOT/开源工具总表.md"
rm -f "$VAULT_ROOT/路线映射.md"
rm -f "$VAULT_ROOT/skill需求池.md"
rm -f "$VAULT_ROOT/作战台开源Skill拆分升级规划_2026-05-18.md"
rm -f "$VAULT_ROOT/作战台开源Skill验证台账_2026-05-18.md"
rm -f "$VAULT_ROOT/作战台与课程中心Skill同步方向_2026-05-19.md"
rm -f "$VAULT_ROOT/优质外挂工具与Skill候选清单_2026-05-19.md"
rm -f "$VAULT_ROOT/外挂工具POC推进清单_2026-05-19.md"
rm -f "$VAULT_ROOT/外挂工具后续推进路线图_2026-05-19.md"
rm -f "$VAULT_ROOT/开始这里.md"
rm -f "$VAULT_ROOT/工具工作间与工具库到课程工作间联动说明_2026-05-20.md"
rm -rf "$VAULT_ROOT/孵化中"
rm -rf "$VAULT_ROOT/竞品监控skill"

copy_file "$REPO_ROOT/工作间/开始这里.md" "$VAULT_ROOT/00_开始这里.md"
copy_file "$REPO_ROOT/工作间/工具工作间与工具库到课程工作间联动说明_2026-05-20.md" "$VAULT_ROOT/工具工作间与工具库到课程工作间联动说明_2026-05-20.md"
copy_file "$REPO_ROOT/工作间/外贸业务主干Skill云端同步清单.md" "$VAULT_ROOT/外贸业务主干Skill云端同步清单.md"
copy_file "$REPO_ROOT/工作间/精选外挂开源Skill云端同步清单.md" "$VAULT_ROOT/精选外挂开源Skill云端同步清单.md"

copy_file "$REPO_ROOT/skill需求池.md" "$MAIN_MAINT_ROOT/skill需求池.md"

if [ -f "$REPO_ROOT/工作间/作战台开源Skill拆分升级规划_2026-05-18.md" ]; then
  copy_file "$REPO_ROOT/工作间/作战台开源Skill拆分升级规划_2026-05-18.md" "$MAIN_MAINT_ROOT/作战台开源Skill拆分升级规划_2026-05-18.md"
fi

if [ -f "$REPO_ROOT/工作间/作战台开源Skill验证台账_2026-05-18.md" ]; then
  copy_file "$REPO_ROOT/工作间/作战台开源Skill验证台账_2026-05-18.md" "$MAIN_MAINT_ROOT/作战台开源Skill验证台账_2026-05-18.md"
fi

if [ -f "$REPO_ROOT/工作间/作战台与课程中心Skill同步方向_2026-05-19.md" ]; then
  copy_file "$REPO_ROOT/工作间/作战台与课程中心Skill同步方向_2026-05-19.md" "$MAIN_MAINT_ROOT/作战台与课程中心Skill同步方向_2026-05-19.md"
fi

if [ -f "$REPO_ROOT/工作间/竞品监控-推进说明.md" ]; then
  copy_file "$REPO_ROOT/工作间/竞品监控-推进说明.md" "$MAIN_MAINT_ROOT/竞品监控-推进说明.md"
fi

if [ -f "$REPO_ROOT/工作间/公开分发与增强承接说明.md" ]; then
  copy_file "$REPO_ROOT/工作间/公开分发与增强承接说明.md" "$MAIN_MAINT_ROOT/公开分发与增强承接说明.md"
fi

if [ -f "$REPO_ROOT/工作间/首次安装与增强入口标准话术.md" ]; then
  copy_file "$REPO_ROOT/工作间/首次安装与增强入口标准话术.md" "$MAIN_MAINT_ROOT/首次安装与增强入口标准话术.md"
fi

copy_file "$REPO_ROOT/工作间/开源工具总表.md" "$ADDON_MAINT_ROOT/开源工具总表.md"
copy_file "$REPO_ROOT/工作间/路线映射.md" "$ADDON_MAINT_ROOT/路线映射.md"

if [ -f "$REPO_ROOT/工作间/优质外挂工具与Skill候选清单_2026-05-19.md" ]; then
  copy_file "$REPO_ROOT/工作间/优质外挂工具与Skill候选清单_2026-05-19.md" "$ADDON_MAINT_ROOT/优质外挂工具与Skill候选清单_2026-05-19.md"
fi

if [ -f "$REPO_ROOT/工作间/外挂工具POC推进清单_2026-05-19.md" ]; then
  copy_file "$REPO_ROOT/工作间/外挂工具POC推进清单_2026-05-19.md" "$ADDON_MAINT_ROOT/外挂工具POC推进清单_2026-05-19.md"
fi

if [ -f "$REPO_ROOT/工作间/外挂工具后续推进路线图_2026-05-19.md" ]; then
  copy_file "$REPO_ROOT/工作间/外挂工具后续推进路线图_2026-05-19.md" "$ADDON_MAINT_ROOT/外挂工具后续推进路线图_2026-05-19.md"
fi

if [ -f "$REPO_ROOT/工作间/外挂Skill晋升通道与论坛同步流程_2026-05-19.md" ]; then
  copy_file "$REPO_ROOT/工作间/外挂Skill晋升通道与论坛同步流程_2026-05-19.md" "$ADDON_MAINT_ROOT/外挂Skill晋升通道与论坛同步流程_2026-05-19.md"
fi

sync_incubating_skill_docs "trade-mail-group"
sync_incubating_skill_docs "trade-social-account-scan"
sync_incubating_skill_docs "trade-feishu-kb"
sync_incubating_skill_docs "trade-market-pulse"
sync_incubating_skill_docs "竞品监控skill"
sync_incubating_skill_docs "客户管理skill"
sync_incubating_skill_docs "展会线索筛选skill"
sync_incubating_skill_docs "跟进优先级skill"

rm -f "$VAULT_ROOT/总说明.md"
rm -rf "$VAULT_ROOT/外贸主动开发链路4合一"

echo "Obsidian workspace sync complete: $VAULT_ROOT"
