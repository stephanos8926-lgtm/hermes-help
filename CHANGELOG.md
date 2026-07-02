# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-07-01

### Added
- CLI: `validate`, `query`, `diff`, `stub`, `schema` commands
- TUI: live search/filter, ParamEditor with type-aware controls, ExportScreen modal
- SchemaCompiler: extracts 464 params, 137 sections from Hermes DEFAULT_CONFIG
- ConfigReader: loads user config.yaml, flattens, masks secrets
- ConfigMatcher: merges user values with schema definitions
- Validator: type, enum, and range validation with structured results
- Plugin: `rapidwebs-help` auto-syncs schema after Hermes update, validates config
- CI/CD: GitHub Actions workflow (lint → format check → mypy → test)
- Docs: comprehensive SPEC.md, PLAN.md, Phase 5 deliverables
- 48 tests covering schema compilation, config reading, validation, matching, and TUI widgets
