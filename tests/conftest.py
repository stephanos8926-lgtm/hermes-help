"""Shared test fixtures."""
from pathlib import Path
import tempfile
import pytest

from hermes_help.schema.static import SchemaCompiler, CompiledSchema


@pytest.fixture
def sample_schema() -> CompiledSchema:
    """Return a compiled schema from a small test config dict."""
    compiler = SchemaCompiler({
        "terminal": {
            "backend": "local",
            "timeout": 180,
            "container_cpu": 1,
        },
        "display": {
            "interface": "cli",
            "compact": False,
        },
        "compression": {
            "enabled": True,
            "threshold": 0.5,
        },
    })
    return compiler.compile()


@pytest.fixture
def temp_config_dir():
    """Create a temp directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def minimal_config_yaml():
    """Content for a minimal but valid config.yaml."""
    return """
terminal:
  backend: local
  timeout: 300
display:
  interface: cli
compression:
  enabled: true
  threshold: 0.6
"""
