"""Hermes Help TUI — interactive config browser (Textual).

Usage::
    uv run python -m hermes_help.tui.app
    uv run hermes-help-tui
"""

from __future__ import annotations

import logging

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static, Tree

from hermes_help.schema.dynamic import ConfigReader
from hermes_help.schema.static import compile_from_hermes
from hermes_help.schema.validator import Validator
from hermes_help.tui.screens import ExportScreen
from hermes_help.tui.widgets.param_editor import ParamEditor

logger = logging.getLogger(__name__)


class HermesHelpApp(App):
    """Hermes config browser TUI."""

    TITLE = "Hermes Help"
    SUB_TITLE = "Config Browser"

    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 35%;
        min-width: 30;
        border: solid $border;
        height: 100%;
    }

    #main-panel {
        width: 65%;
        height: 100%;
    }

    #search-input {
        margin: 0 1;
        dock: top;
    }

    #match-count {
        height: 1;
        dock: top;
        text-align: center;
        color: $text-disabled;
    }

    #detail-panel {
        height: 100%;
        padding: 1;
    }

    Tree {
        height: 100%;
    }
    """

    BINDINGS = [
        ("e", "export", "Export"),
        ("slash", "focus_search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self._schema = compile_from_hermes()
        self._validator = Validator(self._schema) if self._schema else None
        self._user_config = ConfigReader().read()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(
                    placeholder="Search parameters...",
                    id="search-input",
                )
                yield Static(id="match-count")
                yield Tree("Config", id="config-tree")
            with Vertical(id="main-panel"):
                yield Static(id="detail-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Build schema tree on mount."""
        if self._schema is None:
            self.query_one("#detail-panel", Static).update(
                "Cannot load Hermes schema. Is Hermes installed?"
            )
            return

        tree = self.query_one("#config-tree", Tree)
        top_sections = sorted(
            [s for s in self._schema.sections.values() if "." not in s.path],
            key=lambda s: s.path,
        )

        total_params = 0
        for section in top_sections:
            branch = tree.root.add(section.path, expand=False)
            count = 0
            for child_path in section.children:
                param = self._schema.params.get(child_path)
                if param:
                    label = f"{param.path} ({param.type})"
                    if param.enum:
                        label += f" [{param.enum[0]}…]"
                    branch.add_leaf(label, data=param.path)
                    count += 1
                    total_params += 1
            branch.label = f"{section.path} ({count})"

        detail = self.query_one("#detail-panel", Static)
        detail.update(
            f"Hermes Help — {total_params} parameters across "
            f"{len(top_sections)} sections\n\n"
            "Select a parameter to view details.\n"
            "Use the search bar above to filter."
        )

        self.query_one("#match-count", Static).update(f"Showing all {total_params} parameters")

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Filter tree in real-time as user types."""
        query = event.value.strip().lower()
        self._rebuild_tree(query)

    def _rebuild_tree(self, query: str = "") -> None:
        """Rebuild the tree, optionally filtering by query."""
        if self._schema is None:
            return

        tree = self.query_one("#config-tree", Tree)
        tree.clear()

        total_params = 0
        visible_count = 0

        top_sections = sorted(
            [s for s in self._schema.sections.values() if "." not in s.path],
            key=lambda s: s.path,
        )

        for section in top_sections:
            branch = tree.root.add(section.path, expand=bool(query))
            count = 0
            branch_visible = False

            for child_path in section.children:
                param = self._schema.params.get(child_path)
                if param:
                    label = f"{param.path} ({param.type})"
                    if param.enum:
                        label += f" [{param.enum[0]}…]"

                    matches = not query or (
                        query in param.path.lower()
                        or query in param.type.lower()
                        or (param.enum and any(query in str(e).lower() for e in param.enum))
                        or query in str(param.default).lower()
                    )

                    if matches:
                        branch.add_leaf(label, data=param.path)
                        count += 1
                        visible_count += 1
                        branch_visible = True

                    total_params += 1

            if branch_visible:
                branch.label = f"{section.path} ({count})"
                if query:
                    branch.expand()
            elif query:
                branch.remove()

        count_widget = self.query_one("#match-count", Static)
        if query:
            count_widget.update(f"{visible_count} of {total_params} parameters match")
        else:
            count_widget.update(f"Showing all {total_params} parameters")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Show parameter detail or ParamEditor on node selection."""
        if not event.node.data:
            return

        path = event.node.data
        detail = self.query_one("#detail-panel", Static)

        if self._schema is None:
            return

        param = self._schema.params.get(path)
        if param is None:
            detail.update(f"Unknown key: {path}")
            return

        # Replace static detail with ParamEditor with user value
        user_val = None
        if self._user_config and path in self._user_config.flat:
            user_val = self._user_config.flat[path]
        editor = ParamEditor(param=param, current_value=user_val, validator=self._validator)
        detail.remove_children()
        detail.remove()
        # Mount the editor where the detail was
        main_panel = self.query_one("#main-panel")
        main_panel.mount(editor)

    def action_export(self) -> None:
        """Open the Export screen."""
        if self._schema is None:
            return
        self.push_screen(
            ExportScreen(self._schema.params, self._schema.sections),
            self._on_export_dismissed,
        )

    def _on_export_dismissed(self, result: dict | None) -> None:
        """Handle export screen dismissal."""
        if result is not None:
            self.notify("Config exported successfully", severity="information")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search = self.query_one("#search-input", Input)
        search.focus()


def main() -> None:
    """Entry point for hermes-help-tui."""
    app = HermesHelpApp()
    app.run()


if __name__ == "__main__":
    main()
