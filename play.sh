#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  :
elif [[ -f "${HOME}/.local/bin/env" ]]; then
  # shellcheck source=/dev/null
  source "${HOME}/.local/bin/env"
fi

export DISPLAY="${DISPLAY:-:0}"
export SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR=0

# 云环境 / 无声卡时用 dummy，避免 mixer 初始化失败
if [[ -z "${SDL_AUDIODRIVER:-}" ]]; then
  if ! pactl info >/dev/null 2>&1 && ! pulseaudio --check 2>/dev/null; then
    export SDL_AUDIODRIVER=dummy
  fi
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run python pypvz.py
else
  exec python3 pypvz.py
fi
