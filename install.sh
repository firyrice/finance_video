#!/usr/bin/env bash
#
# 把 bilibili-finance-video 技能安装到 Claude Code 和 Codex。
#
# 默认用软链接（symlink）方式：技能目录留在本仓库，两个工具的 skills 目录各建一个
# 指向它的链接。这样 git pull 更新后两个工具都自动生效，无需重装。
#
# 用法:
#   ./install.sh              # 软链接到 Claude Code + Codex（推荐）
#   ./install.sh --copy       # 改为复制（不建链接，适合不想依赖仓库常驻的场景）
#   ./install.sh --claude     # 只装 Claude Code
#   ./install.sh --codex      # 只装 Codex
#
set -euo pipefail

SKILL_NAME="bilibili-finance-video"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="link"          # link | copy
DO_CLAUDE=1
DO_CODEX=1
EXPLICIT_TARGET=0

for arg in "$@"; do
  case "$arg" in
    --copy)   MODE="copy" ;;
    --link)   MODE="link" ;;
    --claude) DO_CLAUDE=1; [ "$EXPLICIT_TARGET" -eq 0 ] && DO_CODEX=0; EXPLICIT_TARGET=1 ;;
    --codex)  DO_CODEX=1;  [ "$EXPLICIT_TARGET" -eq 0 ] && DO_CLAUDE=0; EXPLICIT_TARGET=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "未知参数: $arg（用 --help 看用法）" >&2; exit 1 ;;
  esac
done

install_to() {
  local base="$1"          # 如 ~/.claude 或 ~/.codex
  local label="$2"
  local skills_dir="$base/skills"
  local dest="$skills_dir/$SKILL_NAME"

  mkdir -p "$skills_dir"

  # 已存在则先清掉（软链接/旧目录都清），避免重复嵌套
  if [ -L "$dest" ] || [ -e "$dest" ]; then
    rm -rf "$dest"
  fi

  if [ "$MODE" = "link" ]; then
    ln -s "$SRC_DIR" "$dest"
    echo "[$label] 已软链接: $dest -> $SRC_DIR"
  else
    cp -R "$SRC_DIR" "$dest"
    # 复制模式下别把 .git 带过去
    rm -rf "$dest/.git"
    echo "[$label] 已复制到: $dest"
  fi
}

echo "安装源: $SRC_DIR"
echo "模式: $MODE"
echo

[ "$DO_CLAUDE" -eq 1 ] && install_to "$HOME/.claude" "Claude Code"
[ "$DO_CODEX"  -eq 1 ] && install_to "$HOME/.codex"  "Codex"

echo
echo "完成。重启 Claude Code / Codex 后，输入股票名即可触发本技能。"
echo "可选：安装脚本依赖 ->  pip install -r \"$SRC_DIR/requirements.txt\""
