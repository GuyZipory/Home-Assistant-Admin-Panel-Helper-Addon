# Changelog

All notable changes to this project will be documented in this file.

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
