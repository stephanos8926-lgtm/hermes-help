"""rapidwebs-help: Hermes plugin for schema sync + config validation."""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger("rapidwebs-help")

hooks = ["post_tool_call", "on_session_start"]
version = "0.1.0"
description = "Auto-sync hermes-help schema and validate config on Hermes updates/config changes"
author = "RapidWebs Enterprise (Lucien)"
license = "MIT"
tags = ["config", "schema", "hermes-help", "rapidwebs"]
requirements = ["pyyaml"]


def register(ctx):
    """Register plugin hooks."""
    ctx.register_hook(
        "post_tool_call",
        "tool_name",
        _on_tool_result,
    )
    ctx.register_hook(
        "on_session_start",
        None,
        _on_session_start,
    )


def _hermes_help_bin() -> str | None:
    """Find the hermes-help CLI binary."""
    # Check common locations
    candidates = [
        os.path.expanduser("~/Workspaces/hermes-help/.venv/bin/hermes-help"),
        os.path.expanduser("~/.local/bin/hermes-help"),
        "/usr/local/bin/hermes-help",
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _hermes_help_dir() -> Path:
    """Return the hermes-help project root."""
    return Path(os.path.expanduser("~/Workspaces/hermes-help"))


def _compiled_schema_path() -> Path:
    """Path to the bundled compiled_schema.json."""
    return _hermes_help_dir() / "src" / "hermes_help" / "compiled_schema.json"


def _hermes_config_path() -> Path:
    """Path to Hermes config.yaml."""
    return Path(os.path.expanduser("~/.hermes/config.yaml"))


def _on_tool_result(tool_call, result, context):
    """Post-tool-call hook: sync schema after update, validate after config changes."""
    # Extract tool name regardless of whether tool_call is a dict or object
    tool_name = ""
    if isinstance(tool_call, dict):
        tool_name = tool_call.get("name", "")
        # Also check if this is the tool being called
        args = tool_call.get("arguments", {}) or {}
        tool_name = args.get("tool_name", tool_name)
    else:
        tool_name = getattr(tool_call, "name", "")

    # Normalise to string for matching
    result_str = str(result or "")

    # ── Trigger 1: Hermes update ──
    if "hermes update" in tool_name.lower() or "hermes update" in result_str.lower():
        _sync_schema()
        return {"context": "[rapidwebs-help: schema synced after update]"}

    # ── Trigger 2: Config file written ──
    if "config" in tool_name.lower() or "write_file" in tool_name.lower():
        config_path = _hermes_config_path()
        if config_path.exists() and _has_changed_recently(config_path):
            _validate_config(config_path)
            return {"context": "[rapidwebs-help: config validated]"}
        # Also check if the result mentions config.yaml
        if "config.yaml" in result_str:
            _validate_config(config_path)
            return {"context": "[rapidwebs-help: config validated]"}

    return {}


def _on_session_start(context):
    """On-session-start: check schema freshness."""
    schema_path = _compiled_schema_path()
    if not schema_path.exists():
        return {
            "context": "[rapidwebs-help: no compiled schema — run `hermes-help schema` to generate]"
        }

    # Check if schema is older than Hermes source
    hermes_config_py = Path(os.path.expanduser("~/.hermes/hermes-agent/hermes_cli/config.py"))
    if hermes_config_py.exists():
        schema_mtime = schema_path.stat().st_mtime
        hermes_mtime = hermes_config_py.stat().st_mtime
        if hermes_mtime > schema_mtime:
            return {
                "context": (
                    "[rapidwebs-help: schema may be stale — Hermes DEFAULT_CONFIG "
                    f"updated {_format_age(hermes_mtime)} ago, "
                    f"schema built {_format_age(schema_mtime)} ago. "
                    "Run `hermes-help schema` to refresh]"
                )
            }

    return {}


def _sync_schema():
    """Regenerate compiled_schema.json from Hermes DEFAULT_CONFIG."""
    schema_path = _compiled_schema_path()
    project_dir = _hermes_help_dir()

    # Add project src dir and Hermes source to Python path
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    paths = [
        str(project_dir / "src"),
        str(project_dir),
        os.path.expanduser("~/.hermes/hermes-agent"),
    ]
    env["PYTHONPATH"] = ":".join(paths + [pythonpath])

    script = """
import json, sys
sys.path.insert(0, \"$HOME/.hermes/hermes-agent\")
sys.path.insert(0, \"$HOME/Workspaces/hermes-help/src\")
from hermes_cli.config import DEFAULT_CONFIG
from hermes_help.schema.static import SchemaCompiler
from hermes_help.config import SCHEMA_VERSION

compiler = SchemaCompiler(DEFAULT_CONFIG)
schema = compiler.compile()

data = {
    'version': schema.version,
    'params': {k: {
        'path': v.path, 'type': v.type, 'default': v.default,
        'enum': v.enum, 'min_val': v.min_val, 'max_val': v.max_val,
        'description': v.description, 'required': v.required,
    } for k, v in schema.params.items()},
    'sections': {k: {
        'path': v.path, 'children': v.children, 'description': v.description,
    } for k, v in schema.sections.items()},
    'param_count': schema.param_count,
    'section_count': schema.section_count,
}

with open('$SCHEMA_PATH', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Synced: {schema.param_count} params')
"""

    try:
        # Use python3 -c with inline code
        import shlex

        cmd = [
            sys.executable or "python3",
            "-c",
            script.replace("$HOME", os.path.expanduser("~")).replace(
                "$SCHEMA_PATH", str(schema_path)
            ),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            logger.info(f"Schema synced: {result.stdout.strip()}")
        else:
            logger.warning(f"Schema sync failed: {result.stderr.strip()}")
    except Exception as exc:
        logger.warning(f"Schema sync error: {exc}")


def _validate_config(config_path: Path):
    """Run hermes-help validate against the current config."""
    hermes_help = _hermes_help_bin()
    if hermes_help is None:
        logger.warning("hermes-help CLI not found — skipping auto-validation")
        return

    try:
        result = subprocess.run(
            [hermes_help, "validate", str(config_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            logger.warning(f"Config validation found issues:\\n{result.stdout.strip()}")
    except Exception as exc:
        logger.warning(f"Config validation error: {exc}")


def _has_changed_recently(path: Path, window_seconds: int = 10) -> bool:
    """Check if a file was modified within the last N seconds."""
    try:
        return (time.time() - path.stat().st_mtime) < window_seconds
    except OSError:
        return False


def _format_age(mtime: float) -> str:
    """Format a file mtime into a human-readable age."""
    age = time.time() - mtime
    if age < 60:
        return "just now"
    if age < 3600:
        return f"{int(age // 60)}m ago"
    if age < 86400:
        return f"{int(age // 3600)}h ago"
    return f"{int(age // 86400)}d ago"
