# hermes-help — Technical Specification

> **Version:** 1.0.0  
> **Date:** 2026-07-01  
> **Author:** Lucien (RapidWebs Enterprise)  
> **Mode:** HIGH (security-critical, public-facing tool)

---

## 1. Problem Statement

Hermes Agent has **2,000+** configuration parameters across **50+** nested YAML sections
(agent, terminal, compression, display, tts, stt, voice, memory, delegation,
goals, moa, skills, curator, cron, kanban, approvals, security, browser,
checkpoints, web, plugins, hooks, streaming, sessions, gateway, dashboard,
privacy, logging, network, openrouter, bedrock, auxiliary, and 30+ more).

Users face these problems:

| Problem | Impact |
|---------|--------|
| No single tool knows ALL config params | Manual guessing, YAML errors |
| Config docs go stale between Hermes releases | Wrong advice, silent failures |
| No validation against schema | Runtime errors from bad config |
| No diff tool for "what changed?" | Can't track config drift |
| No TUI to browse 2000+ params | Overwhelming flat docs |

## 2. Solution

**hermes-help** — a dual-mode (CLI + TUI) tool with:

- **Static schema** — extracted from Hermes' `DEFAULT_CONFIG` (the single source of truth)
- **Dynamic introspection** — reads running `~/.hermes/config.yaml` at runtime
- **Validation engine** — type checks, range checks, enum checks, nesting checks
- **Hermes plugin** — auto-regenerates schema when Hermes updates
- **Shell hooks** — auto-validate config on `hermes config set`

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      hermes-help                             │
├──────────────┬──────────────────────┬───────────────────────┤
│   CLI Mode    │      TUI Mode        │   Plugin + Hooks      │
│  (click)     │     (Textual)        │   (Hermes extensions) │
├──────────────┼──────────────────────┼───────────────────────┤
│  validate    │  category browser    │  post-update hook     │
│  query       │  search/filter       │  config validate hook │
│  diff        │  type-aware editor   │  schema sync          │
│  stub        │  export wizard       │                       │
│  doc         │  live preview        │                       │
└──────┴──────┴───────────┴───────────┴───────────┴───────────┘
                │                          │
         ┌──────┴──────┐          ┌────────┴────────┐
         │ Static Schema │          │ Dynamic Reader  │
         │ (from source) │          │ (from config)   │
         └──────┬───────┘          └────────┬────────┘
                └──────────┬───────────────┘
                     ┌─────┴─────┐
                     │ Validator │
                     └───────────┘
```

### 3.1 File Tree

```
src/hermes_help/
├── __init__.py              # Package metadata, version
├── __main__.py              # `python -m hermes_help`
├── cli.py                   # Click CLI (validate, query, diff, stub, doc)
├── config.py                # Config paths, constants, helper utils
│
├── schema/
│   ├── __init__.py
│   ├── static.py            # Static schema extractor from DEFAULT_CONFIG
│   ├── dynamic.py           # Runtime config reader
│   ├── matcher.py           # Schema-to-config matching engine
│   └── validator.py         # Validation engine
│
├── providers/
│   ├── __init__.py
│   ├── base.py              # Base provider model
│   └── registry.py          # Provider definition registry
│
├── tui/
│   ├── __init__.py
│   ├── app.py               # Textual App (TUI entry point)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main_screen.py   # Main browser screen
│   │   ├── detail_screen.py # Key detail + edit screen
│   │   └── export_screen.py # Config export screen
│   └── widgets/
│       ├── __init__.py
│       ├── param_tree.py    # Category tree widget
│       ├── param_detail.py  # Parameter detail panel
│       ├── search_bar.py    # Search/filter bar
│       └── value_input.py   # Type-aware value input
│
├── plugin/
│   ├── __init__.py
│   ├── schema_sync.py       # Post-update schema sync logic
│   └── plugin.yaml          # Hermes plugin manifest
│
└── hooks/
    ├── validate-config.sh    # Shell hook: validate after config set
    └── schema-post-update.sh # Shell hook: regenerate after update

tests/
├── test_static.py            # Schema extraction tests
├── test_dynamic.py           # Config reader tests
├── test_validator.py         # Validation engine tests
├── test_cli.py               # CLI command tests
├── conftest.py               # Shared fixtures

docs/
├── SPEC.md                   # This document
├── ADR-001-schema-extraction.md
└── CONFIG_REFERENCE.md       # Auto-generated config reference
```

### 3.2 Data Flow

```
1. STATIC SCHEMA EXTRACTION
   Hermes source (config.py) ──▶ hermes-help schema/static.py
                                      │
                              DEFAULT_CONFIG dict
                                      │
                              ┌───────┴────────┐
                              │ SchemaCompiler  │
                              │                 │
                              │ For each key:   │
                              │  - type         │
                              │  - default      │
                              │  - description  │
                              │  - enum values  │
                              │  - nested path  │
                              │  - min/max      │
                              │  - version_added│
                              └───────┬────────┘
                                      ▼
                             compiled_schema.json
                           (committed to repo, updated via plugin)

2. DYNAMIC CONFIG READING
   ~/.hermes/config.yaml ──▶ schema/dynamic.py
                                      │
                              ┌───────┴────────┐
                              │ ConfigReader    │
                              │  - loads YAML   │
                              │  - flattens     │
                              │  - masks secrets│
                              └───────┬────────┘
                                      ▼
                             flat_param_map: dict

3. VALIDATION
   flat_param_map + compiled_schema ──▶ schema/validator.py
                                      │
                              ┌───────┴────────┐
                              │ Validator       │
                              │  - type check   │
                              │  - range check  │
                              │  - enum check   │
                              │  - nesting      │
                              │  - unknown keys │
                              │  - missing keys │
                              └───────┬────────┘
                                      ▼
                         ValidationResult
                         (errors, warnings, infos)
```

## 4. Core Components

### 4.1 Static Schema Extractor (`schema/static.py`)

The heart of hermes-help. Extracts a typed, hierarchical schema from the
`DEFAULT_CONFIG` dictionary (from Hermes' `hermes_cli/config.py`).

**How it works:**
1. Imports `DEFAULT_CONFIG` from the installed Hermes package
2. Walks the nested dict recursively
3. At each leaf (non-dict value), infers:
   - Python type (str, int, float, bool, list, dict)
   - Default value
   - Path as dot-separated key (e.g., `terminal.docker_image`)
   - Enum membership (for known constrained values)
   - Range bounds (for numeric values with known constraints)
4. At each branch (dict value), creates a category node with children
5. Writes to `compiled_schema.json` for fast loading without Hermes import

**Example output:**
```json
{
  "terminal": {
    "path": "terminal",
    "type": "section",
    "children": ["terminal.backend", "terminal.timeout", "terminal.cwd"],
    "description": "Terminal backend configuration"
  },
  "terminal.backend": {
    "path": "terminal.backend",
    "type": "string",
    "default": "local",
    "enum": ["local", "docker", "ssh", "modal", "singularity", "daytona"],
    "description": "Terminal execution environment"
  },
  "terminal.timeout": {
    "path": "terminal.timeout",
    "type": "integer",
    "default": 180,
    "min": 1,
    "max": 600,
    "description": "Max seconds for terminal commands"
  }
}
```

### 4.2 Dynamic Config Reader (`schema/dynamic.py`)

Reads the user's live `~/.hermes/config.yaml`.

1. Locates config path (respects `HERMES_HOME`, `HERMES_CONFIG` env vars)
2. Loads YAML safely
3. Flattens nested dict to dot-path keys
4. Masks secret values (keys containing `api_key`, `secret`, `token`, `password`)

### 4.3 Schema Matcher (`schema/matcher.py`)

Matches user config values against the static schema to produce a merged view:

- **Known config**: key exists in schema → show default + user value + description
- **Unknown config**: key exists in user config but NOT in schema → flag as "orphan"
- **Missing config**: key exists in schema but NOT in user config → flag as "optional"

### 4.4 Validator (`schema/validator.py`)

Validates a user config dict against the schema. Checks:

| Check | Logic |
|-------|-------|
| Type | `type(value)` matches schema type |
| Enum | Value is in known enum set |
| Range | Numeric value within [min, max] |
| Required | Required keys present (none currently required) |
| Unknown | Keys present in config but not in schema |
| Format | String matches expected format (regex) |
| Nested | Struct type values are proper dicts |

Returns structured result: `ValidationResult(errors=[], warnings=[], infos=[])`

### 4.5 CLI (`cli.py`)

Commands:

```bash
hermes-help validate [PATH]     # Validate config.yaml against schema
hermes-help query <KEY>          # Show full documentation for a config key
hermes-help diff [PATH]          # Diff user config vs schema defaults
hermes-help stub [--minimal]     # Generate a config.yaml stub
hermes-help schema               # Show schema stats (param count, sections)
hermes-help doc <KEY>            # Show expanded help for a key
hermes-help version              # Show version + schema version
```

### 4.6 TUI (`tui/app.py`)

Textual-based interactive browser:

1. **Main Screen**: Split layout
   - Left: Collapsible category tree (like VS Code settings sidebar)
   - Right: Parameter list + detail panel
   - Top: Search bar with fuzzy filtering

2. **Detail Screen**: When a parameter is selected
   - Full description
   - Type, default, allowed values (enum dropdown)
   - Current user value (green ✓), default value (grey)
   - Validation status
   - Inline editor with type-aware input

3. **Export Screen**: 
   - Select parameters to include
   - Preview generated YAML
   - Copy to clipboard or write to file

## 5. Hermes Plugin + Hooks

### 5.1 Plugin (`plugin/plugin.yaml`)

Registers a `post_tool_call` hook on `hermes update` completion:

- After `hermes update` finishes, checks if `DEFAULT_CONFIG` changed
- If yes, regenerates `compiled_schema.json`
- Reports schema changes to user

### 5.2 Shell Hooks

**`hooks/validate-config.sh`** — Registered on `hermes config set`:
- After any config change, validates the new config
- Surface warnings if validation fails

**`hooks/schema-post-update.sh`** — Registered on `on_session_start`:
- Checks if schema file is stale vs installed Hermes version
- Auto-regenerates if needed (with `allow_lazy_installs` check)

## 6. Versions & Compatibility

| Hermes Version | Schema Format | Notes |
|----------------|--------------|-------|
| >= 0.10.0 | v1 | Initial support |
| >= 0.15.0 | v2 | Added auxiliary sections |
| >= 0.17.0 | v3 | LCM context engine, CronOS |

Schema auto-detects Hermes version at runtime.

## 7. Quality Gates

| Gate | Requirement |
|------|------------|
| Static typing | All code passes `mypy --strict` |
| Linting | Zero `ruff` violations |
| Tests | 90%+ coverage on core schema + validator |
| Validation | Schema compiles 100% of DEFAULT_CONFIG keys |
| CI | GitHub Actions: lint → test → build |
| Safety | No credentials logged or leaked |

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| DEFAULT_CONFIG changes between Hermes versions | Schema compiler auto-detects; version pinning |
| User config has secrets | Dynamic reader masks `api_key`, `token`, `password` keys |
| Hermes not installed | Graceful error with install instructions |
| Circular imports from hermes-agent | Import only DEFAULT_CONFIG (no agent code) |

---

**Document version:** 1.0.0  
**Next review:** After first Hermes version change