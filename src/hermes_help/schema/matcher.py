"""Match user config values against the static schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hermes_help.schema import CompiledSchema, ParamDef
from hermes_help.schema.dynamic import ConfigMap


@dataclass
class MatchedParam:
    """A parameter with both schema definition and user value (if set)."""
    param: ParamDef
    user_value: Any = None
    is_set: bool = False
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class MatchedConfig:
    """Full matched result: schema × user config."""
    known: dict[str, MatchedParam]
    unknown: dict[str, Any]
    missing: dict[str, ParamDef]
    user_config: ConfigMap | None
    schema_version: int

    @property
    def modified_count(self) -> int:
        """Count of params where user value differs from default."""
        return sum(
            1 for p in self.known.values()
            if p.is_set and p.user_value != p.param.default
        )

    @property
    def same_count(self) -> int:
        """Count of params set to the default value."""
        return sum(
            1 for p in self.known.values()
            if p.is_set and p.user_value == p.param.default
        )

    @property
    def unset_count(self) -> int:
        """Count of schema-defined params not set by user."""
        return len(self.missing)

    @property
    def unknown_count(self) -> int:
        return len(self.unknown)


class ConfigMatcher:
    """Match a user ConfigMap against a CompiledSchema."""

    def __init__(self, schema: CompiledSchema, user: ConfigMap | None = None):
        self._schema = schema
        self._user = user

    def match(self) -> MatchedConfig:
        """Produce a merged view of user config vs schema."""
        known: dict[str, MatchedParam] = {}

        for path, param in self._schema.params.items():
            mp = MatchedParam(param=param)
            if self._user and path in self._user.flat:
                mp.user_value = self._user.flat[path]
                mp.is_set = True
            known[path] = mp

        unknown: dict[str, Any] = {}
        if self._user:
            for path, value in self._user.flat.items():
                if path not in self._schema.params:
                    unknown[path] = value

        missing: dict[str, ParamDef] = {
            path: param
            for path, param in self._schema.params.items()
            if not known[path].is_set
        }

        return MatchedConfig(
            known=known,
            unknown=unknown,
            missing=missing,
            user_config=self._user,
            schema_version=self._schema.version,
        )
