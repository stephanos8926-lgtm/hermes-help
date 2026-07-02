# Reverse Audit — Phase 5: TUI Advanced Widgets

> **Date:** 2026-07-01  
> **Status:** Completed

## Gap Analysis

### 🔴 Critical

| # | Gap | Impact | Resolution |
|---|-----|--------|------------|
| 1 | `TreeNode.remove()` in `_rebuild_tree()` may raise if called on a node already removed by the `clear()` | Crash when filtering then clearing search | Use `tree.clear()` first, then only `add()` during rebuild — never call `remove()` after `clear()` |

### 🟠 High

| # | Gap | Impact | Resolution |
|---|-----|--------|------------|
| 2 | ParamEditor needs to handle `None`/`null` type params gracefully | Crash on params with `type: null` | Add guard in ParamEditor — show "No value type" message instead of rendering input |
| 3 | Input `on_change` fires on every keystroke — rapid typing could cause multiple rebuilds per second | Janky UX on 464-param tree | Debounce with `set_timer(0.1)` pattern, or accept rapid rebuilds (each is ~2ms, fine for 464 nodes) |

### 🟡 Medium

| # | Gap | Impact | Resolution |
|---|-----|--------|------------|
| 4 | No graceful handling if `compile_from_hermes()` returns `None` in TUI | Blank app with no tree | Already handled — shows error message in detail panel |
| 5 | Export screen needs to avoid writing files outside cwd | Security: path traversal in file save dialog | Sanitize user-provided paths in export flow |
| 6 | No keyboard shortcuts documented for TUI | Hard to discover Esc/Enter/Slash behavior | Add `BINDINGS` dict in app |

### 🟢 Low

| # | Gap | Impact | Resolution |
|---|-----|--------|------------|
| 7 | Param list doesn't show which values are user-set vs defaults | Reduced usefulness | Future enhancement: read `~/.hermes/config.yaml` and show ✓/✘ next to params |
| 8 | No multi-select in tree | Can't compare params | Future enhancement |

## Summary

- **Critical:** 1 — `remove()` vs `clear()` race → fix: rebuild never calls `remove` after `clear`
- **High:** 2-3 — null type handling, potential jank
- **Medium:** 4-6 — keyboard bindings, path safety
- **Low:** 7-8 — future features

Overall: Spec is sound, implementation path is correct, no blockers.
