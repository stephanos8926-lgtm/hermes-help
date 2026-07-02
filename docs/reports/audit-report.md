# hermes-help Audit Report

> **Date:** 2026-07-02  
> **Scope:** Security, quality, UX, features, tooling  
> **Baseline:** 48 tests, 41% coverage, 0 lint errors

---

## Issue 1: ExportScreen Path Traversal (🔴 Security)

**File:** `src/hermes_help/tui/screens/__init__.py`

**Problem:** The `on_input_submitted` handler writes YAML to any path the user types — no validation, no allowlist. A user could write to `~/.ssh/authorized_keys` or `/etc/cron.d/malicious`.

**Risk:** Medium (TUI is local-only, not exposed as a service, but the user could accidentally overwrite important files)

**Fix:** Validate the resolved path is within the user's home directory or cwd. Block paths containing `..` traversal.

**Effort:** ~10 min

---

## Issue 2: Plugin Test Coverage (🟠 Quality)

**File:** `~/.hermes/plugins/rapidwebs-help/__init__.py`

**Problem:** 103 lines of plugin code with **0% test coverage**. The plugin handles schema sync, config validation, and session-start checks — all critical paths. A breaking change to the schema compiler or Hermes source would silently fail.

**Risk:** High — plugin could silently stop working after a Hermes update, no tests catch it.

**Fix:** Add `tests/test_plugin.py` with unit tests for `_sync_schema()`, `_validate_config()`, `_on_session_start()`, `_format_age()`. Mock subprocess and file I/O.

**Effort:** ~30 min

---

## Issue 3: TUI Widget Coverage Gap (🟠 Quality)

**Files:** `src/hermes_help/tui/widgets/__init__.py` (26%), `src/hermes_help/tui/widgets/param_editor.py` (36%)

**Problem:** The ParamEditor and ExportScreen widgets have low test coverage. The existing 9 TUI tests only cover `_control_type_for_param()` — none test the widget rendering, validation callbacks, or ExportScreen logic.

**Risk:** Medium — widget refactoring could silently break rendering or validation.

**Fix:** Add tests for ParamEditor rendering (`Input` vs `Select` vs `Static`), validation indicator updates, ExportScreen `_build_export_dict()`.

**Effort:** ~30 min

---

## Issue 4: TUI Shows Only Schema Defaults, Not User's Actual Config (🟢 UX)

**File:** `src/hermes_help/tui/app.py`

**Problem:** When selecting a param in the TUI tree, the ParamEditor populates with the schema default value — not the value the user actually has in their `~/.hermes/config.yaml`. This makes the editor feel disconnected from reality.

**Fix:** Read `ConfigReader` on TUI startup, pass user values to ParamEditor. Show "default: X / your: Y" in the editor.

**Effort:** ~20 min

---

## Issue 5: No `hermes-help validate --fix` (🟢 Feature)

**File:** `src/hermes_help/cli.py`

**Problem:** The `validate` command identifies issues but can't fix them. Users must manually edit their `config.yaml` based on error messages.

**Fix:** Add `--fix` flag that auto-corrects:
- Wrong types (convert string "true" → boolean `True`)
- Wrong enum values (auto-select closest match)
- Missing required keys (add schema defaults)

**Effort:** ~25 min

---

## Issue 6: No Shell Completion Scripts (🟢 Tooling)

**Problem:** `hermes-help` has no shell completion support. Users must type full commands.

**Fix:** Add `hermes-help completions bash|zsh` that generates completion scripts. Click supports this natively via `click-shell-completion` or we can use the built-in `click.Command.shell_complete`.

**Effort:** ~10 min

---

## Issue 7: No `hermes-help tui` CLI Subcommand (🟢 UX)

**Problem:** The TUI is launched via `hermes-help-tui` (a separate binary), not as a CLI subcommand. This is inconsistent with tools like `npm` (`npm run`) or `go` (`go tool`).

**Fix:** Add `hermes-help tui` as a CLI subcommand that calls the same `HermesHelpApp.main()`.

**Effort:** ~5 min

---

## Issue 8: No `hermes-help validate --watch` (🟢 Feature)

**Problem:** No file watcher mode for continuous validation. The plugin validates on config changes but there's no CLI equivalent.

**Fix:** Add `--watch` flag to `validate` that uses `inotify` (or polling) to re-validate on file changes.

**Effort:** ~15 min

---

## Issue 9: No CLI Export / Copy-to-Clipboard (🟢 Feature)

**Problem:** The TUI can export config sections and copy YAML to clipboard, but the CLI can't. `hermes-help stub --section` outputs to stdout but can't target a file or clipboard.

**Fix:** Add `--output FILE` flag to `stub` command. Add `--clipboard` flag (uses `xclip`/`pbcopy`).

**Effort:** ~10 min

---

## Summary

| # | Issue | Category | Severity | Effort |
|---|-------|----------|----------|--------|
| 1 | ExportScreen path traversal | Security | 🔴 | 10m |
| 2 | Plugin 0% test coverage | Quality | 🟠 | 30m |
| 3 | TUI widget coverage gap | Quality | 🟠 | 30m |
| 4 | TUI shows defaults, not user config | UX | 🟢 | 20m |
| 5 | No `validate --fix` | Feature | 🟢 | 25m |
| 6 | No shell completions | Tooling | 🟢 | 10m |
| 7 | No `hermes-help tui` subcommand | UX | 🟢 | 5m |
| 8 | No `validate --watch` | Feature | 🟢 | 15m |
| 9 | CLI export/clipboard | Feature | 🟢 | 10m |

**Total estimated effort:** ~2.5 hours

**Coverage after fixes:** ~65% (from 41%)

**Risk reduction:** Plugin path secured, path traversal blocked, two major coverage gaps filled.
