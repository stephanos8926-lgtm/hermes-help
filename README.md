# hermes-help 🪐

**Hermes Agent configuration CLI + TUI wizard.**  
Schema-aware, always-current, always-correct configuration helper for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

## Problem

Hermes Agent has **2000+** configuration parameters across 50+ nested YAML sections.  
The official docs are thorough but no tool tells you:
- *"Is my config.yaml valid?"*
- *"What does `terminal.docker_extra_args` actually do?"*
- *"Show me only the params I haven't set yet."*
- *"Which config section was added in v0.17 vs v0.16?"*

## Solution

`hermes-help` solves this with a **dual-mode** tool:

### CLI Mode (`hermes-help`)
- Validate your `~/.hermes/config.yaml` against the live schema
- Query any config key with full documentation
- Diff your config against defaults
- Show version history for config parameters
- Generate minimal/complete config stubs

### TUI Wizard (`hermes-help-tui`)
- Interactive Textual-based browser of ALL config parameters
- Category-divided parameter tree with search/filter
- Live validation as you type values
- Schema-aware input: dropdowns for enums, type-checked fields
- One-click config stub export

## Architecture

```
hermes-help/
├── src/hermes_help/
│   ├── cli.py           # Click CLI
│   ├── tui/app.py       # Textual TUI app
│   ├── schema/
│   │   ├── static.py    # Static config schema from Hermes DEFAULT_CONFIG
│   │   ├── dynamic.py   # Runtime config reader (yours)
│   │   └── validator.py # Validation engine
│   ├── providers/       # Provider/section definitions
│   └── plugin/          # Optional Hermes plugin + hooks
├── tests/
├── docs/
└── pyproject.toml
```

## Quick Start

```bash
# Install
cd ~/Workspaces/hermes-help
uv sync --dev

# CLI: validate your config
hermes-help validate ~/.hermes/config.yaml

# CLI: query a key
hermes-help query terminal.docker_image

# CLI: diff against defaults
hermes-help diff

# TUI wizard
hermes-help-tui
```

## Principles

1. **100% syntactically correct** — every output is valid YAML
2. **Always up-to-date** — static schema auto-regenerated from Hermes source
3. **Always correct** — validation engine checks type, range, enum, nesting
4. **Full coverage** — knows ALL config parameters, not just common ones
5. **Dual awareness** — static schema (what's possible) + dynamic values (what's set)
