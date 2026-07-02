"""Schema compiler — extracts typed, hierarchical config schema from Hermes."""

# Re-export for convenient import
from hermes_help.schema import (  # noqa: F401
    CompiledSchema,
    ParamDef,
    SchemaCompiler,
    SectionDef,
    compile_from_hermes,
    load_default_config,
)
