#!/usr/bin/env bash
# Install responsive-audit as a skill (Hermes or Claude Code) and fetch the browser it needs.
set -euo pipefail
TARGET="${1:-$HOME/.hermes/skills/design/responsive-audit}"
mkdir -p "$(dirname "$TARGET")"
if [ -d "$TARGET/.git" ]; then git -C "$TARGET" pull --ff-only; else
  git clone https://github.com/lareesahu/responsive-audit.git "$TARGET"; fi
python -m pip install --quiet playwright || pip install --quiet playwright
python -m playwright install chromium
echo "Installed to $TARGET"
echo "Audit something:  python \"$TARGET/scripts/responsive_audit.py\" --url https://example.com --devices iphone"
