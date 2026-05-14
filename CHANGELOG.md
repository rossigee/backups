# Changelog

## v2.7.0

### New Features
- `sftp-folder` source type: backs up remote directories over SFTP using paramiko, streaming files directly into a tar archive with no intermediate copies
- Deb package build and publish to GitHub Releases on semver-tagged releases

### Enhancements
- OpenTelemetry span processor switched from `BatchSpanProcessor` to `SimpleSpanProcessor` so spans are exported before process exit
- Logging initialisation moved before OTEL setup so `-v`/`-d` flags apply to all output
- Added Dependabot for automated GitHub Actions and pip dependency updates
- Bumped all GitHub Actions to latest major versions (Node.js 24 compatible)

## v2.6.0

### New Features
- OpenTelemetry OTLP tracing support — optional tracing via `pip install backups[tracing]`, zero overhead when disabled
- Cloudflare Backup Registry notification driver for backup run reports
- Prometheus Pushgateway API key authentication support

### Enhancements
- Refactored Prometheus notification to use `requests.put` instead of `push_to_gateway`
- Added error handling for notification failures
- Restructured documentation into per-driver docs under `docs/` (sources, destinations, notifications, scheduling)
- Improved package metadata for deb packaging
- Pinned `grpcio>=1.80.0` for OTLP gRPC compatibility

### Bug Fixes
- Fixed Flagfile notification missing `notify_on_start` attribute
- Fixed `typeof` to `type` in error logging
- Updated `.gitignore` to exclude build artifacts

### Removals
- Removed HipChat notification driver (service discontinued)

## v2.5.0

- Initial release of the restructured backup orchestration tool
