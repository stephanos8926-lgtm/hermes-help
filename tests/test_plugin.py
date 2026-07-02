"""Tests for the rapidwebs-help Hermes plugin."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest


@pytest.fixture
def plugin_module():
    """Import the plugin module."""
    import importlib.util
    import sys

    plugin_dir = Path.home() / ".hermes" / "plugins" / "hermes-help"
    init_path = plugin_dir / "__init__.py"

    if not init_path.exists():
        pytest.skip("Plugin not installed at ~/.hermes/plugins/rapidwebs-help/")

    spec = importlib.util.spec_from_file_location(
        "rapidwebs_help", str(init_path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_plugin_loads(plugin_module):
    """Plugin module loads with expected attributes."""
    assert plugin_module.version == "0.1.0"
    assert "post_tool_call" in plugin_module.hooks
    assert "on_session_start" in plugin_module.hooks
    assert hasattr(plugin_module, "register")


def test_register_registers_hooks(plugin_module):
    """register() registers post_tool_call and on_session_start hooks."""
    ctx = MagicMock()
    plugin_module.register(ctx)
    assert ctx.register_hook.call_count == 2


def test_format_age_just_now(plugin_module):
    """Files modified <60s show 'just now'."""
    import time
    age = plugin_module._format_age(time.time() - 30)
    assert "just now" in age


def test_format_age_minutes(plugin_module):
    """Files modified <1h show minutes."""
    import time
    age = plugin_module._format_age(time.time() - 300)
    assert "5m" in age


def test_format_age_hours(plugin_module):
    """Files modified <1d show hours."""
    import time
    age = plugin_module._format_age(time.time() - 7200)
    assert "2h" in age


def test_format_age_days(plugin_module):
    """Files modified >1d show days."""
    import time
    age = plugin_module._format_age(time.time() - 172800)
    assert "2d" in age


def test_validate_export_path_valid(plugin_module):
    """Valid path within home directory passes."""
    from hermes_help.tui.screens import _validate_export_path
    home = Path.home()
    path = _validate_export_path(str(home / "export.yaml"))
    assert path is not None
    assert path.name == "export.yaml"


def test_validate_export_path_traversal(plugin_module):
    """Path traversal with .. is blocked."""
    from hermes_help.tui.screens import _validate_export_path
    path = _validate_export_path("../etc/cron.d/malicious")
    assert path is None


def test_validate_export_path_outside_home(plugin_module):
    """Path outside home directory is blocked."""
    from hermes_help.tui.screens import _validate_export_path
    path = _validate_export_path("/etc/passwd")
    assert path is None


def test_on_session_start_no_schema(plugin_module):
    """on_session_start returns context note when schema missing."""
    with (
        patch.object(Path, "exists", return_value=False),
    ):
        result = plugin_module._on_session_start(None)
        assert "compiled schema" in result["context"]


def test_has_changed_recently_true(plugin_module):
    """File modified within window returns True."""
    with patch("time.time", return_value=100):
        mock = MagicMock()
        mock.stat().st_mtime = 95
        assert plugin_module._has_changed_recently(mock, window_seconds=10)


def test_has_changed_recently_false(plugin_module):
    """File modified outside window returns False."""
    with patch("time.time", return_value=100):
        mock = MagicMock()
        mock.stat().st_mtime = 80
        assert not plugin_module._has_changed_recently(mock, window_seconds=10)
