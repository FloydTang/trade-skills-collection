#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULT_ROOT="/Users/evenbetter/Downloads/半斤九两/Obsidian Vault/工具工作间/外贸skill"

mkdir -p "$VAULT_ROOT"

copy_file() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "synced: $dst"
}

copy_file "$REPO_ROOT/工作间/开源工具总表.md" "$VAULT_ROOT/开源工具总表.md"
copy_file "$REPO_ROOT/工作间/路线映射.md" "$VAULT_ROOT/路线映射.md"
copy_file "$REPO_ROOT/skill需求池.md" "$VAULT_ROOT/skill需求池.md"
copy_file "$REPO_ROOT/工作间/开始这里.md" "$VAULT_ROOT/开始这里.md"

if [ -f "$REPO_ROOT/工作间/竞品监控-推进说明.md" ]; then
  copy_file "$REPO_ROOT/工作间/竞品监控-推进说明.md" "$VAULT_ROOT/竞品监控skill/推进说明.md"
fi

rm -f "$VAULT_ROOT/总说明.md"
rm -rf "$VAULT_ROOT/外贸主动开发链路4合一"

echo "Obsidian workspace sync complete: $VAULT_ROOT"
