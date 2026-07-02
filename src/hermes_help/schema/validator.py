"""Validate user config values against the typed schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hermes_help.schema import CompiledSchema, ParamDef
from hermes_help.schema.dynamic import ConfigMap


@dataclass
class ValidationIssue:
    """A single validation finding."""

    path: str
    severity: str
    message: str
    expected: str = ""
    actual: str = ""


@dataclass
class ValidationResult:
    """Result of a validation pass."""

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    infos: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def summary(self) -> str:
        parts = []
        if self.errors:
            parts.append(f"\033[31m{len(self.errors)} errors\033[0m")
        if self.warnings:
            parts.append(f"\033[33m{len(self.warnings)} warnings\033[0m")
        if self.infos:
            parts.append(f"{len(self.infos)} infos")
        return f"Validation: {', '.join(parts) if parts else '\033[32mall clear\033[0m'}"

    def print(self) -> None:
        """Print validation results to console."""
        for issue in self.errors:
            print(f"  \033[31m✘\033[0m {issue.path}: {issue.message}")
        for issue in self.warnings:
            print(f"  \033[33m⚠\033[0m {issue.path}: {issue.message}")
        for issue in self.infos:
            print(f"  \033[36mℹ\033[0m {issue.path}: {issue.message}")


class Validator:
    """Validate a user config against the compiled schema."""

    # Python type → schema type mapping
    _TYPE_CHECK: dict[str, type] = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "list": list,
        "dict": dict,
        "null": type(None),
    }

    def __init__(self, schema: CompiledSchema):
        self._schema = schema

    def validate(self, config: ConfigMap) -> ValidationResult:
        """Validate a full config against the schema."""
        result = ValidationResult()

        for path, value in config.flat.items():
            param = self._schema.params.get(path)
            if param is None:
                result.warnings.append(
                    ValidationIssue(
                        path=path,
                        severity="warning",
                        message="Unknown config key — not in schema",
                    )
                )
                continue
            self._check_param(path, value, param, result)

        return result

    def validate_value(self, path: str, value: Any) -> list[ValidationIssue]:
        """Validate a single value against its schema definition.

        Used by the TUI's inline editor for live validation.
        """
        param = self._schema.params.get(path)
        if param is None:
            return [
                ValidationIssue(
                    path=path,
                    severity="error",
                    message=f"Unknown config key: {path}",
                )
            ]
        result = ValidationResult()
        self._check_param(path, value, param, result)
        return result.errors + result.warnings

    def _check_param(
        self,
        path: str,
        value: Any,
        param: ParamDef,
        result: ValidationResult,
    ) -> None:
        """Run type, enum, and range checks on a single value."""
        # ── Type check ──
        expected_type = param.type
        py_type = self._TYPE_CHECK.get(expected_type)
        if py_type is not None and not isinstance(value, py_type):
            result.errors.append(
                ValidationIssue(
                    path=path,
                    severity="error",
                    message=f"Expected {expected_type}, got {type(value).__name__}",
                    expected=expected_type,
                    actual=type(value).__name__,
                )
            )
            return  # Stop: no further checks on wrong type

        # ── Enum check ──
        if param.enum is not None and value not in param.enum:
            result.errors.append(
                ValidationIssue(
                    path=path,
                    severity="error",
                    message=f"Value must be one of: {param.enum}",
                    expected=str(param.enum),
                    actual=str(value),
                )
            )

        # ── Range check (numeric only) ──
        if isinstance(value, (int, float)):
            if param.min_val is not None and value < param.min_val:
                result.errors.append(
                    ValidationIssue(
                        path=path,
                        severity="error",
                        message=f"Below minimum ({param.min_val})",
                        expected=f">= {param.min_val}",
                        actual=str(value),
                    )
                )
            if param.max_val is not None and value > param.max_val:
                result.errors.append(
                    ValidationIssue(
                        path=path,
                        severity="error",
                        message=f"Above maximum ({param.max_val})",
                        expected=f"<= {param.max_val}",
                        actual=str(value),
                    )
                )
