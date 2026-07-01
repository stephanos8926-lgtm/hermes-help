"""Static schema extraction from Hermes' DEFAULT_CONFIG."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from hermes_help.config import SCHEMA_VERSION

logger = logging.getLogger(__name__)


@dataclass
class ParamDef:
    """Definition of a single configuration parameter."""
    path: str
    type: str
    default: Any = None
    enum: list | None = None
    min_val: float | None = None
    max_val: float | None = None
    description: str = ""
    required: bool = False
    version_added: int = 1


@dataclass
class SectionDef:
    """Definition of a config section."""
    path: str
    children: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class CompiledSchema:
    """Complete compiled schema."""
    version: int
    params: dict[str, ParamDef]
    sections: dict[str, SectionDef]

    @property
    def param_count(self) -> int:
        return len(self.params)

    @property
    def section_count(self) -> int:
        return len(self.sections)


# ── Known enum sets extracted from DEFAULT_CONFIG ─────────────
KNOWN_ENUMS: dict[str, list] = {
    # Terminal
    "terminal.backend": ["local", "docker", "ssh", "modal", "singularity", "daytona"],
    "terminal.home_mode": ["auto", "real", "profile"],
    "terminal.container_persistent": [True, False],
    "terminal.persistent_shell": [True, False],
    "terminal.docker_run_as_host_user": [True, False],
    "terminal.auto_source_bashrc": [True, False],
    # Web
    "web.backend": ["", "bing", "searxng", "tavily", "exa"],
    "web.search_backend": ["", "searxng", "tavily", "exa"],
    "web.extract_backend": ["", "native", "jina", "firecrawl"],
    # Browser
    "browser.engine": ["auto", "lightpanda", "chrome"],
    "browser.dialog_policy": ["must_respond", "auto_dismiss", "auto_accept"],
    "browser.allow_private_urls": [True, False],
    "browser.record_sessions": [True, False],
    "browser.camofox.managed_persistence": [True, False],
    "browser.camofox.rewrite_loopback_urls": [True, False],
    # TTS
    "tts.provider": [
        "edge", "elevenlabs", "openai", "xai", "minimax",
        "mistral", "gemini", "neutts", "kittentts", "piper",
    ],
    # STT
    "stt.enabled": [True, False],
    "stt.provider": ["local", "groq", "openai", "mistral", "elevenlabs"],
    "stt.local.model": ["tiny", "base", "small", "medium", "large-v3"],
    "stt.openai.model": ["whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe"],
    "stt.mistral.model": ["voxtral-mini-latest", "voxtral-mini-2602"],
    "stt.elevenlabs.model_id": ["scribe_v2", "scribe_v1"],
    # Display
    "display.interface": ["cli", "tui"],
    "display.busy_input_mode": ["interrupt", "queue", "steer"],
    "display.tui_status_indicator": ["kaomoji", "emoji", "unicode", "ascii"],
    "display.language": ["en", "zh", "ja", "de", "es", "fr", "tr", "uk"],
    "display.final_response_markdown": ["render", "strip", "raw"],
    "display.reasoning_style": ["code", "blockquote", "subtext"],
    "display.memory_notifications": ["off", "on", "verbose"],
    "display.copy_shortcut": ["auto", "ctrl_c", "ctrl_shift_c", "disabled"],
    "display.persistent_output": [True, False],
    "display.inline_diffs": [True, False],
    "display.reasoning_full": [True, False],
    "display.tui_agents_nudge": [True, False],
    "display.tui_auto_resume_recent": [True, False],
    "display.credits_notices": [True, False],
    "display.turn_completion_explainer": [True, False],
    "display.file_mutation_verifier": [True, False],
    "display.bell_on_complete": [True, False],
    "display.streaming": [True, False],
    "display.show_cost": [True, False],
    "display.compact": [True, False],
    "display.interim_assistant_messages": [True, False],
    "display.tool_progress_command": [True, False],
    "display.tool_progress_grouping": ["accumulate", "separate"],
    "display.persist_prompts": [True, False],
    "display.resume_skip_tool_only": [True, False],
    # Agent
    "agent.tool_use_enforcement": ["auto", True, False],
    "agent.task_completion_guidance": [True, False],
    "agent.parallel_tool_call_guidance": [True, False],
    "agent.environment_probe": [True, False],
    "agent.coding_context": ["auto", "focus", "on", "off"],
    "agent.verify_on_stop": ["auto", True, False],
    "agent.image_input_mode": ["auto", "native", "text"],
    "agent.service_tier": ["", "default", "eco"],
    # Compression / Context
    "context.engine": ["compressor", "lcm", "dcp"],
    "compression.enabled": [True, False],
    "compression.abort_on_summary_failure": [True, False],
    "compression.in_place": [True, False],
    # Memory
    "memory.memory_enabled": [True, False],
    "memory.user_profile_enabled": [True, False],
    "memory.write_approval": [True, False],
    "memory.provider": ["", "openviking", "mem0", "hindsight", "holographic", "retaindb", "byterover"],
    # Delegation
    "delegation.inherit_mcp_toolsets": [True, False],
    "delegation.orchestrator_enabled": [True, False],
    "delegation.subagent_auto_approve": [True, False],
    # Approvals
    "approvals.mode": ["manual", "smart", "off"],
    "approvals.cron_mode": ["deny", "approve"],
    "approvals.mcp_reload_confirm": [True, False],
    "approvals.destructive_slash_confirm": [True, False],
    # Security
    "security.allow_private_urls": [True, False],
    "security.redact_secrets": [True, False],
    "security.tirith_enabled": [True, False],
    "security.tirith_fail_open": [True, False],
    "security.allow_lazy_installs": [True, False],
    # Curator
    "curator.enabled": [True, False],
    "curator.consolidate": [True, False],
    "curator.prune_builtins": [True, False],
    "curator.backup.enabled": [True, False],
    # Checkpoints
    "checkpoints.enabled": [True, False],
    "checkpoints.auto_prune": [True, False],
    "checkpoints.delete_orphans": [True, False],
    # Cron
    "cron.wrap_response": [True, False],
    "cron.mirror_delivery": [True, False],
    # Kanban
    "kanban.dispatch_in_gateway": [True, False],
    "kanban.auto_decompose": [True, False],
    # Code execution
    "code_execution.mode": ["project", "strict"],
    # Tools
    "tools.tool_search.enabled": ["auto", "on", "off"],
    # Gateway
    "gateway.strict": [True, False],
    "gateway.message_timestamps.enabled": [True, False],
    # Streaming
    "streaming.enabled": [True, False],
    "streaming.transport": ["auto", "draft", "edit", "off"],
    # Sessions
    "sessions.auto_prune": [True, False],
    "sessions.vacuum_after_prune": [True, False],
    "sessions.write_json_snapshots": [True, False],
    # Logging
    "logging.level": ["DEBUG", "INFO", "WARNING"],
    # Privacy
    "privacy.redact_pii": [True, False],
    # Network
    "network.force_ipv4": [True, False],
    # Human delay
    "human_delay.mode": ["off", "fixed", "realistic", "uniform"],
    # Skills
    "skills.template_vars": [True, False],
    "skills.inline_shell": [True, False],
    "skills.guard_agent_created": [True, False],
    "skills.write_approval": [True, False],
    # Dashboard
    "dashboard.show_token_analytics": [True, False],
    "dashboard.theme": ["default", "midnight", "ember", "mono", "cyberpunk", "rose"],
    # Model catalog
    "model_catalog.enabled": [True, False],
    # Hooks
    "hooks_auto_accept": [True, False],
    # TTS providers
    "tts.gemini.audio_tags": [True, False],
    "tts.edge.voice": [
        "en-US-AriaNeural", "en-US-JennyNeural", "en-US-AndrewNeural",
        "en-US-BrianNeural", "en-US-SoniaNeural",
    ],
    "tts.gemini.voice": ["Kore", "Puck", "Seren", "Skye"],
    "tts.openai.voice": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
    "tts.neutts.device": ["cpu", "cuda", "mps"],
    # Browser platforms
    "browser.auto_local_for_private_urls": [True, False],
    # Slack
    "slack.require_mention": [True, False],
    # Discord
    "discord.require_mention": [True, False],
    "discord.thread_require_mention": [True, False],
    "discord.history_backfill": [True, False],
    "discord.reactions": [True, False],
    "discord.voice_fx.enabled": [True, False],
    "discord.allow_any_attachment": [True, False],
    "discord.voice_fx.ambient_enabled": [True, False],
    "discord.voice_fx.ack_enabled": [True, False],
    # Telegram
    "telegram.reactions": [True, False],
    "telegram.extra.rich_messages": [True, False],
    "telegram.extra.rich_drafts": [True, False],
    # Mattermost
    "mattermost.require_mention": [True, False],
    # Matrix
    "matrix.require_mention": [True, False],
    # Voice
    "voice.auto_tts": [True, False],
    "voice.beep_enabled": [True, False],
    # Bedrock
    "bedrock.discovery.enabled": [True, False],
    # Goals
    "goals.max_turns": list(range(1, 101)),
    # Plugin
    "curator.prune_builtins": [True, False],
    # Tool loop guardrails
    "tool_loop_guardrails.warnings_enabled": [True, False],
    "tool_loop_guardrails.hard_stop_enabled": [True, False],
    # MOA
    "moa.presets.default.enabled": [True, False],
    # Prompt caching
    "prompt_caching.cache_ttl": ["5m", "1h"],
    # OpenRouter
    "openrouter.response_cache": [True, False],
}

# ── Known numeric ranges extracted from DEFAULT_CONFIG ────────
KNOWN_RANGES: dict[str, tuple[float | None, float | None]] = {
    # Terminal
    "terminal.timeout": (1, 600),
    "terminal.container_cpu": (0.5, 64),
    "terminal.container_memory": (256, 131072),
    "terminal.container_disk": (1024, 1_000_000),
    "terminal.daemon_term_grace_seconds": (0, 30),
    # Agent
    "agent.max_turns": (1, 500),
    "agent.gateway_timeout": (0, 36000),
    "agent.restart_drain_timeout": (0, 3600),
    "agent.api_max_retries": (0, 10),
    "agent.gateway_timeout_warning": (0, 36000),
    "agent.clarify_timeout": (0, 36000),
    "agent.gateway_notify_interval": (0, 3600),
    "agent.gateway_auto_continue_freshness": (0, 86400),
    # Compression
    "compression.threshold": (0.1, 1.0),
    "compression.target_ratio": (0.05, 1.0),
    "compression.protect_last_n": (0, 200),
    "compression.protect_first_n": (0, 20),
    "compression.hygiene_hard_message_limit": (10, 50000),
    # Memory
    "memory.memory_char_limit": (100, 50000),
    "memory.user_char_limit": (100, 30000),
    # Delegation
    "delegation.max_iterations": (1, 500),
    "delegation.max_concurrent_children": (1, 20),
    "delegation.max_spawn_depth": (1, 10),
    "delegation.child_timeout_seconds": (0, 36000),
    "delegation.reasoning_effort": (None, None),
    # Checkpoints
    "checkpoints.max_snapshots": (1, 200),
    "checkpoints.max_total_size_mb": (0, 100000),
    "checkpoints.max_file_size_mb": (0, 100000),
    "checkpoints.retention_days": (1, 365),
    "checkpoints.min_interval_hours": (1, 720),
    # Browser
    "browser.inactivity_timeout": (10, 3600),
    "browser.command_timeout": (5, 120),
    "browser.dialog_timeout_s": (30, 600),
    # Display
    "display.resume_exchanges": (1, 200),
    "display.resume_max_user_chars": (50, 10000),
    "display.resume_max_assistant_chars": (50, 5000),
    "display.resume_max_assistant_lines": (1, 100),
    "display.cli_refresh_interval": (0.0, 60.0),
    "display.ephemeral_system_ttl": (0, 3600),
    # Streaming
    "streaming.edit_interval": (0.1, 10.0),
    "streaming.buffer_threshold": (1, 500),
    "streaming.fresh_final_after_seconds": (0.0, 300.0),
    # Cron
    "cron.output_retention": (0, 500),
    "cron.max_parallel_jobs": (1, 100),
    # Kanban
    "kanban.dispatch_interval_seconds": (5, 600),
    "kanban.failure_limit": (1, 20),
    "kanban.worker_log_rotate_bytes": (65536, 100_000_000),
    "kanban.worker_log_backup_count": (0, 10),
    "kanban.auto_decompose_per_tick": (1, 50),
    "kanban.dispatch_stale_timeout_seconds": (60, 259200),
    # Sessions
    "sessions.retention_days": (1, 730),
    "sessions.min_interval_hours": (1, 720),
    # Logging
    "logging.max_size_mb": (1, 500),
    "logging.backup_count": (0, 50),
    # Curator
    "curator.interval_hours": (1, 720),
    "curator.min_idle_hours": (0, 72),
    "curator.stale_after_days": (1, 365),
    "curator.archive_after_days": (1, 730),
    "curator.backup.keep": (1, 50),
    # MCP
    "mcp_discovery_timeout": (0.1, 30.0),
    # Tool output
    "tool_output.max_bytes": (1000, 1_000_000),
    "tool_output.max_lines": (50, 10000),
    "tool_output.max_line_length": (50, 100000),
    # Gateway
    "gateway.max_inbound_media_bytes": (0, 5_000_000_000),
    "gateway.trust_recent_files_seconds": (0, 86400),
    "gateway.scale_to_zero.idle_timeout_minutes": (1, 60),
    # Read file
    "file_read_max_chars": (1000, 5_000_000),
    "context_file_max_chars": (1000, 2_000_000),
    # Model catalog
    "model_catalog.ttl_hours": (0, 720),
    # Security
    "security.tirith_timeout": (1, 60),
    # Voice
    "voice.silence_threshold": (0, 32767),
    "voice.silence_duration": (0.5, 30.0),
    "voice.max_recording_seconds": (5, 600),
    # Human delay
    "human_delay.min_ms": (0, 10000),
    "human_delay.max_ms": (0, 30000),
    # TTS
    "tts.gemini.persona_prompt_file": (None, None),
    # API server
    "gateway.api_server.max_concurrent_runs": (0, 1000),
    # Search
    "tools.tool_search.threshold_pct": (1, 50),
    "tools.tool_search.search_default_limit": (1, 50),
    "tools.tool_search.max_search_limit": (1, 50),
    # Bedrock
    "bedrock.discovery.refresh_interval": (60, 86400),
    # Goals
    "goals.max_turns": (1, 500),
    # Tool loop guardrails
    "tool_loop_guardrails.warn_after.exact_failure": (1, 20),
    "tool_loop_guardrails.warn_after.same_tool_failure": (1, 20),
    "tool_loop_guardrails.warn_after.idempotent_no_progress": (1, 20),
    "tool_loop_guardrails.hard_stop_after.exact_failure": (1, 50),
    "tool_loop_guardrails.hard_stop_after.same_tool_failure": (1, 50),
    "tool_loop_guardrails.hard_stop_after.idempotent_no_progress": (1, 50),
    # Display
    "display.persistent_output_max_lines": (10, 10000),
    "display.tool_preview_length": (0, 5000),
    # User message preview
    "display.user_message_preview.first_lines": (1, 20),
    "display.user_message_preview.last_lines": (1, 20),
}


class SchemaCompiler:
    """Extract a typed schema from Hermes' DEFAULT_CONFIG dict."""

    TYPE_MAP: dict[type, str] = {
        str: "string",
        int: "integer",
        float: "float",
        bool: "boolean",
        list: "list",
        dict: "dict",
        type(None): "null",
    }

    def __init__(self, default_config: dict | None = None):
        self._default_config = default_config

    def compile(self) -> CompiledSchema:
        """Walk DEFAULT_CONFIG and build a CompiledSchema."""
        config = self._default_config or {}
        params: dict[str, ParamDef] = {}
        sections: dict[str, SectionDef] = {}
        self._walk(config, "", params, sections)
        return CompiledSchema(
            version=SCHEMA_VERSION,
            params=params,
            sections=sections,
        )

    def _walk(
        self,
        data: dict,
        prefix: str,
        params: dict[str, ParamDef],
        sections: dict[str, SectionDef],
    ) -> None:
        """Recursively walk a nested dict, populating params and sections."""
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # ── Always a section node ──
                # Every dict is a section; its immediate scalar children are params.
                children = list(value.keys())
                full_children = [f"{path}.{c}" for c in children]

                sections[path] = SectionDef(
                    path=path,
                    children=full_children,
                    description=self._make_description(path, key),
                )

                # Recurse into child dicts
                self._walk(value, path, params, sections)
            else:
                # ── Leaf param ──
                param_type = self._infer_type(value)
                enum = KNOWN_ENUMS.get(path)
                rmin, rmax = KNOWN_RANGES.get(path, (None, None))
                params[path] = ParamDef(
                    path=path,
                    type=param_type,
                    default=value,
                    enum=enum,
                    min_val=rmin,
                    max_val=rmax,
                    description=self._make_description(path, key),
                )

    def _infer_type(self, value: Any) -> str:
        py_type = type(value)
        return self.TYPE_MAP.get(py_type, "unknown")

    @staticmethod
    def _make_description(path: str, key: str) -> str:
        """Generate a human-readable description from the path."""
        parts = path.replace("_", " ").split(".")
        return f"{parts[-1].title()} configuration" if len(parts) == 1 else ""


def load_default_config() -> dict | None:
    """Import DEFAULT_CONFIG from the installed Hermes package.

    Returns None if Hermes is not installed or can't be imported.
    """
    try:
        from hermes_cli.config import DEFAULT_CONFIG  # type: ignore[import-untyped]

        return DEFAULT_CONFIG
    except ImportError:
        logger.warning("Hermes Agent not installed — cannot load DEFAULT_CONFIG")
        return None


def compile_from_hermes() -> CompiledSchema | None:
    """Compile the schema from the installed Hermes DEFAULT_CONFIG.

    Falls back to bundled compiled_schema.json if Hermes is not installed.
    """
    config = load_default_config()
    if config is not None:
        compiler = SchemaCompiler(config)
        schema = compiler.compile()
        logger.info(
            "Compiled schema from Hermes: "
            f"{schema.param_count} params, {schema.section_count} sections"
        )
        return schema

    # Fallback: try bundled compiled_schema.json
    import json
    from pathlib import Path

    bundled = Path(__file__).parent.parent / "compiled_schema.json"
    if bundled.exists():
        with open(bundled) as f:
            data = json.load(f)
        return CompiledSchema(
            version=data["version"],
            params={k: ParamDef(**v) for k, v in data["params"].items()},
            sections={k: SectionDef(**v) for k, v in data["sections"].items()},
        )

    logger.warning("No Hermes install and no bundled schema found")
    return None
