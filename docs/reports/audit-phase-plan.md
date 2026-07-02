# hermes-help Audit — Phase Plan

> **Mode:** LOW (plan-and-audit)  
> **Rationale:** All issues are discrete, well-understood, <5 files each, no cross-cutting changes

---

## Phase 1: Easy Wins (~30 min)

| # | Task | Effort | Reason |
|---|------|--------|--------|
| 7 | Add `hermes-help tui` CLI subcommand | 5m | 4-line change, eliminates UX inconsistency |
| 1 | Fix ExportScreen path traversal | 10m | Single guard function, security-critical |
| 6 | Add shell completion script | 10m | Click built-in support, standard for CLI tools |
| 9 | Add `--output` + `--clipboard` to `stub` | 10m | Reuses existing `yaml.dump` |
| | **Total** | **~35m** | |

## Phase 2: Medium Value (~50 min)

| # | Task | Effort | Reason |
|---|------|--------|--------|
| 4 | TUI shows user's actual config values | 20m | Major UX upgrade, reads ConfigReader at startup |
| 5 | Add `validate --fix` command | 25m | Auto-corrects types/enums, saves manual editing |
| 8 | Add `validate --watch` | 15m | Uses inotify/polling for continuous validation |
| | **Total** | **~60m** | |

## Phase 3: Quality Gates (~60 min)

| # | Task | Effort | Reason |
|---|------|--------|--------|
| 2 | Plugin tests (0% → 80% coverage) | 30m | Critical — plugin silently breaks otherwise |
| 3 | TUI widget tests (26% → 70% coverage) | 30m | ParamEditor + ExportScreen rendering tests |
| | **Total** | **~60m** | |

**Grand total:** ~2.5 hours, 9 issues resolved, coverage 41% → ~65%
