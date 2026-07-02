"""Read user's config.yaml, flatten to dot-path map, mask secrets."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from hermes_help.config import SECRET_KEY_PATTERNS, get_config_path

logger = logging.getLogger(__name__)


@dataclass
class ConfigMap:
    """User's config as a flat path→value map with metadata."""

    raw: dict
    flat: dict[str, Any]
    source_path: str
    masked_keys: list[str] = field(default_factory=list)


class ConfigReader:
    """Read and flatten the user's ~/.hermes/config.yaml."""

    SECRET_PATTERNS = SECRET_KEY_PATTERNS

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else get_config_path()
        self._resolved: Path | None = None

    def read(self) -> ConfigMap | None:
        """Load, flatten, and mask secrets. Returns None if file missing."""
        resolved = self.path.expanduser().resolve()
        if not resolved.exists():
            logger.info(f"Config not found: {resolved}")
            return None
        self._resolved = resolved

        with open(resolved) as f:
            try:
                raw = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                logger.warning(f"YAML parse error in {resolved}: {exc}")
                return None

        flat: dict[str, Any] = {}
        masked: list[str] = []
        self._flatten(raw, "", flat, masked)

        return ConfigMap(
            raw=raw,
            flat=flat,
            source_path=str(resolved),
            masked_keys=masked,
        )

    def _flatten(
        self,
        data: dict,
        prefix: str,
        out: dict[str, Any],
        masked: list[str],
    ) -> None:
        """Recursively flatten nested dict to dot-path keys, masking secrets."""
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._flatten(value, path, out, masked)
            else:
                # Mask known secret patterns
                if any(p in key.lower() for p in self.SECRET_PATTERNS):
                    out[path] = "***MASKED***"
                    masked.append(path)
                else:
                    out[path] = value

    def __repr__(self) -> str:
        return f"ConfigReader({self.path})"
