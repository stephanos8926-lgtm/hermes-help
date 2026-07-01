# hermes-help Implementation Plan

> **For Hermes:** Use `subagent-driven-development` to implement this plan task-by-task.
> **Mode:** HIGH — security-critical, public-facing tool, 20+ files, multi-phase sprint

**Goal:** Build a dual-mode (CLI + TUI) Hermes Agent configuration helper with 100% schema coverage, static + dynamic config awareness, validation engine, and complementary Hermes plugin + hooks.

**Architecture:** Click CLI + Textual TUI sharing a common schema/validation core. Static schema extracted from Hermes' `DEFAULT_CONFIG` at build time; dynamic reader loads runtime `config.yaml`. Validator compares user config against typed schema.

**Tech Stack:** Python 3.12, Click 8.1, Textual 1.0, PyYAML 6.0, pytest 8.0, ruff

---

## Phase 0: Project Foundation

### Task 0.1: Set up source tree + package scaffolding

**Objective:** Write all `__init__.py` files and ensure the package is importable

**Step 1: Write init files**

```python
# src/hermes_help/__init__.py
"""Hermes Agent configuration helper — schema-aware CLI + TUI."""

__version__ = "0.1.0"
```

```python
# src/hermes_help/schema/__init__.py
from hermes_help.schema.static import SchemaCompiler, CompiledSchema
from hermes_help.schema.dynamic import ConfigReader, ConfigMap
from hermes_help.schema.validator import Validator, ValidationResult
```

```python
# src/hermes_help/tui/__init__.py
```

```python
# src/hermes_help/tui/screens/__init__.py
```

```python
# src/hermes_help/tui/widgets/__init__.py
```

```python
# src/hermes_help/providers/__init__.py
```

```python
# src/hermes_help/plugin/__init__.py
```

```python
# src/hermes_help/hooks/__init__.py  # empty
```

```python
# src/hermes_help/__main__.py
"""Allow `python -m hermes_help` to invoke the CLI."""
from hermes_help.cli import main
main()
```

**Step 2: Verify import**

```bash
cd ~/Workspaces/hermes-help
uv run python -c "from hermes_help import __version__; print(__version__)"
uv run python -c "from hermes_help.schema import SchemaCompiler; print('ok')"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "init: project scaffolding with package structure"
```

---

### Task 0.2: Create config.py with paths + constants

**Objective:** Define config paths, default locations, helper utilities

**Files:**
- Create: `src/hermes_help/config.py`

**Content:**

```python
"""Config paths, defaults, and utility helpers."""

import os
from pathlib import Path


def get_hermes_home() -> Path:
    """Locate ~/.hermes/ respecting HERMES_HOME env var."""
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".hermes"


def get_config_path() -> Path:
    """Locate config.yaml, respecting HERMES_CONFIG env var."""
    env = os.environ.get("HERMES_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return get_hermes_home() / "config.yaml"


# Paths for Hermes source introspection
HERMES_SOURCE_DIR = get_hermes_home() / "hermes-agent"
HERMES_CONFIG_PY = HERMES_SOURCE_DIR / "hermes_cli" / "config.py"
COMPILED_SCHEMA_PATH = Path(__file__).parent / "compiled_schema.json"

# Known secret-matching patterns (for masking)
SECRET_KEY_PATTERNS = ["api_key", "secret", "token", "password", "private_key"]

# Schema version (bump when DEFAULT_CONFIG changes structure)
SCHEMA_VERSION = 3
```

**Test:**
```bash
uv run python -c "from hermes_help.config import get_config_path; print(get_config_path())"
```

---

## Phase 1: Static Schema Extractor

### Task 1.1: SchemaCompiler — walk DEFAULT_CONFIG

**Objective:** Build the core schema compiler that extracts all config parameters from Hermes' `DEFAULT_CONFIG`

**Files:**
- Create: `src/hermes_help/schema/static.py`
- Test: `tests/test_static.py`

**Schema model:**

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParamDef:
    """Definition of a single configuration parameter."""
    path: str                    # dot.separated.path
    type: str                    # "string" | "integer" | "float" | "boolean" | "list" | "dict"
    default: Any = None
    enum: list | None = None     # Allowed values (for constrained params)
    min_val: float | None = None
    max_val: float | None = None
    description: str = ""
    required: bool = False
    version_added: int = 1       # Schema version when added


@dataclass
class SectionDef:
    """Definition of a config section (branch node)."""
    path: str
    children: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class CompiledSchema:
    """Complete compiled schema."""
    version: int
    params: dict[str, ParamDef]     # path → ParamDef
    sections: dict[str, SectionDef]  # path → SectionDef
    param_count: int
    section_count: int
```

**SchemaCompiler class:**

```python
class SchemaCompiler:
    """Extracts a typed schema from Hermes' DEFAULT_CONFIG."""
    
    # Type inference map
    TYPE_MAP: dict[type, str] = {
        str: "string",
        int: "integer",
        float: "float",
        bool: "boolean",
        list: "list",
        dict: "dict",
        type(None): "null",
    }
    
    # Known enum sets extracted from DEFAULT_CONFIG
    KNOWN_ENUMS: dict[str, list] = {
        "terminal.backend": ["local", "docker", "ssh", "modal", "singularity", "daytona"],
        "tts.provider": ["edge", "elevenlabs", "openai", "xai", "minimax", "mistral", "gemini", "neutts", "kittentts", "piper"],
        "stt.provider": ["local", "groq", "openai", "mistral", "elevenlabs"],
        "display.interface": ["cli", "tui"],
        "terminal.home_mode": ["auto", "real", "profile"],
        "approvals.mode": ["manual", "smart", "off"],
        "approvals.cron_mode": ["deny", "approve"],
        "context.engine": ["compressor", "lcm", "dcp"],
        "display.final_response_markdown": ["render", "strip", "raw"],
        "display.reasoning_style": ["code", "blockquote", "subtext"],
        "display.memory_notifications": ["off", "on", "verbose"],
        "web.search_backend": ["", "searxng", "tavily", "exa"],
        "web.extract_backend": ["", "native", "jina", "firecrawl"],
        "agent.tool_use_enforcement": ["auto", True, False],
        "agent.coding_context": ["auto", "focus", "on", "off"],
        "agent.verify_on_stop": ["auto", True, False],
        "agent.image_input_mode": ["auto", "native", "text"],
        "coding.mode": ["auto", "disabled", "warn", "strict"],
        "tools.tool_search.enabled": ["auto", "on", "off"],
        # Display platforms
        "display.platforms.telegram.streaming": [True, False],
        "display.platforms.discord.streaming": [True, False],
        # Container resource types
        "terminal.backend": ["local", "docker", "ssh", "modal", "singularity", "daytona"],
        "browser.engine": ["auto", "lightpanda", "chrome"],
        "streaming.transport": ["auto", "draft", "edit", "off"],
        "stt.local.model": ["tiny", "base", "small", "medium", "large-v3"],
        "stt.openai.model": ["whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe"],
        "stt.elevenlabs.model_id": ["scribe_v2", "scribe_v1"],
        "display.busy_input_mode": ["interrupt", "queue", "steer"],
        "display.tui_status_indicator": ["kaomoji", "emoji", "unicode", "ascii"],
        "display.language": ["en", "zh", "ja", "de", "es", "fr", "tr", "uk"],
        "display.copy_shortcut": ["auto", "ctrl_c", "ctrl_shift_c", "disabled"],
        "dashboard.theme": ["default", "midnight", "ember", "mono", "cyberpunk", "rose"],
        "code_execution.mode": ["project", "strict"],
        "human_delay.mode": ["off", "fixed", "realistic", "uniform"],
        "agent.service_tier": ["", "default", "eco"],
        "curator.prune_builtins": [True, False],
        "curator.consolidate": [True, False],
        "display.resume_skip_tool_only": [True, False],
        "display.inline_diffs": [True, False],
    }
    
    # Known range bounds
    KNOWN_RANGES: dict[str, tuple[float | None, float | None]] = {
        "terminal.timeout": (1, 600),
        "terminal.container_cpu": (0.5, None),
        "terminal.container_memory": (256, None),
        "terminal.container_disk": (1024, None),
        "terminal.daemon_term_grace_seconds": (0, None),
        "compression.threshold": (0.0, 1.0),
        "compression.target_ratio": (0.0, 1.0),
        "compression.hygiene_hard_message_limit": (1, None),
        "compression.protect_last_n": (0, None),
        "compression.protect_first_n": (0, None),
        "agent.max_turns": (1, 500),
        "agent.gateway_timeout": (0, 36000),
        "agent.restart_drain_timeout": (0, 3600),
        "agent.api_max_retries": (0, 10),
        "agent.gateway_notify_interval": (0, 3600),
        "agent.clarify_timeout": (0, 3600),
        "agent.gateway_auto_continue_freshness": (0, 86400),
        "memory.memory_char_limit": (100, 50000),
        "memory.user_char_limit": (100, 30000),
        "delegation.max_iterations": (1, 500),
        "delegation.max_concurrent_children": (1, 20),
        "delegation.max_spawn_depth": (1, None),
        "delegation.child_timeout_seconds": (0, 36000),
        "checkpoints.max_snapshots": (1, 100),
        "checkpoints.max_total_size_mb": (0, 10000),
        "checkpoints.max_file_size_mb": (0, 1000),
        "checkpoints.retention_days": (1, 365),
        "browser.inactivity_timeout": (10, 3600),
        "browser.command_timeout": (5, 120),
        "browser.dialog_timeout_s": (30, 600),
        "display.resume_exchanges": (1, 50),
        "streaming.edit_interval": (0.1, 5.0),
        "sessions.retention_days": (1, 365),
        "curator.stale_after_days": (1, 365),
        "curator.archive_after_days": (1, 730),
        "cron.output_retention": (1, 500),
        "kanban.failure_limit": (1, 10),
        "kanban.dispatch_interval_seconds": (10, 600),
        "kanban.dispatch_stale_timeout_seconds": (60, 86400),
        "kanban.auto_decompose_per_tick": (1, 20),
        "logging.max_size_mb": (1, 100),
        "logging.backup_count": (1, 10),
        "mcp_discovery_timeout": (0.1, 30.0),
        "tool_output.max_bytes": (1000, 500000),
        "tool_output.max_lines": (50, 5000),
        "tool_output.max_line_length": (100, 10000),
        "gateway.max_inbound_media_bytes": (0, 1_000_000_000),
        "file_read_max_chars": (1000, 500_000),
        "context_file_max_chars": (5000, None),
    }

    def __init__(self, default_config: dict | None = None):
        self._default_config = default_config
    
    def compile(self) -> CompiledSchema:
        """Walk DEFAULT_CONFIG and build CompiledSchema."""
        ...
    
    def _walk(self, data: dict, prefix: str, params: dict, sections: dict):
        """Recursively walk nested dict."""
        ...
    
    def _infer_type(self, value: Any) -> str: ...
    def _get_enum(self, path: str) -> list | None: ...
    def _get_range(self, path: str) -> tuple | None: ...
    def _make_description(self, path: str, key: str) -> str: ...
```

**Implementation detail — the walker:**

```python
def _walk(self, data: dict, prefix: str, params: dict, sections: dict):
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict) and not self._is_flat_dict(value):
            # Branch — section node
            children = list(value.keys())
            full_children = [f"{path}.{c}" for c in children]
            sections[path] = SectionDef(path=path, children=full_children)
            self._walk(value, path, params, sections)
        else:
            # Leaf — param node
            param_type = self._infer_type(value)
            enum = self._get_enum(path)
            rmin, rmax = self._get_range(path) or (None, None)
            params[path] = ParamDef(
                path=path,
                type=param_type,
                default=value,
                enum=enum,
                min_val=rmin,
                max_val=rmax,
            )

def _is_flat_dict(self, d: dict) -> bool:
    """Detect if a dict is a flat config leaf (not a section)."""
    # Flat dicts contain only scalar/list values (no nested dicts)
    # OR have an 'enabled', 'provider', 'model', 'voice', 'backend' key
    # which are known leaf patterns
    return not any(isinstance(v, dict) for v in d.values())
```

**Tests:**
```python
# tests/test_static.py
import pytest
from hermes_help.schema.static import SchemaCompiler, CompiledSchema, ParamDef, SectionDef

def test_compile_returns_schema():
    """SchemaCompiler.compile() returns a CompiledSchema."""
    compiler = SchemaCompiler({"terminal": {"backend": "local", "timeout": 180}})
    result = compiler.compile()
    assert isinstance(result, CompiledSchema)
    assert result.param_count == 2
    assert result.section_count == 1

def test_compile_terminal_backend():
    """terminal.backend is string type with known enum."""
    compiler = SchemaCompiler({"terminal": {"backend": "local"}})
    result = compiler.compile()
    param = result.params["terminal.backend"]
    assert param.type == "string"
    assert "local" in (param.enum or [])

def test_compile_numeric_bounds():
    """Numeric params get min/max from KNOWN_RANGES."""
    compiler = SchemaCompiler({"terminal": {"timeout": 180}})
    result = compiler.compile()
    param = result.params["terminal.timeout"]
    assert param.min_val == 1
    assert param.max_val == 600

def test_compile_deep_nesting():
    """test that nesting up to 4 levels deep works."""
    compiler = SchemaCompiler({"a": {"b": {"c": {"d": "val"}}}})
    result = compiler.compile()
    assert "a.b.c.d" in result.params
    assert "a.b.c" in result.sections

def test_compile_flat_dict_as_param():
    """dict with scalar values only should be treated as params, not sections."""
    compiler = SchemaCompiler({"options": {"enabled": True, "name": "test"}})
    result = compiler.compile()
    assert "options" in result.sections  # options is a section container
    assert "options.enabled" in result.params
```

---

### Task 1.2: SchemaCompiler — load from real Hermes DEFAULT_CONFIG

**Objective:** Compile the schema from the actual installed Hermes source

**Files:**
- Modify: `src/hermes_help/schema/static.py`
- Create: `tests/test_static_real.py`

**Implementation:**

```python
import importlib.util
import sys

def load_default_config() -> dict | None:
    """Import DEFAULT_CONFIG from installed Hermes package."""
    try:
        from hermes_cli.config import DEFAULT_CONFIG
        return DEFAULT_CONFIG
    except ImportError:
        return None

def compile_from_hermes() -> CompiledSchema | None:
    """Try to compile schema from installed Hermes."""
    config = load_default_config()
    if config is None:
        return None
    return SchemaCompiler(config).compile()
```

**Fallback path:** If Hermes not installed, load from bundled `compiled_schema.json`

---

## Phase 2: Dynamic Config Reader

### Task 2.1: ConfigReader with secret masking

**Objective:** Read user's config.yaml, flatten to dot-path map, mask secrets

**Files:**
- Create: `src/hermes_help/schema/dynamic.py`
- Test: `tests/test_dynamic.py`

```python
@dataclass
class ConfigMap:
    """User's config as a flat path→value map with metadata."""
    raw: dict                      # Original nested dict
    flat: dict[str, Any]           # Flattened path→value
    source_path: str               # Path to config.yaml
    version: str = ""              # Hermes version if detectable
    masked_keys: list[str] = field(default_factory=list)

class ConfigReader:
    """Read and flatten user's config.yaml."""
    
    SECRET_PATTERNS = ["api_key", "secret", "token", "password"]
    
    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else get_config_path()
    
    def read(self) -> ConfigMap | None:
        """Load, flatten, mask. Returns None if file missing."""
        if not self._path.exists():
            return None
        
        with open(self._path) as f:
            raw = yaml.safe_load(f) or {}
        
        flat = {}
        masked = []
        self._flatten(raw, "", flat, masked)
        
        return ConfigMap(
            raw=raw, flat=flat, source_path=str(self._path),
            masked_keys=masked,
        )
    
    def _flatten(self, data: dict, prefix: str, out: dict, masked: list):
        """Recursively flatten nested dict to dot-path keys."""
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten(value, path, out, masked)
            else:
                # Mask secrets
                if any(p in key.lower() for p in self.SECRET_PATTERNS):
                    out[path] = "***MASKED***"
                    masked.append(path)
                else:
                    out[path] = value
```

**Tests:**
```python
def test_read_existing_config(tmp_path):
    """Reads and flattens a valid config.yaml."""
    config = tmp_path / "config.yaml"
    config.write_text("terminal:\n  backend: docker\n  timeout: 300\n")
    reader = ConfigReader(config)
    result = reader.read()
    assert result is not None
    assert result.flat["terminal.backend"] == "docker"
    assert result.flat["terminal.timeout"] == 300

def test_read_missing_file(tmp_path):
    """Returns None for missing file."""
    reader = ConfigReader(tmp_path / "nonexistent.yaml")
    assert reader.read() is None

def test_masks_secrets(tmp_path):
    """Keys matching secret patterns are masked."""
    config = tmp_path / "config.yaml"
    config.write_text("openrouter:\n  api_key: sk-or-v1-abc123\n  response_cache: true\n")
    reader = ConfigReader(config)
    result = reader.read()
    assert result.flat["openrouter.api_key"] == "***MASKED***"
    assert "openrouter.api_key" in result.masked_keys
    assert result.flat["openrouter.response_cache"] is True
```

---

### Task 2.2: Schema matcher — merge user config with schema

**Objective:** Match user config values against the static schema to produce merged view

**Files:**
- Create: `src/hermes_help/schema/matcher.py`
- Test: `tests/test_matcher.py`

```python
@dataclass
class MatchedParam:
    """A parameter with both schema and user value (if set)."""
    param: ParamDef
    user_value: Any = None        # None = not set by user
    is_set: bool = False
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

@dataclass
class MatchedConfig:
    """Full matched result: schema × user config."""
    known: dict[str, MatchedParam]     # Key matches schema
    unknown: dict[str, Any]            # User key NOT in schema
    missing: dict[str, ParamDef]       # Schema key NOT in user config
    user_config: ConfigMap | None
    schema_version: int

class ConfigMatcher:
    """Match user config against compiled schema."""
    
    def __init__(self, schema: CompiledSchema, user: ConfigMap | None = None):
        self._schema = schema
        self._user = user
    
    def match(self) -> MatchedConfig:
        """Produce merged view."""
        known = {}
        for path, param in self._schema.params.items():
            mp = MatchedParam(param=param)
            if self._user and path in self._user.flat:
                mp.user_value = self._user.flat[path]
                mp.is_set = True
            known[path] = mp
        
        unknown = {}
        if self._user:
            for path in self._user.flat:
                if path not in self._schema.params:
                    unknown[path] = self._user.flat[path]
        
        missing = {}
        for path, param in self._schema.params.items():
            if not known[path].is_set:
                missing[path] = param
        
        return MatchedConfig(
            known=known, unknown=unknown, missing=missing,
            user_config=self._user, schema_version=self._schema.version,
        )
```

---

## Phase 3: Validation Engine

### Task 3.1: Validator implementation

**Objective:** Validate user config values against schema types, enums, ranges

**Files:**
- Create: `src/hermes_help/schema/validator.py`
- Test: `tests/test_validator.py`

```python
@dataclass
class ValidationIssue:
    path: str
    severity: str            # "error" | "warning" | "info"
    message: str
    expected: str = ""
    actual: str = ""

@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    infos: list[ValidationIssue] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    @property
    def summary(self) -> str:
        parts = []
        if self.errors: parts.append(f"{len(self.errors)} errors")
        if self.warnings: parts.append(f"{len(self.warnings)} warnings")
        if self.infos: parts.append(f"{len(self.infos)} infos")
        return f"Validation: {', '.join(parts) if parts else 'all clear'}"

class Validator:
    """Validate a user config against schema."""
    
    def __init__(self, schema: CompiledSchema):
        self._schema = schema
    
    def validate(self, config: ConfigMap) -> ValidationResult:
        """Validate full config against schema."""
        result = ValidationResult()
        
        for path, value in config.flat.items():
            param = self._schema.params.get(path)
            if param is None:
                result.warnings.append(ValidationIssue(
                    path=path, severity="warning",
                    message=f"Unknown config key: {path}",
                ))
                continue
            self._validate_param(path, value, param, result)
        
        return result
    
    def validate_value(self, path: str, value: Any) -> list[ValidationIssue]:
        """Validate a single value against schema. Used by TUI inline editor."""
        param = self._schema.params.get(path)
        if param is None:
            return [ValidationIssue(path, "error", f"Unknown key: {path}")]
        result = ValidationResult()
        self._validate_param(path, value, param, result)
        return result.errors + result.warnings
    
    def _validate_param(self, path: str, value: Any, param: ParamDef, result: ValidationResult):
        """Validate one param value."""
        # Type check
        expected_type = param.type
        actual_type = type(value).__name__
        type_ok = self._check_type(value, expected_type)
        if not type_ok:
            result.errors.append(ValidationIssue(
                path=path, severity="error",
                message=f"Expected {expected_type}, got {actual_type}",
                expected=expected_type, actual=actual_type,
            ))
            return  # No further checks if type is wrong
        
        # Enum check
        if param.enum and value not in param.enum:
            result.errors.append(ValidationIssue(
                path=path, severity="error",
                message=f"Value must be one of: {param.enum}",
                expected=str(param.enum), actual=str(value),
            ))
        
        # Range check (numeric)
        if isinstance(value, (int, float)):
            if param.min_val is not None and value < param.min_val:
                result.errors.append(ValidationIssue(
                    path=path, severity="error",
                    message=f"Below minimum ({param.min_val})",
                    expected=f">= {param.min_val}", actual=str(value),
                ))
            if param.max_val is not None and value > param.max_val:
                result.errors.append(ValidationIssue(
                    path=path, severity="error",
                    message=f"Above maximum ({param.max_val})",
                    expected=f"<= {param.max_val}", actual=str(value),
                ))
    
    def _check_type(self, value: Any, expected: str) -> bool:
        mapping = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "list": list,
            "dict": dict,
            "null": type(None),
        }
        py_type = mapping.get(expected)
        if py_type is None:
            return True  # Unknown type — skip
        return isinstance(value, py_type)
```

**Tests:**
```python
def test_validate_correct_config():
    schema = SchemaCompiler({"terminal": {"backend": "local", "timeout": 180}}).compile()
    config = ConfigMap(raw={}, flat={"terminal.backend": "docker", "terminal.timeout": 300}, source_path="")
    validator = Validator(schema)
    result = validator.validate(config)
    assert result.is_valid

def test_validate_type_error():
    schema = SchemaCompiler({"terminal": {"timeout": 180}}).compile()
    config = ConfigMap(raw={}, flat={"terminal.timeout": "not_a_number"}, source_path="")
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Expected integer" in e.message for e in result.errors)

def test_validate_enum_error():
    schema = SchemaCompiler({"terminal": {"backend": "local"}}).compile()
    config = ConfigMap(raw={}, flat={"terminal.backend": "invalid_backend"}, source_path="")
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Value must be one of" in e.message for e in result.errors)

def test_validate_range_below_min():
    schema = SchemaCompiler({"terminal": {"timeout": 180}}).compile()
    config = ConfigMap(raw={}, flat={"terminal.timeout": 0}, source_path="")
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Below minimum" in e.message for e in result.errors)
```

---

## Phase 4: CLI Implementation

### Task 4.1: Click CLI — validate command

**Objective:** `hermes-help validate [--path PATH] [--verbose]` — validate config against schema

**Files:**
- Create: `src/hermes_help/cli.py`

```python
import click
from pathlib import Path
from hermes_help.schema.static import SchemaCompiler, compile_from_hermes
from hermes_help.schema.dynamic import ConfigReader
from hermes_help.schema.validator import Validator
from hermes_help import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """hermes-help — Hermes Agent configuration helper."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True), required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show all checks including passing")
def validate(path, verbose):
    """Validate a Hermes config.yaml against the schema."""
    schema = compile_from_hermes()
    if schema is None:
        click.echo("✘ Cannot load Hermes DEFAULT_CONFIG. Is Hermes installed?", err=True)
        raise click.Abort()
    
    config_path = Path(path) if path else None
    reader = ConfigReader(config_path)
    config = reader.read()
    if config is None:
        click.echo(f"✘ Config not found: {reader.path}", err=True)
        raise click.Abort()
    
    validator = Validator(schema)
    result = validator.validate(config)
    
    if result.is_valid and not verbose:
        click.echo(f"✔ Config is valid ({len(result.infos)} informational items)")
        return
    
    for issue in result.errors:
        click.echo(f"✘ {issue.path}: {issue.message}")
    for issue in result.warnings:
        click.echo(f"⚠ {issue.path}: {issue.message}")
    for issue in result.infos:
        click.echo(f"ℹ {issue.path}: {issue.message}")
    
    if not result.is_valid:
        raise click.Abort()
```

### Task 4.2: CLI — query, diff, stub commands

**Objective:** Complete CLI with query, diff, stub, schema, doc commands

**query command:**
```python
@main.command()
@click.argument("key")
def query(key):
    """Show full documentation for a config key."""
    schema = compile_from_hermes()
    if schema is None:
        click.echo("✘ Cannot load Hermes schema.", err=True)
        raise click.Abort()
    
    param = schema.params.get(key)
    section = schema.sections.get(key)
    
    if param is None and section is None:
        click.echo(f"✘ Unknown key: {key}")
        raise click.Abort()
    
    if param:
        click.echo(f"  Key: {param.path}")
        click.echo(f"  Type: {param.type}")
        click.echo(f"  Default: {param.default}")
        if param.enum:
            click.echo(f"  Allowed: {', '.join(str(e) for e in param.enum)}")
        if param.min_val is not None:
            click.echo(f"  Range: [{param.min_val}, {param.max_val or '∞'}]")
        click.echo(f"  Required: {param.required}")
    
    if section:
        click.echo(f"\n  Section: {section.path}")
        click.echo(f"  Parameters: {len(section.children)}")
        for child in section.children[:10]:
            click.echo(f"    • {child}")
        if len(section.children) > 10:
            click.echo(f"    … and {len(section.children) - 10} more")
```

**diff command:**
```python
@main.command()
@click.argument("path", type=click.Path(exists=True), required=False)
def diff(path):
    """Diff user config against schema defaults."""
    schema = compile_from_hermes()
    reader = ConfigReader(Path(path) if path else None)
    config = reader.read()
    
    from hermes_help.schema.matcher import ConfigMatcher
    matched = ConfigMatcher(schema, config).match()
    
    modified = [p for p in matched.known.values() if p.is_set and p.user_value != p.param.default]
    same = [p for p in matched.known.values() if p.is_set and p.user_value == p.param.default]
    
    click.echo(f"Modified parameters: {len(modified)}")
    for mp in modified:
        click.echo(f"  ~ {mp.param.path}: {mp.param.default!r} → {mp.user_value!r}")
    
    click.echo(f"\nSet to default: {len(same)}")
    click.echo(f"Not set: {len(matched.missing)}")
    if matched.unknown:
        click.echo(f"\nUnknown keys: {len(matched.unknown)}")
        for path in matched.unknown:
            click.echo(f"  ? {path}")
```

**stub command:**
```python
@main.command()
@click.option("--minimal", is_flag=True, help="Only required/important params")
@click.option("--section", "-s", help="Generate stub for a specific section only")
def stub(minimal, section):
    """Generate a config.yaml stub with all parameters."""
    schema = compile_from_hermes()
    import yaml
    
    def build_stub(schema, section_filter=None):
        result = {}
        for path, param in schema.params.items():
            if section_filter and not path.startswith(section_filter):
                continue
            if minimal and not param.required:
                continue
            keys = path.split(".")
            d = result
            for k in keys[:-1]:
                if k not in d:
                    d[k] = {}
                d = d[k]
            if keys[-1] not in d:
                d[keys[-1]] = param.default
        return result
    
    data = build_stub(schema, section)
    output = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    click.echo(output)
```

---

## Phase 5: TUI Implementation

### Task 5.1: Textual App shell

**Objective:** Basic Textual app with tree widget showing config categories

**Files:**
- Create: `src/hermes_help/tui/app.py`

```python
#!/usr/bin/env python3
"""Hermes Help TUI — interactive config browser."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static, ContentSwitcher

from hermes_help.schema.static import compile_from_hermes
from hermes_help.schema.dynamic import ConfigReader


class HermesHelpApp(App):
    """Hermes config browser TUI."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 35%;
        dock: left;
        border: solid $border;
    }
    #main-panel {
        width: 65%;
    }
    #search-bar {
        dock: top;
        height: 3;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Tree("Config", id="config-tree")
        yield Static(id="detail-panel")
        yield Footer()
    
    def on_mount(self) -> None:
        self._schema = compile_from_hermes()
        tree = self.query_one("#config-tree", Tree)
        # Build tree from schema sections
        root = tree.root
        for s_path, section in self._schema.sections.items():
            if "." not in s_path:  # Top-level only
                branch = root.add(s_path, expand=True)
                for child_path in section.children:
                    param = self._schema.params.get(child_path)
                    if param:
                        branch.add_leaf(f"{child_path}: {param.type}")
```

### Task 5.2: Search bar + param detail + inline editor

**Objective:** Interactive TUI with fuzzy search, parameter detail view, and type-aware editing

**Files:**
- Create: `src/hermes_help/tui/widgets/search_bar.py`
- Create: `src/hermes_help/tui/widgets/param_detail.py`
- Create: `src/hermes_help/tui/widgets/value_input.py`

(This phase has detailed Textual widget patterns per the `textual-framework-patterns` skill.)

---

## Phase 6: Plugin + Hooks

### Task 6.1: Hermes plugin manifest

**Objective:** Create Hermes plugin so hermes-help auto-updates its schema after `hermes update`

**Files:**
- Create: `src/hermes_help/plugin/plugin.yaml`
- Create: `src/hermes_help/plugin/__init__.py`

```yaml
# plugin.yaml
name: hermes-help
version: "0.1.0"
description: "Auto-sync hermes-help schema after Hermes updates"
author: "RapidWebs (Lucien)"
license: "MIT"
tags: ["config", "schema", "hermes-help"]
hooks:
  - post_tool_call
```

```python
# __init__.py
"""Hermes Help schema sync plugin."""

hooks = ["post_tool_call"]
version = "0.1.0"
description = "Auto-sync hermes-help schema after Hermes updates"
author = "RapidWebs (Lucien)"
license = "MIT"
tags = ["config", "schema", "hermes-help"]
requirements = ["pyyaml"]


def register(ctx):
    """Register post_tool_call hook for schema sync."""
    ctx.register_hook(
        "post_tool_call",
        "tool_call_name",
        schema_sync_handler,
    )


def schema_sync_handler(tool_call, result, context):
    """After hermes update, regenerate the schema."""
    tool_name = getattr(tool_call, "name", "") or tool_call.get("name", "")
    if tool_name in ("terminal",) and "hermes update" in str(result):
        from hermes_help.plugin.schema_sync import sync_schema
        sync_schema()
        return {"context": "[hermes-help: schema synced after update]"}
    return {}
```

---

## Execution Order

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| **0** | 0.1–0.2: Scaffolding, config.py | ~15 min |
| **1** | 1.1–1.2: SchemaCompiler + Hermes source loading | ~45 min |
| **2** | 2.1–2.2: ConfigReader, ConfigMatcher | ~30 min |
| **3** | 3.1: Validator | ~30 min |
| **4** | 4.1–4.2: CLI (validate, query, diff, stub) | ~45 min |
| **5** | 5.1–5.2: TUI shell + widgets | ~60 min |
| **6** | 6.1: Plugin + hooks | ~15 min |
| **7** | Integration testing, CI, docs | ~30 min |

**Total:** ~4.5 hours

---

## Verification

```bash
# Phase 0
uv run python -c "from hermes_help import __version__; print(__version__)"

# Phase 1
uv run python -c "from hermes_help.schema.static import compile_from_hermes; s = compile_from_hermes(); print(f'{s.param_count} params, {s.section_count} sections')"

# Phase 2
uv run python -m pytest tests/test_dynamic.py -v

# Phase 3
uv run python -m pytest tests/test_validator.py -v

# Phase 4
uv run hermes-help schema
uv run hermes-help query terminal.backend
uv run hermes-help diff

# Phase 5
uv run python -m hermes_help.tui.app

# Full test suite
uv run python -m pytest tests/ -v --tb=short
```