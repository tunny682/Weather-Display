#!/usr/bin/env bash
set -euo pipefail

# Rotate the desktop (all connected displays) to landscape for 8.8" LCD.
# Supports:
#   - Wayland: wlr-randr (transform normal)
#   - X11:     xrandr --rotate normal on every connected output
#
# Boot can be racy: X/Wayland may not be ready when systemd runs this,
# so we retry for a while. We rotate ALL connected outputs so the whole
# desktop is in landscape.

MAX_WAIT_SECONDS=60
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Give the desktop a moment to be ready before first attempt
sleep 3

try_wayland() {
  command -v wlr-randr >/dev/null 2>&1 || return 1

  # Get all enabled outputs and rotate each to landscape
  local ok=0
  while IFS= read -r out; do
    [[ -z "$out" ]] && continue
    if wlr-randr --output "$out" --transform normal 2>/dev/null || \
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

  # Rotate every connected output so the whole desktop is landscape
  local ok=0
  while IFS= read -r out; do
    [[ -z "$out" ]] && continue
    if xrandr --output "$out" --rotate normal 2>/dev/null; then
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

echo "Could not rotate desktop to landscape after ${MAX_WAIT_SECONDS}s."
exit 1
