#!/bin/bash
# plug-and-play installer for fastsh + fastallow + laya daemon. Idempotent.
# Usage: ./setup.sh [--no-daemon]
set -u
REPO="$(cd "$(dirname "$0")" && pwd)"
OCFG="$HOME/.config/opencode/opencode.jsonc"
PLUGDIR="$HOME/.config/opencode/plugins"
LAYA_VENV="${LAYA_VENV:-/home/uzu/code/infra/laya/.venv/lib/python3.14/site-packages}"
LAYA_MODEL="${LAYA_MODEL:-/home/uzu/code/infra/laya/laya-cli-best}"
SOCK="${LAYA_SOCK:-/tmp/laya-gate.sock}"

fail() { echo "SETUP FAIL: $1" >&2; exit 1; }
command -v python3 >/dev/null || fail "python3 missing"
[ -f "$LAYA_VENV/laya/__init__.py" ] || fail "laya package not at $LAYA_VENV (set LAYA_VENV)"
[ -f "$LAYA_MODEL/rl_agent_config.json" ] || fail "model not at $LAYA_MODEL (set LAYA_MODEL)"
[ -f "$OCFG" ] || fail "opencode config not found at $OCFG"

cp "$OCFG" "$OCFG.fastsh-bak" 2>/dev/null
if ! grep -q '"fastsh"' "$OCFG"; then
  python3 - "$OCFG" "$REPO" <<'EOF'
import sys
p, repo = sys.argv[1], sys.argv[2]
s = open(p).read()
block = ('      "fastsh": {\n        "type": "local",\n'
         f'        "command": ["python3", "{repo}/mcp_fastsh.py"],\n        "enabled": true\n      },\n')
anchor = '      "codegraph": {'
assert anchor in s, "codegraph anchor missing"
open(p, 'w').write(s.replace(anchor, block + anchor, 1))
print("mcp block added")
EOF
else echo "mcp block present, skipping"; fi

PKG="$HOME/.config/opencode/node_modules/@opencode/plugin/dist/promise/index.js"
[ -f "$PKG" ] || fail "opencode plugin package missing"
mkdir -p "$PLUGDIR"
sed -e "s|__GATE__|$REPO/fastgate.py|" -e "s|__PLUGIN_PKG__|$PKG|" \
  "$REPO/plugin/fastallow.ts" > "$PLUGDIR/fastallow.ts"
echo "plugin installed"

if [ "${1:-}" != "--no-daemon" ]; then
  if [ -S "$SOCK" ] && systemctl --user is-active -q laya-daemon.service 2>/dev/null; then
    echo "daemon already up ($SOCK)"
  else
    sed -e "s|/home/uzu|$HOME|g" "$REPO/laya-daemon.service" > "$HOME/.config/systemd/user/laya-daemon.service"
    systemctl --user daemon-reload
    systemctl --user enable --now laya-daemon.service
    echo "daemon enabled (starts on login)"
  fi
fi
python3 "$REPO/q" --selfcheck && echo "SETUP OK: restart OpenCode session to pick up fastsh"
