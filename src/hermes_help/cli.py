"""hermes-help CLI — Click-based Hermes config helper."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

from hermes_help import __version__
from hermes_help.schema.dynamic import ConfigReader
from hermes_help.schema.matcher import ConfigMatcher
from hermes_help.schema.static import compile_from_hermes
from hermes_help.schema.validator import Validator

# ── Helpers ──


def _get_schema(*, exit_on_fail: bool = True):
    """Load schema, error and exit if unavailable."""
    schema = compile_from_hermes()
    if schema is None:
        click.echo(
            "✘ Cannot load Hermes DEFAULT_CONFIG.\n"
            "  Is Hermes Agent installed and hermes_cli importable?\n"
            "  Install: curl -fsSL https://raw.githubusercontent.com/..."
            "/NousResearch/hermes-agent/main/scripts/install.sh | bash",
            err=True,
        )
        if exit_on_fail:
            sys.exit(1)
    return schema


def _get_reader(path: str | None = None) -> ConfigReader:
    return ConfigReader(Path(path) if path else None)


def _read_config(reader: ConfigReader):
    """Read config, error and exit if missing."""
    config = reader.read()
    if config is None:
        click.echo(f"✘ Config not found at: {reader.path}", err=True)
        click.echo(
            "  Expected ~/.hermes/config.yaml or path argument.\n"
            "  Run `hermes setup` or create one manually.",
            err=True,
        )
        sys.exit(1)
    return config


def _auto_fix_config(config, result, schema):
    """Auto-fix trivial config issues (type mismatches, wrong enums).

    Writes corrected values back to config.yaml.
    """
    import shutil

    fixes = 0
    raw = config.raw

    for issue in result.errors:
        path = issue.path
        param = schema.params.get(path)
        if param is None:
            continue

        keys = path.split(".")
        # Navigate to the parent dict
        d = raw
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]

        current = d.get(keys[-1])

        # Fix type: string -> correct Python type
        if param.type == "boolean" and isinstance(current, str):
            d[keys[-1]] = current.lower() in ("true", "1", "yes")
            fixes += 1
            click.echo(f"  Fix: {path} → {d[keys[-1]]} (converted string to bool)")
        elif param.type == "integer" and isinstance(current, str):
            try:
                d[keys[-1]] = int(current)
                fixes += 1
                click.echo(f"  Fix: {path} → {d[keys[-1]]} (converted to int)")
            except ValueError:
                pass
        elif param.type == "float" and isinstance(current, str):
            try:
                d[keys[-1]] = float(current)
                fixes += 1
                click.echo(f"  Fix: {path} → {d[keys[-1]]} (converted to float)")
            except ValueError:
                pass

        # Fix enum: pick closest match if current is close
        if param.enum and current not in param.enum:
            lowered = {str(e).lower(): e for e in param.enum}
            if isinstance(current, str) and current.lower() in lowered:
                d[keys[-1]] = lowered[current.lower()]
                fixes += 1
                click.echo(f"  Fix: {path} → {d[keys[-1]]} (matched enum)")

    if fixes == 0:
        click.echo("  No auto-fixable issues found.")
        return

    # Backup and write
    config_path = Path(config.source_path)
    backup = config_path.with_suffix(".yaml.bak")
    shutil.copy2(config_path, backup)
    click.echo(f"  Backup saved: {backup}")

    import yaml

    with open(config_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True)
    click.echo(f"  {fixes} fix(es) applied to {config_path}")


# ── Commands ──


@click.group()
@click.version_option(version=__version__, prog_name="hermes-help")
def main():
    """hermes-help — Hermes Agent configuration helper.

    Validate, query, diff, and generate config files for Hermes Agent.
    Knows every configuration parameter, their types, enums, and ranges.
    """
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True), required=False, default=None)
@click.option("--verbose", "-v", is_flag=True, help="Show all checks including passing")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--fix", "do_fix", is_flag=True, help="Auto-fix trivial issues (type/enum mismatches)"
)
@click.option(
    "--watch", "do_watch", is_flag=True, help="Watch config file for changes and re-validate"
)
def validate(path: str | None, verbose: bool, as_json: bool, do_fix: bool, do_watch: bool) -> None:
    """Validate a Hermes config.yaml against the schema.

    PATH: path to config.yaml (default: ~/.hermes/config.yaml)
    """
    schema = _get_schema()
    reader = _get_reader(path)
    config = _read_config(reader)

    validator = Validator(schema)
    result = validator.validate(config)

    if as_json:
        import json

        click.echo(
            json.dumps(
                {
                    "is_valid": result.is_valid,
                    "errors": [{"path": e.path, "message": e.message} for e in result.errors],
                    "warnings": [{"path": w.path, "message": w.message} for w in result.warnings],
                    "infos": [{"path": i.path, "message": i.message} for i in result.infos],
                },
                indent=2,
            )
        )
        return

    if do_watch:
        import time
        from pathlib import Path as _Path

        config_path = _Path(path) if path else reader.path
        click.echo(f"Watching {config_path} for changes... (Ctrl+C to stop)")
        last_mtime = config_path.stat().st_mtime
        try:
            while True:
                time.sleep(2)
                current_mtime = config_path.stat().st_mtime
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    click.echo("\nFile changed — re-validating...")
                    reader = _get_reader(str(config_path))
                    config = reader.read()
                    if config:
                        new_result = validator.validate(config)
                        if new_result.is_valid:
                            click.echo("✔ Config is valid")
                        else:
                            new_result.print()
        except KeyboardInterrupt:
            click.echo("\nStopped.")

        return

    if result.is_valid and not verbose:
        click.echo("✔ Config is valid")
        click.echo(f"  {len(result.warnings)} warnings, {len(result.infos)} infos")
        return

    result.print()

    if do_fix and not result.is_valid:
        click.echo("\nAttempting auto-fix...")
        _auto_fix_config(config, result, schema)
        click.echo("Done. Re-run without --fix to verify.")

    if not result.is_valid:
        sys.exit(1)


@main.command()
@click.argument("key")
def query(key: str) -> None:
    """Show full documentation for a config key.

    KEY: dot-separated path (e.g. terminal.backend, compression.threshold)
    """
    schema = _get_schema()

    param = schema.params.get(key)
    section = schema.sections.get(key)

    if param is None and section is None:
        # Try to find similar keys
        similar = [p for p in schema.params if key in p]
        click.echo(f"✘ Unknown key: {key}")
        if similar:
            click.echo("\n  Did you mean?")
            for s in similar[:5]:
                click.echo(f"    • {s}")
        sys.exit(1)

    if param:
        click.echo(f"  Key:     \033[1m{param.path}\033[0m")
        click.echo(f"  Type:    {param.type}")
        click.echo(f"  Default: \033[90m{param.default!r}\033[0m")
        if param.enum:
            click.echo(f"  Allowed: {', '.join(str(e) for e in param.enum)}")
        if param.min_val is not None or param.max_val is not None:
            lo = param.min_val if param.min_val is not None else "∞"
            hi = param.max_val if param.max_val is not None else "∞"
            click.echo(f"  Range:   [{lo}, {hi}]")
        click.echo(f"  Required: {param.required}")
        if param.description:
            click.echo(f"\n  {param.description}")

    if section:
        click.echo(f"\n  Section: \033[1m{section.path}\033[0m")
        click.echo(f"  Children: {len(section.children)}")
        for child in section.children[:15]:
            click.echo(f"    • {child}")
        if len(section.children) > 15:
            click.echo(f"    \033[90m… and {len(section.children) - 15} more\033[0m")


@main.command()
@click.argument("path", type=click.Path(exists=True), required=False, default=None)
def diff(path: str | None) -> None:
    """Diff user config against schema defaults.

    PATH: path to config.yaml (default: ~/.hermes/config.yaml)
    """
    schema = _get_schema()
    reader = _get_reader(path)
    config = reader.read()

    if config is None:
        click.echo(f"Config not found at {reader.path} — showing schema only")
        matcher = ConfigMatcher(schema)
    else:
        matcher = ConfigMatcher(schema, config)

    matched = matcher.match()

    click.echo(f"Schema version: {matched.schema_version}")
    click.echo(f"Total parameters: {len(matched.known)}")
    click.echo()

    modified = [p for p in matched.known.values() if p.is_set and p.user_value != p.param.default]
    same = [p for p in matched.known.values() if p.is_set and p.user_value == p.param.default]

    if config and matched.unknown:
        click.echo(f"\033[33mUnknown keys: {len(matched.unknown)}\033[0m")
        for path in sorted(matched.unknown):
            click.echo(f"  ? {path}")

    if modified:
        click.echo(f"\n\033[36mModified: {len(modified)}\033[0m")
        for mp in sorted(modified, key=lambda p: p.param.path):
            click.echo(f"  ~ \033[1m{mp.param.path}\033[0m")
            click.echo(f"    default: \033[90m{mp.param.default!r}\033[0m")
            click.echo(f"    current: {mp.user_value!r}")

    if same:
        click.echo(f"\n\033[90mSet to default: {len(same)}\033[0m")

    click.echo(f"\n\033[90mNot set: {matched.unset_count}\033[0m")


@main.command()
@click.argument("shell", type=click.Choice(["bash", "zsh"]), default="bash")
def completions(shell: str) -> None:
    """Generate shell completion scripts.

    SHELL: bash or zsh

    Usage::
        eval "$(hermes-help completions bash)"
        hermes-help completions zsh > /usr/local/share/zsh/site-functions/_hermes-help
    """
    import click as _click

    ctx = _click.Context(main)
    if shell == "bash":
        print(_click.shell_completion.ShellCompletionForBash(main, ctx).source())
    else:
        print(_click.shell_completion.ShellCompletionForZsh(main, ctx).source())


@main.command()
@click.option("--section", "-s", help="Generate stub for a specific section only")
@click.option("--minimal", is_flag=True, help="Only required/important params")
@click.option("--output", "-o", type=click.Path(), help="Write to file instead of stdout")
@click.option("--clipboard", is_flag=True, help="Copy to clipboard (requires xclip or pbcopy)")
def stub(section: str | None, minimal: bool, output: str | None, clipboard: bool) -> None:
    """Generate a config.yaml stub with all (or some) parameters."""
    schema = _get_schema()

    result: dict = {}

    for path, param in schema.params.items():
        if section and not path.startswith(section):
            continue
        if minimal and not param.required:
            continue

        keys = path.split(".")
        d = result
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        if keys[-1] not in d:
            d[keys[-1]] = param.default

    output_yaml = yaml.dump(result, default_flow_style=False, allow_unicode=True)

    if clipboard:
        import subprocess as _sp

        try:
            _sp.run(["xclip", "-selection", "clipboard"], input=output_yaml.encode(), check=True)
            click.echo("Copied to clipboard")
        except FileNotFoundError:
            try:
                _sp.run(["pbcopy"], input=output_yaml.encode(), check=True)
                click.echo("Copied to clipboard")
            except FileNotFoundError:
                click.echo("Clipboard requires xclip (Linux) or pbcopy (macOS)")
    elif output:
        Path(output).write_text(output_yaml)
        click.echo(f"Written to {output}")
    else:
        click.echo(output_yaml)


@main.command()
def schema() -> None:
    """Show schema statistics."""
    schema = _get_schema()
    click.echo("\033[1mhermes-help Schema\033[0m")
    click.echo(f"  Version:   {schema.version}")
    click.echo(f"  Params:    {schema.param_count}")
    click.echo(f"  Sections:  {schema.section_count}")
    click.echo()

    # Group top-level sections
    top_sections = [s for s in schema.sections.values() if "." not in s.path]
    top_sections.sort(key=lambda s: s.path)

    click.echo("  Sections:")
    for sec in top_sections:
        child_params = sum(1 for c in sec.children if c in schema.params)
        child_sections = sum(1 for c in sec.children if c in schema.sections)
        click.echo(
            f"    \033[1m{sec.path}\033[0m — {child_params} params, {child_sections} sub-sections"
        )


@main.command()
@click.argument("key")
def doc(key: str) -> None:
    """Show expanded documentation for a config key.

    KEY: dot-separated path (e.g. terminal.backend)
    """
    # Same as query but with more detail
    query.callback(key)


@main.command()
def tui() -> None:
    """Launch the Hermes Help TUI config browser."""
    from hermes_help.tui.app import main as tui_main

    tui_main()


if __name__ == "__main__":
    main()
