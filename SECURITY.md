# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in hermes-help, please do **not** open a public issue. Instead, send a private report to the project maintainer.

**Do not disclose the vulnerability publicly until it has been addressed.**

## Scope

hermes-help itself is a configuration helper tool. Security concerns would include:
- Accidental exposure of API keys or secrets in output
- Path traversal in file export functionality
- Injection through YAML deserialization

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Active development |
