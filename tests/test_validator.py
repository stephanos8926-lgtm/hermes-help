"""Tests for the config validator."""
import pytest

from hermes_help.schema.static import SchemaCompiler
from hermes_help.schema.dynamic import ConfigMap
from hermes_help.schema.validator import Validator, ValidationResult


@pytest.fixture
def schema():
    return SchemaCompiler({
        "terminal": {
            "backend": "local",
            "timeout": 180,
        },
        "display": {
            "interface": "cli",
            "compact": False,
        },
        "compression": {
            "enabled": True,
            "threshold": 0.5,
        },
    }).compile()


def test_validate_correct_config(schema):
    """Valid config yields no errors."""
    config = ConfigMap(
        raw={},
        flat={
            "terminal.backend": "docker",
            "terminal.timeout": 300,
            "display.interface": "tui",
            "compression.enabled": True,
            "compression.threshold": 0.6,
        },
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert result.is_valid


def test_validate_type_error(schema):
    """Wrong type produces an error."""
    config = ConfigMap(
        raw={},
        flat={"terminal.timeout": "not_a_number"},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Expected integer, got str" in e.message for e in result.errors)


def test_validate_enum_error(schema):
    """Value outside enum produces an error."""
    config = ConfigMap(
        raw={},
        flat={"terminal.backend": "invalid_backend"},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Value must be one of" in e.message for e in result.errors)


def test_validate_range_below_min(schema):
    """Value below minimum produces an error."""
    config = ConfigMap(
        raw={},
        flat={"terminal.timeout": 0},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Below minimum" in e.message for e in result.errors)


def test_validate_range_above_max(schema):
    """Value above maximum produces an error."""
    config = ConfigMap(
        raw={},
        flat={"terminal.timeout": 1000},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert not result.is_valid
    assert any("Above maximum" in e.message for e in result.errors)


def test_validate_unknown_key(schema):
    """Unknown keys produce a warning (not error)."""
    config = ConfigMap(
        raw={},
        flat={"nonexistent.key": "value", "terminal.backend": "local"},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    assert result.is_valid  # Unknown keys are only warnings
    assert any("Unknown config key" in w.message for w in result.warnings)


def test_validate_boolean_type(schema):
    """Booleans are validated correctly."""
    config = ConfigMap(
        raw={},
        flat={"display.compact": "yes", "display.interface": "cli"},
        source_path="test.yaml",
    )
    validator = Validator(schema)
    result = validator.validate(config)
    # 'yes' is a string, not boolean
    assert not result.is_valid


def test_single_value_validation_ok(schema):
    """validate_value on a correct value returns empty list."""
    validator = Validator(schema)
    issues = validator.validate_value("terminal.backend", "docker")
    assert issues == []


def test_single_value_validation_error(schema):
    """validate_value on an incorrect value returns issues."""
    validator = Validator(schema)
    issues = validator.validate_value("terminal.backend", "mars")
    assert len(issues) > 0
    assert issues[0].severity == "error"


def test_validation_result_all_clear(schema):
    """ValidationResult.summary on valid result."""
    result = ValidationResult()
    assert result.is_valid
    assert "all clear" in result.summary


def test_validation_result_with_errors(schema):
    """ValidationResult.summary with errors."""
    from hermes_help.schema.validator import ValidationIssue
    result = ValidationResult(
        errors=[ValidationIssue("test", "error", "test error")]
    )
    assert not result.is_valid
    assert "error" in result.summary.lower()
