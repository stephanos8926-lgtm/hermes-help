"""Tests for the dynamic config reader."""
from pathlib import Path
import pytest
import yaml

from hermes_help.schema.dynamic import ConfigReader, ConfigMap


def test_read_existing_config(temp_config_dir, minimal_config_yaml):
    """Reader loads and flattens a valid config.yaml."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text(minimal_config_yaml)

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result is not None
    assert result.flat["terminal.backend"] == "local"
    assert result.flat["terminal.timeout"] == 300
    assert result.flat["display.interface"] == "cli"
    assert result.flat["compression.threshold"] == 0.6


def test_read_missing_file():
    """Returns None for nonexistent path."""
    reader = ConfigReader("/nonexistent/path/config.yaml")
    assert reader.read() is None


def test_read_empty_config(temp_config_dir):
    """Empty config file yields empty flat map."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result is not None
    assert result.flat == {}


def test_masks_api_keys(temp_config_dir):
    """Keys matching secret patterns are masked."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("openrouter:\n  api_key: sk-or-v1-abc123\n")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.flat["openrouter.api_key"] == "***MASKED***"
    assert "openrouter.api_key" in result.masked_keys


def test_masks_tokens(temp_config_dir):
    """Token keys are masked."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("discord:\n  token: abc.def.ghi\n")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.flat["discord.token"] == "***MASKED***"


def test_masks_secrets(temp_config_dir):
    """Secret keys are masked."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("bedrock:\n  secret: supersecret\n")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.flat["bedrock.secret"] == "***MASKED***"


def test_non_secret_keys_visible(temp_config_dir):
    """Non-secret keys remain visible."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("terminal:\n  backend: docker\n  timeout: 300\n")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.flat["terminal.backend"] == "docker"
    assert result.flat["terminal.timeout"] == 300
    assert result.masked_keys == []


def test_deep_nesting(temp_config_dir):
    """3+ level nesting is flattened correctly."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text("a:\n  b:\n    c:\n      d: deep_value\n")

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.flat["a.b.c.d"] == "deep_value"


def test_source_path(temp_config_dir, minimal_config_yaml):
    """source_path is set to the resolved config path."""
    config_path = temp_config_dir / "config.yaml"
    config_path.write_text(minimal_config_yaml)

    reader = ConfigReader(config_path)
    result = reader.read()
    assert result.source_path == str(config_path.resolve())
