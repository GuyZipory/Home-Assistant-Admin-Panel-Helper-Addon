# Supervisor Gateway API - Custom Integration

**Clean API access to Home Assistant Supervisor without port forwarding or ingress tokens!**

A Home Assistant custom integration that provides secure REST API access to Supervisor endpoints for managing addons remotely.

## Version

**Current Version**: 3.1.0

⚠️ **v3.0.0 Breaking Change**: x-api-key is now REQUIRED (was optional in v2.x)

## What This Does

Exposes Supervisor API endpoints through Home Assistant's native API at clean paths:

```
https://your-instance.ui.nabu.casa/api/supervisor_gateway/addons
https://your-instance.ui.nabu.casa/api/supervisor_gateway/health
```

Requires dual authentication: Home Assistant long-lived tokens + configured x-api-key.

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the **3 dots** menu (top right)
3. Select **Custom repositories**
4. Add: `https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon`
5. Select category: **Integration**
6. Find "**Supervisor Gateway API**" and download
7. **REQUIRED**: Add to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key-here"  # REQUIRED
     ip_whitelist:  # OPTIONAL - restrict access to specific public IPs
       - "203.0.113.1"
       - "198.51.100.42"
   ```
8. Restart Home Assistant

### Method 2: Manual Installation

1. Copy the `supervisor_gateway` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/supervisor_gateway/
   ```

2. **REQUIRED**: Add to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key-here"  # REQUIRED
     ip_whitelist:  # OPTIONAL - restrict access to specific public IPs
       - "203.0.113.1"
       - "198.51.100.42"
   ```

3. Restart Home Assistant

4. Done! The API endpoints are now available.

## Configuration

The `api_key` is **REQUIRED** in v3.0.0+:

```yaml
supervisor_gateway:
  api_key: "use-a-long-random-string-32-chars-minimum"  # REQUIRED
  ip_whitelist:  # OPTIONAL - restrict access to specific public IPs
    - "203.0.113.1"
    - "198.51.100.42"
```

**Why is api_key required?**
- Provides dual authentication for maximum security
- External requests must include both:
  - `Authorization: Bearer YOUR_HA_TOKEN` (Home Assistant auth)
  - `x-api-key: YOUR_API_KEY` (Your custom API key from config)
- Use a long, random string (recommended: 32+ characters)

**IP Whitelist (Optional - New in v3.1.0):**
- Restrict API access to specific public IP addresses
- If configured, only requests from whitelisted IPs will be allowed (403 Forbidden otherwise)
- If not configured or empty, all IPs are allowed (backward compatible)
- Use `/my-ip` endpoint to discover your public IP (see below)

## Usage

### From Your External Dashboard

```javascript
const HA_URL = "https://your-instance.ui.nabu.casa";
const HA_TOKEN = "your-long-lived-access-token";
const API_KEY = "your-api-key-from-config";  // Required

// List all addons
fetch(`${HA_URL}/api/supervisor_gateway/addons`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,  // Required
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));

// Update an addon
fetch(`${HA_URL}/api/supervisor_gateway/addons/some_addon_slug/update`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,  // Required
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

## Available Endpoints

### Documentation
- `GET /api/supervisor_gateway` - API documentation

### Utility
- `GET /api/supervisor_gateway/health` - Health check (no auth required)
- `GET /api/supervisor_gateway/my-ip` - Show your public IP (HA token only, no x-api-key needed)

### Addon Management
- `GET /api/supervisor_gateway/addons` - List all addons
- `GET /api/supervisor_gateway/addons/{slug}` - Get addon info
- `POST /api/supervisor_gateway/addons/{slug}/update` - Update addon
- `POST /api/supervisor_gateway/addons/{slug}/start` - Start addon
- `POST /api/supervisor_gateway/addons/{slug}/stop` - Stop addon
- `POST /api/supervisor_gateway/addons/{slug}/restart` - Restart addon

## IP Whitelist (Optional - New in v3.1.0)

Restrict API access to specific public IP addresses for enhanced security.

**How to find your public IP:**
1. Access the `/my-ip` endpoint with only your HA token (no x-api-key needed):
   ```bash
   curl -H "Authorization: Bearer YOUR_HA_TOKEN" \
        https://your-instance.ui.nabu.casa/api/supervisor_gateway/my-ip
   ```

2. Response shows your public IP:
   ```json
   {
     "ip": "203.0.113.1",
     "message": "This is your public IP address. Add it to ip_whitelist in configuration.yaml if you want IP restrictions.",
     "source": "X-Forwarded-For"
   }
   ```

3. Add it to your configuration:
   ```yaml
   supervisor_gateway:
     api_key: "your-api-key"
     ip_whitelist:
       - "203.0.113.1"  # Your public IP
   ```

4. Restart Home Assistant

**How it works:**
- When accessing through Nabu Casa, your public IP is extracted from `X-Forwarded-For` or `X-Real-IP` headers
- If `ip_whitelist` is configured, only requests from those IPs are allowed (403 Forbidden otherwise)
- If `ip_whitelist` is not configured or empty, all IPs are allowed (backward compatible)
- Applies to all protected endpoints (addon management)
- Does NOT apply to `/health` and `/my-ip` endpoints

## Authentication

This integration requires **dual authentication** for maximum security:

### 1. Home Assistant Long-Lived Token (Required)

1. In Home Assistant, click your profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Copy the token and use it in the `Authorization: Bearer TOKEN` header

### 2. x-api-key Header (Required)

Must be configured in `configuration.yaml` - all requests must include this header matching your configured `api_key`.

## Security

### ⚠️ Important Security Considerations

This integration exposes Supervisor API endpoints which allow **addon management operations**. While this is useful for external dashboards, be aware:

**What this integration allows:**
- ✅ List installed addons and their status
- ✅ Get addon information
- ✅ Start, stop, restart addons
- ✅ Update addons to newer versions

**Security measures in place:**
- ✅ Uses Home Assistant's built-in authentication
- ✅ All requests go through HA's auth middleware
- ✅ Required x-api-key for dual authentication
- ✅ Optional IP whitelist for restricting access by public IP
- ✅ Tokens can be revoked from your HA profile
- ✅ Works only with Supervisor API endpoints (no direct system access)

### Best Practices

- 🔐 Use a strong api_key (32+ characters)
- 🔐 Consider IP whitelisting for enhanced security (use `/my-ip` endpoint to discover your public IP)
- 🔐 Keep your HA tokens secure and never commit them to version control
- 🔐 Regularly rotate your tokens (recommended: every 90 days)
- 🔐 Monitor your HA logs for suspicious activity
- 🔐 Only share tokens with trusted applications

## Migration from v2.x

If upgrading from v2.x, you **must** add the `api_key` to your configuration:

```yaml
supervisor_gateway:
  api_key: "your-long-random-string-here"
```

Without this configuration, the integration will reject all API requests.

## Documentation

For full documentation, see the main [README.md](../../README.md) in the repository root.

## Version History

- **3.1.0** - Added optional IP whitelist and /my-ip endpoint
- **3.0.0** - Breaking change: x-api-key now required
- **2.0.3** - Optional x-api-key added
- **2.0.0** - Initial release
