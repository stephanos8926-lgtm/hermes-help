# Phase 5 Spec: TUI Advanced Widgets

> **Version:** 1.0.0  
> **Date:** 2026-07-01  
> **Mode:** MEDIUM (plan-and-audit Phase 1)

## Goal

Upgrade the Hermes Help TUI from basic tree+detail to a fully interactive config browser with live search, inline type-aware editing, and config export.

## Problem

Current TUI (`hermes-help-tui`) has:
- Static tree that never filters — 464 params in a flat tree
- Detail panel is read-only — can't edit or validate values
- No export capability — the CLI stub command exists but TUI can't generate config

## Solution

Three interconnected features:

### Feature 1: Live Search/Filter
- Input at top of sidebar filters tree in real-time
- Match on param path, type, enum values, description
- Case-insensitive substring match (basic) with plan for fuzzy
- Preserves tree expand state when filtering
- Shows match count in status area

### Feature 2: Inline Type-Aware Editor
- When param selected, detail panel shows editable form:
  - **Strings**: `Input` widget
  - **Integers**: `Input` with numeric validation
  - **Floats**: `Input` with float validation
  - **Booleans**: `Select` with True/False options
  - **Enums**: `Select` with allowed values
  - **Lists**: `Input` showing repr
- Validation indicator icon (✓/✘) updates on each keystroke
- "Set" button applies the value to a temporary config preview

### Feature 3: Config Export Screen
- Modal Screen (pushed onto app)
- Multi-select section tree
- Live YAML preview as sections are checked
- Copy to clipboard button
- Write to file button (prompts for path)

## Files & Interfaces

| File | Action | Description |
|------|--------|-------------|
| `src/hermes_help/tui/app.py` | MODIFY | Add search handlers, enhanced detail, editor wiring |
| `src/hermes_help/tui/screens/export_screen.py` | CREATE | ExportScreen(ModalScreen) |
| `src/hermes_help/tui/widgets/param_editor.py` | CREATE | ParamEditor(Vertical) — inline editor |

## Acceptance Criteria

- [ ] Input filters tree in real-time (case-insensitive substring match)
- [ ] Detail panel shows editable form when param selected
- [ ] Validation indicator updates on each keystroke (✓ green / ✘ red)
- [ ] Select widget for enums shows all allowed values
- [ ] Export screen shows YAML preview that updates live
- [ ] Export writes valid YAML to file
- [ ] All existing 39 tests still pass
- [ ] Enter key submits/confirms edits
- [ ] Esc cancels editing / closes export modal
