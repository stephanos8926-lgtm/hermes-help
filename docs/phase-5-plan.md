# Phase 5 Plan: TUI Advanced Widgets Implementation

> **Version:** 1.0.0  
> **Date:** 2026-07-01  
> **Mode:** MEDIUM (plan-and-audit Phase 2)

## Task 5.1: Live Search/Filter in Tree

**Files:** `src/hermes_help/tui/app.py`

**Steps:**
1. Add `on_input_changed` handler to `HermesHelpApp`
2. Filter tree by walking nodes and setting `.visible`
3. Show match count in status area
4. Verify: type in search, tree narrows, count updates

## Task 5.2: Inline Type-Aware Editor

**Files:**
- Create: `src/hermes_help/tui/widgets/param_editor.py`
- Modify: `src/hermes_help/tui/app.py`

**ParamEditor widget:**
- Takes a `ParamDef` + optional user value
- Renders: label, type badge, input field, validation indicator
- `Input` for strings/ints/floats, `Select` for enums, `Checkbox` for bools
- Validates on change via `Validator.validate_value()`
- When valid: shows green ✓ icon
- When invalid: shows red ✘ icon + error message
- "Set" button emits `ParamChanged` message

## Task 5.3: Export Screen

**Files:**
- Create: `src/hermes_help/tui/screens/export_screen.py`
- Modify: `src/hermes_help/tui/app.py`

**ExportScreen(ModalScreen):**
- Header with title + close button
- Left: section tree with checkboxes (use `Tree` with `TreeNode` glyph handling)
- Right: live YAML preview (`Static` updated on selection change)
- Footer: "Copy to clipboard" + "Write to file" buttons
- On file write: prompts for path via `Input` screen

## Task 5.4: Integration Tests

**Files:**
- Create: `tests/test_tui.py` (unit tests for ParamEditor)

**Tests:**
- `test_param_editor_string`: renders Input for string param
- `test_param_editor_enum`: renders Select for enum param
- `test_param_editor_boolean`: renders Select for bool param
- `test_param_editor_validation`: shows ✘ on invalid input

## Execution Order

| Step | Task | Est. |
|------|------|------|
| 1 | Search/filter in tree | ~15 min |
| 2 | ParamEditor widget + wiring | ~30 min |
| 3 | Export screen | ~30 min |
| 4 | Tests + commit | ~15 min |
