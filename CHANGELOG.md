# Changelog

All notable changes to the Supervisor Gateway API custom integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.3] - 2024-11-25

### Added
- Optional x-api-key header authentication for extra security layer
- Dual authentication support (HA token + optional x-api-key)
- Comprehensive security documentation and best practices

### Changed
- Improved supervisor token access handling
- Enhanced API documentation with security considerations
- Updated all documentation to reflect dual authentication

### Fixed
- Supervisor token retrieval from environment and hassio data
- Version consistency across all files

## [2.0.2] - 2024-11-25

### Fixed
- Supervisor token access issues in custom integration
- Token retrieval from environment variables and hassio integration data

## [2.0.1] - 2024-11-25

### Fixed
- TypeError when initializing API views
- Corrected view initialization without passing hass parameter

## [2.0.0] - 2024-11-25

### Added
- **Initial release**
- Clean API URLs through Home Assistant's native API
- Works through Nabu Casa without port forwarding
- Home Assistant long-lived token authentication
- API endpoints:
  - `GET /api/supervisor_gateway/` - API documentation
  - `GET /api/supervisor_gateway/health` - Health check (no auth)
  - `GET /api/supervisor_gateway/addons` - List all addons
  - `GET /api/supervisor_gateway/addons/{slug}` - Get addon info
  - `POST /api/supervisor_gateway/addons/{slug}/start` - Start addon
  - `POST /api/supervisor_gateway/addons/{slug}/stop` - Stop addon
  - `POST /api/supervisor_gateway/addons/{slug}/restart` - Restart addon
  - `POST /api/supervisor_gateway/addons/{slug}/update` - Update addon
- HACS support via custom repository
- Configuration via configuration.yaml
- Automatic Supervisor API proxying

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Breaking changes
- **MINOR** version: New features (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)
