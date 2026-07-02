"""Tests for the Hermes Help TUI widgets."""
from __future__ import annotations

from typing import Any

import pytest
from hermes_help.schema.static import ParamDef

# Textual widgets need an active App context — skip full init tests
# and focus on param parsing, control mapping, and compose yields


def _make_param(path: str, type_name: str, default: Any = None, enum: list | None = None) -> ParamDef:
    return ParamDef(path=path, type=type_name, default=default, enum=enum)


def test_param_editor_string_type():
    param = _make_param("test.key", "string", default="hello")
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_integer_type():
    param = _make_param("test.num", "integer", default=42)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_float_type():
    param = _make_param("test.ratio", "float", default=0.5)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_boolean_type():
    param = _make_param("test.flag", "boolean", default=True)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "checkbox"


def test_param_editor_enum_type():
    param = _make_param("test.backend", "string", enum=["a", "b", "c"])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "select"


def test_param_editor_list_type():
    param = _make_param("test.items", "list", default=[])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "input"


def test_param_editor_null_type():
    param = _make_param("test.empty", "null", default=None)
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "none"


def test_param_editor_enum_wins_over_string():
    param = _make_param("test.enum_str", "string", default="a", enum=["a", "b"])
    from hermes_help.tui.widgets.param_editor import _control_type_for_param
    assert _control_type_for_param(param) == "select"


def test_param_editor_compose_yields_widgets():
    """ParamEditor.compose() yields widgets for any param type."""
    for p in [
        _make_param("s", "string"),
        _make_param("i", "integer", default=0),
        _make_param("e", "string", enum=["a"]),
        _make_param("b", "boolean"),
        _make_param("n", "null"),
    ]:
        from hermes_help.tui.widgets.param_editor import ParamEditor
        editor = ParamEditor(p)
        widgets = list(editor.compose())
        assert len(widgets) >= 3  # header + meta + control + status


def test_param_editor_parse_value_int():
    from hermes_help.tui.widgets.param_editor import ParamEditor
    param = ParamDef(path="test.n", type="integer", default=0)
    editor = ParamEditor(param)
    assert editor._parse_value("42") == 42
    assert editor._parse_value("0") == 0


def test_param_editor_parse_value_float():
    from hermes_help.tui.widgets.param_editor import ParamEditor
    param = ParamDef(path="test.f", type="float", default=0.0)
    editor = ParamEditor(param)
    assert editor._parse_value("3.14") == 3.14


def test_param_editor_parse_value_string():
    from hermes_help.tui.widgets.param_editor import ParamEditor
    param = ParamDef(path="test.s", type="string", default="")
    editor = ParamEditor(param)
    assert editor._parse_value("hello") == "hello"


def test_param_editor_parse_value_none():
    from hermes_help.tui.widgets.param_editor import ParamEditor
    param = ParamDef(path="test.n", type="string", default="")
    editor = ParamEditor(param)
    assert editor._parse_value("") is None
    assert editor._parse_value("None") is None