#!/bin/bash
# deploy.sh — Install the hermes-help Hermes plugin
#
# Two deployment methods:
#
# 1. From GitHub (recommended for users):
#    hermes plugins install https://github.com/stephanos8926-lgtm/hermes-help
#
# 2. From local source (for development):
#    bash deploy.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$HOME/.hermes/plugins/hermes-help"

echo "→ Deploying hermes-help plugin..."

# Create plugin directory
mkdir -p "$PLUGIN_DIR"

# Copy plugin files
cp "$PROJECT_DIR/plugin/plugin.yaml" "$PLUGIN_DIR/plugin.yaml"
cp "$PROJECT_DIR/plugin/__init__.py" "$PLUGIN_DIR/__init__.py"

# Copy compiled schema for offline use
if [ -f "$PROJECT_DIR/src/hermes_help/compiled_schema.json" ]; then
    cp "$PROJECT_DIR/src/hermes_help/compiled_schema.json" \
       "$PLUGIN_DIR/compiled_schema.json"
fi

# Restrictive permissions
chmod 700 "$PLUGIN_DIR/__init__.py"
chmod 700 "$PLUGIN_DIR/plugin.yaml"

# Enable in Hermes config
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
plugins = c.setdefault('plugins', {})
enabled = plugins.setdefault('enabled', [])
if 'hermes-help' not in enabled:
    enabled.append('hermes-help')
    with open('$HOME/.hermes/config.yaml', 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print('  ✓ Enabled in plugins.enabled')
else:
    print('  ✓ Already enabled')
"

echo "→ Plugin deployed to $PLUGIN_DIR"
echo "→ Start a new Hermes session to activate"
