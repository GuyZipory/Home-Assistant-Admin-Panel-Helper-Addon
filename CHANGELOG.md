# Changelog

All notable changes to this project will be documented in this file.

## [1.1.3] - 2025-11-25

### Fixed
- Remove `ingress_entry: /api` to fix path routing through ingress
- Ingress requests now reach correct endpoints without path prefix issues

## [1.1.2] - 2025-11-25

### Fixed
- Add debugging to catch-all route to diagnose path routing issues through ingress
- Log requested paths and headers when endpoint not found

## [1.1.1] - 2025-11-25

### Fixed
- Trust Home Assistant ingress authentication (X-Ingress-Path header)
- Skip IP whitelist checks for ingress requests (already authenticated by HA)
- Allow ingress requests to bypass addon authentication

## [1.1.0] - 2025-11-25

### Added
- **Home Assistant Token Authentication**: Support for HA long-lived access tokens
- **Dual Authentication Mode**: Choose between `api_key`, `homeassistant`, or `both` auth modes
- **Ingress API Access**: Use addon through Nabu Casa ingress without exposing ports
- Validate HA tokens against Home Assistant's API
- `auth_mode` configuration option

### Changed
- Enable `auth_api` and `homeassistant_api` in config for HA token validation
- Updated authentication middleware to support both auth methods
- Added `ingress_entry: /api` for cleaner ingress paths

## [1.0.3] - 2025-11-25

### Fixed
- Fixed SUPERVISOR_TOKEN not being injected by using proper S6 service scripts
- Integrated with Home Assistant's S6 overlay instead of bypassing it
- Added bashio logging for better integration with HA

## [1.0.2] - 2025-11-25

### Changed
- Print ALL environment variables for debugging
- Don't exit if SUPERVISOR_TOKEN not found, attempt to continue
- Better debugging output

## [1.0.1] - 2025-11-25

### Fixed
- Improved SUPERVISOR_TOKEN detection to check multiple sources (SUPERVISOR_TOKEN, HASSIO_TOKEN, /run/secrets/)
- Added detailed debugging when token is not found
- Better error messages with troubleshooting steps

## [1.0.0] - 2024-01-15

### Added
- Initial release
- API key authentication with key rotation support
- IP whitelisting support
- Rate limiting (per minute and per hour)
- Comprehensive audit logging
- Emergency disable kill switch
- Endpoint whitelist for security
- Supervisor API proxy for addon management endpoints:
  - GET /addons - List all addons
  - GET /addons/<slug> - Get addon info
  - POST /addons/<slug>/update - Update addon
  - POST /addons/<slug>/start - Start addon
  - POST /addons/<slug>/stop - Stop addon
  - POST /addons/<slug>/restart - Restart addon
- Key management endpoints:
  - POST /manage/generate-key - Generate new API keys
  - POST /manage/rotate-key - Rotate keys with grace period
  - POST /manage/auto-rotate - One-click automatic rotation
  - POST /manage/revoke-key - Revoke keys immediately
  - GET /manage/list-keys - List all keys with metadata
  - GET /manage - Web UI for key management
- Multi-architecture support (amd64, aarch64, armhf, armv7, i386)
- Configurable log levels
- Health check endpoint (GET /health)
- IP detection endpoint (GET /my-ip) - Shows your IP for whitelist setup

### Security
- All requests require valid API key
- IP whitelisting prevents unauthorized networks
- Rate limiting prevents brute force attacks
- All access attempts logged with client IP
- Emergency disable for instant shutdown
