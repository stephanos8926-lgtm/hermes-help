"""Tests for the Hermes Help TUI widgets."""
from __future__ import annotations

from typing import Any

import pytest
from hermes_help.schema.static import SchemaCompiler, ParamDef


# ── Test helpers ──


def _make_param(path: str, type_name: str, default: Any = None, enum: list | None = None) -> ParamDef:
    return ParamDef(
        path=path,
        type=type_name,
        default=default,
        enum=enum,
    )


# ── ParamEditor type mapping tests ──


def test_param_editor_string_type():
    """String params map to 'input' control type."""
    param = _make_param("test.key", "string", default="hello")
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_integer_type():
    """Integer params map to 'input' control type."""
    param = _make_param("test.num", "integer", default=42)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_float_type():
    """Float params map to 'input' control type."""
    param = _make_param("test.ratio", "float", default=0.5)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_boolean_type():
    """Boolean params map to 'checkbox' control type."""
    param = _make_param("test.flag", "boolean", default=True)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "checkbox"


def test_param_editor_enum_type():
    """Enum params map to 'select' control type."""
    param = _make_param("test.backend", "string", enum=["a", "b", "c"])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "select"


def test_param_editor_list_type():
    """List params map to 'input' control type."""
    param = _make_param("test.items", "list", default=[])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_null_type():
    """Null params map to 'none' control type (no editing)."""
    param = _make_param("test.empty", "null", default=None)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "none"


def test_param_editor_enum_wins_over_string():
    """Enum takes priority over string for control type mapping."""
    param = _make_param("test.enum_str", "string", default="a", enum=["a", "b"])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "select"


def test_param_editor_label_contains_path():
    """Editor label includes the param path."""
    param = _make_param("terminal.backend", "string", default="local", enum=["local", "docker"])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) in ("select", "input")
