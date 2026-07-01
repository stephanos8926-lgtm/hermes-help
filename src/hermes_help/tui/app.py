"""Hermes Help TUI — interactive config browser (Textual).

Usage::
    uv run python -m hermes_help.tui.app
    uv run hermes-help-tui
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static, Input
from textual.containers import Horizontal, Vertical


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

    #search-container {
        height: 3;
        dock: top;
        border-bottom: solid $border;
    }

    #search-input {
        margin: 0 1;
    }

    #detail-panel {
        height: 100%;
        padding: 1;
    }

    Tree {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(
                    placeholder="Search parameters...",
                    id="search-input",
                )
                yield Tree("Config", id="config-tree")
            with Vertical(id="main-panel"):
                yield Static(id="detail-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Build schema tree on mount."""
        from hermes_help.schema.static import compile_from_hermes

        schema = compile_from_hermes()
        if schema is None:
            self.query_one("#detail-panel", Static).update(
                "Cannot load Hermes schema. Is Hermes installed?"
            )
            return

        tree = self.query_one("#config-tree", Tree)
        root = tree.root

        # Build top-level section branches
        top_sections = sorted(
            [s for s in schema.sections.values() if "." not in s.path],
            key=lambda s: s.path,
        )

        for section in top_sections:
            branch = root.add(section.path, expand=False)
            # Add child params
            for child_path in section.children:
                param = schema.params.get(child_path)
                if param:
                    enum_tag = f" [{param.enum[0]}…]" if param.enum else ""
                    branch.add_leaf(
                        f"{param.path} ({param.type}{enum_tag})",
                        data=param.path,
                    )

        detail = self.query_one("#detail-panel", Static)
        detail.update(
            f"Hermes Help — {schema.param_count} parameters across "
            f"{len(top_sections)} sections\n\n"
            "Select a parameter from the left tree to view details."
        )

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Show parameter detail on node selection."""
        if not event.node.data:
            return  # Section node

        path = event.node.data
        detail = self.query_one("#detail-panel", Static)

        from hermes_help.schema.static import compile_from_hermes

        schema = compile_from_hermes()
        if schema is None:
            return

        param = schema.params.get(path)
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
