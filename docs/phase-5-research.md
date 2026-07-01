# Phase 5 Research: TUI Advanced Widgets

> **Date:** 2026-07-01  
> **Mode:** MEDIUM (plan-and-audit Phase 0)  
> **Sources:** textual-framework-patterns skill, Textual docs, textual-widgets package

## Research Summary

### 1. Live Search/Filter

**Approach:** Input widget + `Tree.filter()` or manual node visibility toggling

**Best option:** Input `on_change` handler that walks all tree nodes and sets `tree_node.visible` based on fuzzy match against label.

**Key Textual API:**
- `Input.Changed` message — fires on every keystroke
- `Tree.clear()` + repopulate on filter — simple but resets expand state
- Better: iterate nodes, set `node.visible = bool(match)` — preserves expand state

```python
@on(Input.Changed, "#search-input")
def on_search_changed(self, event: Input.Changed) -> None:
    query = event.value.strip().lower()
    tree = self.query_one("#config-tree", Tree)
    for node in tree.root.children:
        for child in node.children:
            child.visible = not query or query in child.label.plain.lower()
```

### 2. SearchInputWithHistory

The `textual-widgets` package (michaelblaess) provides a `SearchInputWithHistory` widget with:
- Live substring filter (case-insensitive) while typing
- Match highlighting in accent + bold
- Arrow keys / mouse to pick
- History persistence

### 3. Inline Type-Aware Editor

**Pattern:** When a param is selected, swap the Static detail panel for a form with:
- Label showing param name + type + current description
- Input widget (for string/int/float) or Select widget (for enums) or Checkbox (for booleans)
- Validation indicator (✓/✘) updating live via `Input.Changed` + `Validator.validate_value()`
- Preview showing what the YAML would look like

### 4. Config Export Screen

**Pattern:** Modal screen (`Screen.Modal`) with:
- Multi-select of sections/params to export
- Live YAML preview as the user checks/unchecks
- "Copy to clipboard" and "Write to file" actions

**Key Textual APIs:**
- `Screen` subclass as modal — `self.app.push_screen(ExportScreen())`
- `Select` widget for enum params
- `Input` for string/int/float with validation on change
- `on_input_submitted` for commit

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Search approach | Manual node visibility + `Input.Changed` | Preserves tree expand state, simple |
| Detail editor | Rich Textual form (not TextArea) | Type-aware: Select for enums, Input for strings, Checkbox for bools |
| Validation | Instant via `Validator.validate_value()` on each keystroke | Gives immediate feedback |
| Export | Modal screen with YAML preview | Clean UX, no accidental writes |
| Entry point | `hermes-help-tui` → `HermesHelpApp().run()` | Already established |

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/hermes_help/tui/app.py` | MODIFY | Add search, enhanced detail, inline editing |
| `src/hermes_help/tui/screens/export_screen.py` | CREATE | Export modal screen |
| `src/hermes_help/tui/widgets/param_editor.py` | CREATE | Inline type-aware editor widget |
| `src/hermes_help/tui/widgets/search_bar.py` | CREATE | Advanced search widget (optional wrapper) |
| `tests/test_tui.py` | CREATE | TUI tests |
