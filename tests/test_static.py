"""Tests for the static schema compiler."""

import pytest
from hermes_help.schema import SchemaCompiler, CompiledSchema, ParamDef, SectionDef


def test_compile_returns_compiled_schema(sample_schema):
    """SchemaCompiler.compile() returns a CompiledSchema."""
    assert isinstance(sample_schema, CompiledSchema)


def test_compile_param_count(sample_schema):
    """Compiling a 3-section config yields correct param count."""
    # terminal: 3, display: 2, compression: 2
    assert sample_schema.param_count == 7


def test_compile_section_count(sample_schema):
    """Compiling yields correct section count."""
    assert sample_schema.section_count == 3


def test_compile_terminal_backend(sample_schema):
    """terminal.backend is a string with known enum."""
    param = sample_schema.params["terminal.backend"]
    assert param.type == "string"
    assert param.default == "local"
    assert param.enum is not None
    assert "local" in param.enum


def test_compile_terminal_timeout(sample_schema):
    """terminal.timeout is integer with range bounds."""
    param = sample_schema.params["terminal.timeout"]
    assert param.type == "integer"
    assert param.default == 180
    assert param.min_val == 1
    assert param.max_val == 600


def test_compile_display_interface(sample_schema):
    """display.interface has enum set."""
    param = sample_schema.params["display.interface"]
    assert param.type == "string"
    assert param.default == "cli"
    assert "cli" in (param.enum or [])
    assert "tui" in (param.enum or [])


def test_compile_compression_enabled(sample_schema):
    """compression.enabled is boolean."""
    param = sample_schema.params["compression.enabled"]
    assert param.type == "boolean"
    assert param.default is True


def test_compile_section_has_children(sample_schema):
    """Sections list their child param paths."""
    terminal_section = sample_schema.sections["terminal"]
    assert len(terminal_section.children) >= 3
    assert "terminal.backend" in terminal_section.children
    assert "terminal.timeout" in terminal_section.children


def test_compile_empty_config():
    """Empty config yields empty schema."""
    compiler = SchemaCompiler({})
    schema = compiler.compile()
    assert schema.param_count == 0
    assert schema.section_count == 0


def test_compile_deep_nesting():
    """Params at 3+ levels of nesting are correctly extracted."""
    compiler = SchemaCompiler({
        "a": {
            "b": {
                "c": {"deep_param": True},
                "d": "value",
            }
        }
    })
    schema = compiler.compile()
    assert "a.b.c" in schema.sections
    assert "a.b.c.deep_param" in schema.params
    assert "a.b.d" in schema.params
    assert schema.params["a.b.c.deep_param"].type == "boolean"
    assert schema.params["a.b.d"].type == "string"


def test_compile_none_default():
    """None values are typed as 'null'."""
    compiler = SchemaCompiler({"null_option": None})
    schema = compiler.compile()
    assert schema.params["null_option"].type == "null"


def test_compile_numeric_params_get_ranges(sample_schema):
    """Numeric params get KNOWN_RANGES bounds when available."""
    param = sample_schema.params["terminal.timeout"]
    assert param.min_val is not None
    assert param.max_val is not None


def test_section_properties(sample_schema):
    """SectionDef has correct path, children, description."""
    sec = sample_schema.sections["terminal"]
    assert sec.path == "terminal"
    assert isinstance(sec.children, list)
