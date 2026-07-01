"""Tests for the schema matcher."""
import pytest

from hermes_help.schema.static import SchemaCompiler
from hermes_help.schema.dynamic import ConfigMap
from hermes_help.schema.matcher import ConfigMatcher


@pytest.fixture
def schema():
    return SchemaCompiler({
        "terminal": {
            "backend": "local",
            "timeout": 180,
        },
        "display": {
            "interface": "cli",
        },
        "compression": {
            "enabled": True,
            "threshold": 0.5,
        },
    }).compile()


def test_match_all_defaults(schema):
    """All default values when user has no config."""
    matcher = ConfigMatcher(schema)
    matched = matcher.match()
    # terminal.backend, terminal.timeout, display.interface,
    # compression.enabled, compression.threshold = 5
    assert len(matched.known) == 5
    assert matched.modified_count == 0
    assert matched.same_count == 0  # None set
    assert matched.unset_count == 5  # None set
    assert matched.unknown_count == 0


def test_match_with_user_config(schema):
    """User values override defaults."""
    config = ConfigMap(
        raw={},
        flat={"terminal.backend": "docker"},
        source_path="test.yaml",
    )
    matcher = ConfigMatcher(schema, config)
    matched = matcher.match()

    # Check user override
    tp = matched.known["terminal.backend"]
    assert tp.is_set
    assert tp.user_value == "docker"

    # Check default still present
    tt = matched.known["terminal.timeout"]
    assert not tt.is_set
    assert tt.param.default == 180


def test_match_modified_count(schema):
    """Modified count is correct."""
    config = ConfigMap(
        raw={},
        flat={"terminal.backend": "docker", "terminal.timeout": 300},
        source_path="test.yaml",
    )
    matcher = ConfigMatcher(schema, config)
    matched = matcher.match()
    assert matched.modified_count == 2  # backend and timeout changed


def test_match_same_count(schema):
    """Same count tracks params set to default."""
    config = ConfigMap(
        raw={},
        flat={"terminal.backend": "local"},  # 'local' IS the default
        source_path="test.yaml",
    )
    matcher = ConfigMatcher(schema, config)
    matched = matcher.match()
    assert matched.same_count >= 1


def test_match_unknown_keys(schema):
    """Unknown user keys appear in .unknown."""
    config = ConfigMap(
        raw={},
        flat={"made.up.key": "value", "nonexistent": 42},
        source_path="test.yaml",
    )
    matcher = ConfigMatcher(schema, config)
    matched = matcher.match()
    assert "made.up.key" in matched.unknown
    assert "nonexistent" in matched.unknown
    assert matched.unknown_count == 2


def test_match_missing_keys(schema):
    """Missing keys are all schema keys not set by user."""
    config = ConfigMap(
        raw={},
        flat={"terminal.backend": "local"},
        source_path="test.yaml",
    )
    matcher = ConfigMatcher(schema, config)
    matched = matcher.match()
    assert "terminal.backend" not in matched.missing
    assert "terminal.timeout" in matched.missing
    assert matched.unset_count == 4
