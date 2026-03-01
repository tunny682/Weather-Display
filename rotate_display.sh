#!/usr/bin/env bash
set -euo pipefail

# Rotate the desktop (all connected displays) for 8.8" LCD.
# No user input: default is "right" (matches Canterrain working example and many 8.8" panels).
# Override by creating rotate.conf next to this script with ROTATE=normal|right|left|inverted
#
# X11: xrandr --rotate <ROTATE>
# Wayland: wlr-randr --transform (normal|90|270|180)
#
# Boot can be racy: we retry for a while and rotate ALL connected outputs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" && pwd)"
if [[ -f "$SCRIPT_DIR/rotate.conf" ]]; then
  # shellcheck source=/dev/null
  . "$SCRIPT_DIR/rotate.conf"
fi
# Default right so display works without any input (no keyboard on the unit)
ROTATE="${ROTATE:-right}"
MAX_WAIT_SECONDS=60
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Map ROTATE to wlr-randr transform (Wayland)
case "$ROTATE" in
  normal)   WLR_TRANSFORM="normal" ;;
  right)    WLR_TRANSFORM="90" ;;
  left)     WLR_TRANSFORM="270" ;;
  inverted) WLR_TRANSFORM="180" ;;
  *)        WLR_TRANSFORM="normal" ;;
esac

# Give the desktop a moment to be ready
sleep 3

try_wayland() {
  command -v wlr-randr >/dev/null 2>&1 || return 1

  local ok=0
  while IFS= read -r out; do
    [[ -z "$out" ]] && continue
    if wlr-randr --output "$out" --transform "$WLR_TRANSFORM" 2>/dev/null || \
       wlr-randr --output "$out" --transform 0 2>/dev/null; then
      ok=1
    fi
  done < <(wlr-randr 2>/dev/null | awk '
    /^[^ ]/ {o=$1}
    /Enabled: yes/ {print o}
  ' || true)
  [[ $ok -eq 1 ]]
}

try_x11() {
  command -v xrandr >/dev/null 2>&1 || return 1

  xrandr >/dev/null 2>&1 || return 1

  local ok=0
  while IFS= read -r out; do
    [[ -z "$out" ]] && continue
    if xrandr --output "$out" --rotate "$ROTATE" 2>/dev/null; then
      ok=1
    fi
  done < <(xrandr 2>/dev/null | awk '/ connected/ {print $1}' || true)
  [[ $ok -eq 1 ]]
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

echo "Could not rotate desktop (ROTATE=$ROTATE) after ${MAX_WAIT_SECONDS}s."
echo "Try manually: ROTATE=right $0   or   ROTATE=left $0"
exit 1
