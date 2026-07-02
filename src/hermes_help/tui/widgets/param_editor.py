"""ParamEditor widget — type-aware inline editor for Hermes config params."""
from __future__ import annotations

from typing import Any

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.widgets import Input, Select, Static
from textual.widget import Widget
from textual import on

from hermes_help.schema.static import ParamDef


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
    """Inline parameter editor with type-aware input and live validation.

    Renders different controls based on the param definition:
    - enum params → Select dropdown
    - boolean params → Select (True/False)
    - string/int/float params → Input field
    - null params → static non-editable label
    """

    DEFAULT_CSS = """
    ParamEditor {
        height: auto;
        padding: 1;
        border: solid $border;
    }

    ParamEditor #editor-header {
        text-style: bold;
        margin-bottom: 1;
    }

    ParamEditor #editor-meta {
        color: $text-disabled;
        margin-bottom: 1;
    }

    ParamEditor #editor-control {
        margin-bottom: 1;
    }

    ParamEditor #editor-status {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        param: ParamDef,
        current_value: Any = None,
        validator=None,
    ):
        super().__init__()
        self._param = param
        self._current_value = current_value
        self._validator = validator
        self._control_type = _control_type_for_param(param)

    def compose(self):
        yield Static(self._param.path, id="editor-header")
        meta = f"Type: {self._param.type}  Default: {self._param.default!r}"
        if self._param.enum:
            meta += f"  Options: {len(self._param.enum)}"
        yield Static(meta, id="editor-meta")

        if self._control_type == "select":
            options = [(str(v), v) for v in (self._param.enum or [])]
            initial = self._current_value if self._current_value is not None else self._param.default
            yield Select(options, value=initial, id="editor-control")
        elif self._control_type == "checkbox":
            initial = self._current_value if self._current_value is not None else self._param.default
            yield Select(
                [("True", True), ("False", False)],
                value=initial,
                id="editor-control",
            )
        elif self._control_type == "input":
            value = str(self._current_value) if self._current_value is not None else str(self._param.default or "")
            yield Input(value=value, id="editor-control")
        else:
            yield Static("(not editable — null type)", id="editor-control")

        yield Static(id="editor-status")

    @on(Input.Changed, "#editor-control")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Live-validate on every keystroke."""
        status = self.query_one("#editor-status", Static)
        parsed = self._parse_value(event.value)
        if self._validator:
            issues = self._validator.validate_value(self._param.path, parsed)
            if issues:
                status.update(f"\u274c {issues[0].message}")
            else:
                status.update(f"\u2705 Valid {self._param.type}")

    @on(Select.Changed, "#editor-control")
    def on_select_changed(self, event: Select.Changed) -> None:
        """Validate on selection change."""
        status = self.query_one("#editor-status", Static)
        if self._validator:
            issues = self._validator.validate_value(self._param.path, event.value)
            if issues:
                status.update(f"\u274c {issues[0].message}")
            else:
                status.update(f"\u2705 Valid")

    def action_cancel(self) -> None:
        """Cancel editing — remove the editor widget."""
        self.remove()

    def _parse_value(self, text: str) -> Any:
        """Parse a string back to the expected Python type for validation."""
        if not text or text == "None":
            return None
        try:
            if self._param.type == "integer":
                return int(text)
            if self._param.type == "float":
                return float(text)
        except ValueError:
            return text
        return text