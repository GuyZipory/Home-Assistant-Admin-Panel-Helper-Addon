# Supervisor Gateway API

**Clean API access to Home Assistant Supervisor through Nabu Casa - No ports, no ingress tokens!**

A Home Assistant custom integration that provides clean REST API access to Supervisor endpoints for managing addons remotely through your external dashboards.

## 🚀 Quick Start

### What You Get

- ✅ Clean URLs: `https://your-instance.ui.nabu.casa/api/supervisor_gateway/addons`
- ✅ No port forwarding needed
- ✅ Works through Nabu Casa automatically
- ✅ Simple authentication with HA tokens
- ✅ Optional extra security with x-api-key
- ✅ Manage addons from external dashboards

### Install via HACS

1. Open **HACS** → **Integrations**
2. Click **⋮** → **Custom repositories**
3. Add: `https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon`
4. Category: **Integration**
5. Download "**Supervisor Gateway API**"
6. Add to `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-key"  # Optional for extra security
   ```
7. Restart Home Assistant

**[📖 Full Installation Guide & Documentation →](INTEGRATION_INSTALL.md)**

---

## Features

### Available API Endpoints

All endpoints are accessible at `https://your-instance.ui.nabu.casa/api/supervisor_gateway/`

#### Utility Endpoints
- `GET /health` - Health check (no authentication required)
- `GET /` - API documentation

#### Addon Management
- `GET /addons` - List all installed addons
- `GET /addons/{slug}` - Get specific addon information
- `POST /addons/{slug}/start` - Start an addon
- `POST /addons/{slug}/stop` - Stop an addon
- `POST /addons/{slug}/restart` - Restart an addon
- `POST /addons/{slug}/update` - Update an addon

### Authentication

The integration supports **dual authentication** for maximum security:

1. **Home Assistant Long-Lived Token** (required)
   - Standard HA authentication
   - Create from your profile → Long-Lived Access Tokens

2. **x-api-key Header** (optional but recommended)
   - Additional security layer
   - Configure in `configuration.yaml`

### Usage Example

```javascript
const HA_URL = "https://your-instance.ui.nabu.casa";
const HA_TOKEN = "your-long-lived-token";
const API_KEY = "your-api-key";  // If configured

// List all addons
fetch(`${HA_URL}/api/supervisor_gateway/addons`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));

// Restart an addon
fetch(`${HA_URL}/api/supervisor_gateway/addons/some_addon/restart`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## Security

### ⚠️ Important Security Considerations

This integration exposes Supervisor API endpoints which allow **addon management operations**. While useful for external dashboards, please be aware:

**What this integration allows:**
- ✅ List installed addons and their status
- ✅ Get addon information
- ✅ Start, stop, restart addons
- ✅ Update addons to newer versions

**Security measures in place:**
- ✅ Uses Home Assistant's built-in authentication
- ✅ All requests go through HA's auth middleware
- ✅ Optional x-api-key for additional protection
- ✅ Tokens can be revoked from your HA profile
- ✅ Works only with Supervisor API endpoints (no direct system access)
- ✅ Install/uninstall operations intentionally not exposed

### Best Practices

- 🔐 Use the optional `api_key` for external access
- 🔐 Keep your HA tokens secure and never commit them to version control
- 🔐 Regularly rotate your tokens (recommended: every 90 days)
- 🔐 Monitor your HA logs for suspicious activity
- 🔐 Only share tokens with trusted applications
- 🔐 Use different tokens for different external applications

**[📖 Full Security Guide →](SECURITY.md)**

---

## Documentation

- **[Installation Guide](INTEGRATION_INSTALL.md)** - Detailed installation and setup instructions
- **[Security Policy](SECURITY.md)** - Security best practices and vulnerability reporting
- **[Contributing](CONTRIBUTING.md)** - Guidelines for contributing to this project
- **[Changelog](CHANGELOG.md)** - Version history and changes

---

## Troubleshooting

### "404 Not Found"
Integration not loaded. Check:
1. Files are in `/config/custom_components/supervisor_gateway/`
2. `supervisor_gateway:` is in `configuration.yaml`
3. Home Assistant has been restarted

### "401 Unauthorized"
Authentication issue. Check:
1. Token is valid (create new one from profile)
2. `Authorization: Bearer TOKEN` header is set correctly
3. If using x-api-key, verify it matches configuration.yaml

### "Invalid or missing x-api-key header"
If you configured `api_key` in configuration.yaml, you must include the `x-api-key` header in all requests.

### Check Logs
Settings → System → Logs → Search for "supervisor_gateway"

---

## Support

- **Issues**: [GitHub Issues](https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon/issues)
- **Community**: [Home Assistant Community](https://community.home-assistant.io/)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

---

## Version

**Current Version**: 2.0.3

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

**Remember**: This integration provides external access to addon management capabilities. Use it responsibly and follow security best practices.
