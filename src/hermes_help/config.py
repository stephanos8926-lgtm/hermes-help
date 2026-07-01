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

# Known secret-matching patterns (for masking in output)
SECRET_KEY_PATTERNS = ["api_key", "secret", "token", "password", "private_key"]

# Schema version — bump when DEFAULT_CONFIG undergoes structural change
SCHEMA_VERSION = 3
