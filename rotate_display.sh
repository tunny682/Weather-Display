#!/usr/bin/env bash
set -euo pipefail

# Rotate the active display to landscape (normal orientation) for 8.8" LCD.
# Supports:
#   - Wayland: wlr-randr (transform normal)
#   - X11:     xrandr --rotate normal
#
# Boot can be racy: X/Wayland may not be ready when systemd runs this,
# so we retry for a while (same approach as Canterrain/weather-display).

MAX_WAIT_SECONDS=60

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

try_wayland() {
  command -v wlr-randr >/dev/null 2>&1 || return 1

  local out=""
  out="$(wlr-randr 2>/dev/null | awk '
    /^[^ ]/ {o=$1}
    /Enabled: yes/ {print o; exit}
  ' || true)"

  [[ -n "$out" ]] || return 1

  # Landscape: no rotation (normal; some versions use 0)
  wlr-randr --output "$out" --transform normal >/dev/null 2>&1 || \
  wlr-randr --output "$out" --transform 0 >/dev/null 2>&1
}

try_x11() {
  command -v xrandr >/dev/null 2>&1 || return 1

  xrandr >/dev/null 2>&1 || return 1

  local out=""
  out="$(xrandr 2>/dev/null | awk '/ connected/ {print $1; exit}' || true)"
  [[ -n "$out" ]] || return 1

  xrandr --output "$out" --rotate normal >/dev/null 2>&1
}

for ((i=1; i<=MAX_WAIT_SECONDS; i++)); do
  if try_wayland; then
    exit 0
  fi
  if try_x11; then
    exit 0
  fi
  sleep 1
done

echo "Could not rotate display to landscape after ${MAX_WAIT_SECONDS}s."
exit 1
