# Changelog

All notable changes to the Supervisor Gateway API custom integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2025-11-26

### Added
- **Optional IP Whitelist**: New `ip_whitelist` configuration option for restricting API access to specific public IP addresses
  - Fully optional - backward compatible (if not configured or empty, all IPs are allowed)
  - Extracts real client IP from `X-Forwarded-For` and `X-Real-IP` headers (Nabu Casa compatible)
  - Returns 403 Forbidden for non-whitelisted IPs when configured
  - Applies to all protected addon management endpoints
  - Does not apply to `/health` and `/my-ip` endpoints
- **New `/my-ip` Endpoint**: Helper endpoint to discover your public IP address
  - Located at `/api/supervisor_gateway/my-ip`
  - Requires Home Assistant token only (no x-api-key needed for convenience)
  - Shows the client's public IP address extracted from proxy headers
  - Displays the source of the IP (X-Forwarded-For, X-Real-IP, or request.remote)
  - Helps users configure IP whitelist by discovering their current public IP

### Changed
- Enhanced security with optional IP-based access control
- Improved public IP detection for Nabu Casa cloud proxy compatibility
- Updated version to 3.1.0 across all files

### Technical Details
- Added `get_client_ip()` helper function for extracting public IP from headers
- Added `validate_ip_whitelist()` function for IP validation logic
- IP whitelist validation occurs before x-api-key validation in request flow
- Configuration schema supports optional `ip_whitelist` array of strings

## [3.0.0] - 2024-11-25

### ⚠️ BREAKING CHANGES

**x-api-key is now REQUIRED**
- The `api_key` configuration is now mandatory in `configuration.yaml`
- All API requests must include the `x-api-key` header
- Upgrading from 2.x requires adding `api_key` to your configuration

**Migration from 2.x:**
```yaml
# Add this to your configuration.yaml
supervisor_gateway:
  api_key: "your-long-random-string-here"
```

### Changed
- x-api-key authentication is now required (was optional)
- Configuration schema now requires `api_key` field
- API validation now rejects requests without x-api-key header
- Updated all documentation to reflect required authentication
- Enhanced security with mandatory dual authentication

### Rationale
This breaking change improves security by enforcing dual authentication for all installations, preventing accidental exposure of Supervisor API without proper protection.

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
