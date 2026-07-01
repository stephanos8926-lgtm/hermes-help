"""Schema compiler — extracts typed, hierarchical config schema from Hermes."""
# Re-export for convenient import
from hermes_help.schema import (  # noqa: F401
    SchemaCompiler,
    CompiledSchema,
    ParamDef,
    SectionDef,
    compile_from_hermes,
    load_default_config,
)
