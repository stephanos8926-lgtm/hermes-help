"""Type-aware parameter editor widget for Hermes Help TUI."""
from __future__ import annotations

from typing import Any

from textual.widgets import Static, Select
from textual.widgets._input import Input
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.binding import Binding
from textual.reactive import reactive

from hermes_help.schema.static import ParamDef
from hermes_help.schema.validator import Validator
from hermes_help.schema.static import compile_from_hermes


def _control_type_for_param(param: ParamDef) -> str:
    """Determine the TUI control type for a parameter definition.

    Returns one of: 'input', 'select', 'checkbox', 'none'.
    """
    if param.type == "null":
        return "none"
    if param.enum is not None and len(param.enum) > 0:
        return "select"
    if param.type == "boolean":
        return "checkbox"
    return "input"


class ParamEditor(Widget):
    """Inline parameter editor with type-aware input and live validation."""

    DEFAULT_CSS = """
    ParamEditor {
        height: auto;
        padding: 1;
    }

    ParamEditor #editor-label {
        text-style: bold;
        margin-bottom: 1;
    }

    ParamEditor #editor-type-badge {
        color: $text-disabled;
        margin-bottom: 1;
    }

    ParamEditor #editor-description {
        color: $text;
        margin-bottom: 1;
    }

    ParamEditor #editor-default {
        color: $text-disabled;
        margin-bottom: 1;
    }

    ParamEditor #editor-validation {
        height: 1;
        margin-top: 1;
    }

    ParamEditor #editor-control {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        param: ParamDef,
        current_value: Any = None,
        validator: Validator | None = None,
    ):
        super().__init__()
        self._param = param
        self._current_value = current_value
        self._validator = validator
        self._control_type = _control_type_for_param(param)

    def compose(self):
        yield Static(self._param.path, id="editor-label")
        yield Static(f"Type: {self._param.type}", id="editor-type-badge")
        if self._param.description:
            yield Static(self._param.description, id="editor-description")
        yield Static(f"Default: {self._param.default!r}", id="editor-default")

        if self._control_type == "select":
            options = []
            for val in (self._param.enum or []):
                label = str(val)
                options.append((label, val))
            yield Select(
                options,
                prompt="Choose a value...",
                id="editor-control",
                value=self._current_value if self._current_value is not None else self._param.default,
            )
        elif self._control_type == "checkbox":
            bool_options = [("True", True), ("False", False)]
            current = self._current_value if self._current_value is not None else self._param.default
            yield Select(
                bool_options,
                prompt="Select...",
                id="editor-control",
                value=current,
            )
        elif self._control_type == "input":
            value = str(self._current_value) if self._current_value is not None else str(self._param.default or "")
            yield Input(
                value=value,
                placeholder=f"Enter {self._param.type} value...",
                id="editor-control",
            )
        else:
            yield Static("(No editable value)", id="editor-control")

        yield Static(id="editor-validation")

    def action_cancel(self) -> None:
        """Cancel editing and return to detail view."""
        self.remove()

    def _validate(self, value: str) -> str:
        """Validate a string value against the param schema. Returns status icon + message."""
        if self._validator is None:
            return "\u2705"

        parsed = self._parse_value(value)
        issues = self._validator.validate_value(self._param.path, parsed)
        if not issues:
            return f"\u2705 Valid"
        return f"\u274c {issues[0].message}"

    def _parse_value(self, text: str) -> Any:
        """Parse a string back to the param's expected Python type."""
        if not text:
            return self._param.default
        if self._param.type == "integer":
            try:
                return int(text)
            except ValueError:
                return text
        if self._param.type == "float":
            try:
                return float(text)
            except ValueError:
                return text
        if self._param.type == "boolean":
            return text.lower() in ("true", "1", "yes")
        return text
