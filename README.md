# hermes-help 🪐

**Hermes Agent configuration CLI + TUI wizard.**
Schema-aware, always-current, always-correct — knows every config parameter.

[![CI](https://github.com/stephanos8926-lgtm/hermes-help/actions/workflows/ci.yml/badge.svg)](https://github.com/stephanos8926-lgtm/hermes-help/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](pyproject.toml)

---

## Features

### CLI — `hermes-help`

| Command | Description |
|---------|-------------|
| `validate [PATH]` | Validate config.yaml against the full Hermes schema (464 params) |
| `query <KEY>` | Show full docs for any config key with type, enum, range, default |
| `diff [PATH]` | Diff user config vs schema defaults |
| `stub [--section S]` | Generate a config.yaml stub for one or all sections |
| `schema` | Show schema statistics (464 params, 57 top-level sections) |

### TUI — `hermes-help-tui`

- **Live search** — real-time filter of 464 params by path, type, enum, default
- **ParamEditor** — type-aware inline editing (Select for enums, Input for strings, live validation)
- **ExportScreen** — modal with section tree, live YAML preview, copy/write to file
- **Keyboard** — `/` focus search, `E` export, `Esc` cancel

### Hermes Plugin — `rapidwebs-help`

Auto-syncs `compiled_schema.json` after Hermes updates, validates config after changes. Installed at `~/.hermes/plugins/rapidwebs-help/`.

## Quick Start

```bash
# Install
cd ~/Workspaces/hermes-help
uv sync --group dev

# Validate your config
hermes-help validate ~/.hermes/config.yaml

# Query a parameter
hermes-help query terminal.docker_image

# Diff your config against defaults  
hermes-help diff

# Launch the TUI
hermes-help-tui
```

## Documentation

| Document | Description |
|----------|-------------|
| [SPEC.md](docs/SPEC.md) | Technical specification |
| [PLAN.md](docs/PLAN.md) | Implementation plan (HIGH mode) |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guide |
| [SECURITY.md](SECURITY.md) | Security policy |

## Architecture

```
hermes-help/
├── src/hermes_help/
│   ├── cli.py              # Click CLI (validate, query, diff, stub, schema)
│   ├── tui/app.py          # Textual TUI (search, ParamEditor, ExportScreen)
│   ├── tui/widgets/        # ParamEditor widget
│   ├── tui/screens/        # ExportScreen modal
│   ├── schema/             # Static schema, config reader, validator, matcher
│   └── plugin/             # Hermes plugin source (mirrored to ~/.hermes/plugins/)
├── scripts/
│   └── deploy-plugin.sh    # Plugin deploy script
├── tests/                  # 48 tests (schema, config, validation, TUI)
└── docs/                   # Spec, plan, phase deliverables
```

## Schema Coverage

- **464** compiled parameters across **57** top-level sections
- **110+** known enums extracted from Hermes DEFAULT_CONFIG
- **100+** numeric range bounds (terminal.timeout: 1-600, etc.)
- **137** total sections including nested subsections
- Schema version **3** (auto-detects Hermes version at runtime)

## Plugin Deployment

```bash
bash scripts/deploy-plugin.sh
```

Enables the `rapidwebs-help` Hermes plugin for auto schema sync + config validation.

## License

MIT — see [LICENSE](LICENSE)