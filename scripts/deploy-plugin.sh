#!/bin/bash
# deploy-plugin.sh — Sync the rapidwebs-help Hermes plugin from the project
# Run from project root: bash scripts/deploy-plugin.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="$HOME/.hermes/plugins/rapidwebs-help"

echo "→ Deploying rapidwebs-help plugin..."

# Create plugin directory
mkdir -p "$PLUGIN_DIR"

# Copy plugin files
cp "$PROJECT_DIR/src/hermes_help/plugin/__init__.py" "$PLUGIN_DIR/__init__.py" 2>/dev/null || \
    echo "  ⚠ No plugin/__init__.py in project — using installed"
cp "$PROJECT_DIR/src/hermes_help/plugin/plugin.yaml" "$PLUGIN_DIR/plugin.yaml" 2>/dev/null || \
    echo "  ⚠ No plugin/plugin.yaml in project — using installed"

# Also copy the compiled schema for offline use
cp "$PROJECT_DIR/src/hermes_help/compiled_schema.json" \
   "$PLUGIN_DIR/compiled_schema.json" 2>/dev/null || true

# Set restrictive permissions
chmod 700 "$PLUGIN_DIR/__init__.py" 2>/dev/null || true

# Enable in Hermes config
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
plugins = c.setdefault('plugins', {})
enabled = plugins.setdefault('enabled', [])
if 'rapidwebs-help' not in enabled:
    enabled.append('rapidwebs-help')
    with open('$HOME/.hermes/config.yaml', 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print('  ✓ Added to plugins.enabled')
else:
    print('  ✓ Already enabled')
"

echo "→ Plugin deployed to $PLUGIN_DIR"
echo "→ Restart Hermes or start a new session to activate"
