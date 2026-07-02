"""Export screen — modal dialog for selecting sections and exporting YAML config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Header, Input, Static, Tree


def _validate_export_path(raw: str) -> Path | None:
    """Validate and resolve an export file path.

    Blocks path traversal and restricts writes to home directory.
    """
    if ".." in raw.split("/"):
        return None
    path = Path(raw).expanduser().resolve()
    try:
        path.relative_to(Path.home().resolve())
    except ValueError:
        return None
    return path


class ExportScreen(ModalScreen[dict | None]):
    """Modal screen for selecting config sections and exporting as YAML."""

    DEFAULT_CSS = """
    ExportScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    ExportScreen > #dialog {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
    }

    ExportScreen #export-header {
        dock: top;
        height: 3;
        content-align: center middle;
        text-style: bold;
    }

    ExportScreen #export-body {
        height: 1fr;
    }

    ExportScreen #section-tree {
        width: 40%;
        height: 100%;
        border-right: solid $border;
    }

    ExportScreen #preview-panel {
        width: 60%;
        height: 100%;
        padding: 1;
    }

    ExportScreen #export-preview {
        height: 1fr;
        border: solid $border;
        padding: 1;
        overflow-y: auto;
    }

    ExportScreen #export-footer {
        dock: bottom;
        height: 3;
        align: center middle;
    }

    ExportScreen Button {
        margin: 0 1;
    }
    """

    def __init__(self, schema_params: dict[str, Any], schema_sections: dict[str, Any]):
        super().__init__()
        self._params = schema_params
        self._sections = schema_sections
        self._selected: set[str] = set()
        self._section_list: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Export Config as YAML", id="export-header")
            with Horizontal(id="export-body"):
                with ScrollableContainer(id="section-tree"):
                    yield Tree("Sections", id="export-tree")
                with Vertical(id="preview-panel"):
                    yield Static("Preview:", id="preview-label")
                    yield Static("(select sections to preview)", id="export-preview")
            with Horizontal(id="export-footer"):
                yield Button("Select All", id="btn-select-all", variant="primary")
                yield Button("Deselect All", id="btn-deselect-all")
                yield Button("Copy to Clipboard", id="btn-copy", variant="primary")
                yield Button("Write to File", id="btn-write")
                yield Button("Cancel", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        """Build section tree from schema."""
        tree = self.query_one("#export-tree", Tree)
        root = tree.root

        top_sections = sorted(
            [s for s in self._sections.values() if "." not in s.path],
            key=lambda s: s.path,
        )

        for section in top_sections:
            param_count = sum(1 for c in section.children if c in self._params)
            label = f"[ ] {section.path} ({param_count} params)"
            root.add(label, data=section.path)
            self._section_list.append(section.path)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Toggle section selection on click."""
        if not event.node.data:
            return

        path: str = event.node.data

        if path in self._selected:
            self._selected.discard(path)
        else:
            self._selected.add(path)

        self._refresh_labels()
        self._update_preview()

    def _refresh_labels(self) -> None:
        """Update all tree node labels to reflect current selection."""
        tree = self.query_one("#export-tree", Tree)
        for node in tree.root.children:
            if node.data and isinstance(node.data, str):
                marker = "[x]" if node.data in self._selected else "[ ]"
                # Preserve the count from the original label
                label = str(node.label)
                if "(" in label:
                    rest = label.split("(", 1)[1]
                    node.label = f"{marker} {node.data} ({rest}"
                else:
                    node.label = f"{marker} {node.data}"

    def _build_export_dict(self) -> dict:
        """Build a nested YAML dict from selected sections."""
        result: dict = {}
        for section_path in sorted(self._selected):
            section = self._sections.get(section_path)
            if not section:
                continue
            section_data: dict = {}
            for child_path in section.children:
                param = self._params.get(child_path)
                if param:
                    keys = child_path.split(".")
                    current = section_data
                    for k in keys[1:-1]:  # Skip section root
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = param.default
            if section_data:
                result[section_path] = section_data
        return result

    def _update_preview(self) -> None:
        """Render the YAML preview."""
        preview = self.query_one("#export-preview", Static)
        data = self._build_export_dict()
        if not data:
            preview.update("(select sections to preview)")
            return
        yaml_text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        preview.update(yaml_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn_id = event.button.id

        if btn_id == "btn-cancel":
            self.dismiss(None)

        elif btn_id == "btn-select-all":
            self._selected = set(self._section_list)
            self._refresh_labels()
            self._update_preview()

        elif btn_id == "btn-deselect-all":
            self._selected.clear()
            self._refresh_labels()
            self._update_preview()

        elif btn_id == "btn-copy":
            data = self._build_export_dict()
            if data:
                import subprocess

                yaml_text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
                try:
                    subprocess.run(
                        ["xclip", "-selection", "clipboard"],
                        input=yaml_text.encode(),
                        check=True,
                    )
                    self.query_one("#preview-label", Static).update(
                        "Preview: (copied to clipboard)"
                    )
                except FileNotFoundError:
                    self.query_one("#preview-label", Static).update(
                        "Preview: (xclip not found — install or use Write to File)"
                    )

        elif btn_id == "btn-write":
            self._show_file_input()

    def _show_file_input(self) -> None:
        """Show a file path input below the preview."""
        existing = self.query_one("#export-path-input", default=None)
        if existing:
            existing.focus()
            return
        path_input = Input(
            placeholder="Enter path (e.g. ~/export.yaml)",
            id="export-path-input",
        )
        footer = self.query_one("#export-footer")
        footer.mount(path_input)
        path_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Write YAML to the specified file path."""
        if event.input.id == "export-path-input":
            raw = event.value.strip()
            if not raw:
                return
            validated = _validate_export_path(raw)
            if validated is None:
                self.query_one("#preview-label", Static).update(
                    "Preview: (path must be within home directory)"
                )
                return
            data = self._build_export_dict()
            if data:
                yaml_text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
                validated.write_text(yaml_text)
                self.query_one("#preview-label", Static).update(
                    f"Preview: (written to {validated})"
                )
                event.input.remove()
