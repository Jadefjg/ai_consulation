#!/bin/bash
# 打开微信开发者工具并导入当前小程序产物。
# HBuilderX 自动拉起会用另一套 userData 目录；若 Default/.cli 不存在就会 ENOENT。
set -euo pipefail

APP="/Applications/wechatwebdevtools.app"
CLI="$APP/Contents/MacOS/cli"
SUPPORT="${HOME}/Library/Application Support/微信开发者工具"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:-}"

if [[ ! -x "$CLI" ]]; then
  echo "未找到微信开发者工具：$CLI" >&2
  exit 1
fi

if [[ -z "$PROJECT" ]]; then
  if [[ -d "$ROOT/dist/dev/mp-weixin" ]]; then
    PROJECT="$ROOT/dist/dev/mp-weixin"
  elif [[ -d "$ROOT/dist/build/mp-weixin" ]]; then
    PROJECT="$ROOT/dist/build/mp-weixin"
  else
    echo "没有编译产物。请先运行：npm run dev:mp-weixin" >&2
    exit 1
  fi
fi

if [[ ! -f "$PROJECT/app.json" ]]; then
  echo "不是有效的小程序目录：$PROJECT" >&2
  exit 1
fi

mkdir -p "$SUPPORT"

# CLI initialize 会往 {hash}/Default/.cli 写端口；目录必须先存在。
# 图形界面和 CLI 的 hash 不同，把已开启服务端口的状态文件同步过去。
SOURCE_DEFAULT=""
for candidate in "$SUPPORT"/*/Default; do
  if [[ -f "$candidate/.ide-status" ]] && [[ "$(tr -d '[:space:]' < "$candidate/.ide-status")" == "On" ]]; then
    SOURCE_DEFAULT="$candidate"
    break
  fi
done

ensure_cli_dir() {
  local dest="$1"
  mkdir -p "$dest"
  if [[ -n "$SOURCE_DEFAULT" ]]; then
    [[ -f "$dest/.ide-status" ]] || cp -f "$SOURCE_DEFAULT/.ide-status" "$dest/.ide-status"
    [[ -f "$dest/.ide" ]] || cp -f "$SOURCE_DEFAULT/.ide" "$dest/.ide" 2>/dev/null || true
    [[ -f "$dest/.cli" ]] || cp -f "$SOURCE_DEFAULT/.cli" "$dest/.cli" 2>/dev/null || true
  else
    printf 'On' > "$dest/.ide-status"
  fi
}

# HBuilderX 实际用的目录（与 GUI 的 productHash 不同）
ensure_cli_dir "$SUPPORT/d1e8765721a6c23d43b14c95b1843e6b/Default"
if [[ -n "$SOURCE_DEFAULT" ]]; then
  ensure_cli_dir "$SOURCE_DEFAULT"
fi
# 其余已存在的 hash 目录也补 Default，避免再次 ENOENT
shopt -s nullglob
for hashdir in "$SUPPORT"/*/; do
  if [[ -d "$hashdir" ]]; then
    ensure_cli_dir "${hashdir}Default"
  fi
done
shopt -u nullglob

echo "打开微信开发者工具：$PROJECT"
echo "若仍失败：开发者工具 → 设置 → 安全设置 → 开启服务端口，然后完全退出再打开工具。"
"$CLI" open --project "$PROJECT"
