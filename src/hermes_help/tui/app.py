"""Hermes Help TUI — interactive config browser (Textual).

Usage::
    uv run python -m hermes_help.tui.app
    uv run hermes-help-tui
"""
from __future__ import annotations

import logging

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static, Input
from textual.containers import Horizontal, Vertical
from textual import on

from hermes_help.schema.static import compile_from_hermes

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

    def __init__(self):
        super().__init__()
        self._schema = compile_from_hermes()

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

        self.query_one("#match-count", Static).update(
            f"Showing all {total_params} parameters"
        )

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
        """Show parameter detail on node selection."""
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

        lines = [
            f"[bold]{param.path}[/bold]",
            f"\nType: [italic]{param.type}[/italic]",
            f"Default: [dim]{param.default!r}[/dim]",
        ]

        if param.enum:
            lines.append(f"Allowed: {', '.join(str(e) for e in param.enum)}")

        if param.min_val is not None or param.max_val is not None:
            lo = param.min_val if param.min_val is not None else "∞"
            hi = param.max_val if param.max_val is not None else "∞"
            lines.append(f"Range: [{lo}, {hi}]")

        detail.update("\n".join(lines))


def main() -> None:
    """Entry point for hermes-help-tui."""
    app = HermesHelpApp()
    app.run()


if __name__ == "__main__":
    main()
