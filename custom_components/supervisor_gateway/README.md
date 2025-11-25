# Supervisor Gateway API - Custom Integration

**Clean API access to Home Assistant Supervisor without port forwarding or ingress tokens!**

## What This Does

Exposes Supervisor API endpoints through Home Assistant's native API at clean paths:

```
https://your-instance.ui.nabu.casa/api/supervisor_gateway/addons
https://your-instance.ui.nabu.casa/api/supervisor_gateway/health
```

Uses your existing Home Assistant long-lived access tokens - no extra configuration needed!

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the **3 dots** menu (top right)
3. Select **Custom repositories**
4. Add: `https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon`
5. Select category: **Integration**
6. Find "**Supervisor Gateway API**" and download
7. Add to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key"  # Optional but recommended
   ```
8. Restart Home Assistant

### Method 2: Manual Installation

1. Copy the `supervisor_gateway` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/supervisor_gateway/
   ```

2. Add to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key"  # Optional but recommended
   ```

3. Restart Home Assistant

4. Done! The API endpoints are now available.

## Usage

### From Your External Dashboard

```javascript
const HA_URL = "https://your-instance.ui.nabu.casa";
const HA_TOKEN = "your-long-lived-access-token";
const API_KEY = "your-api-key-from-config";  // If you configured api_key

// List all addons
fetch(`${HA_URL}/api/supervisor_gateway/addons`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,  // Include if you configured api_key
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
    "x-api-key": API_KEY,  // Include if you configured api_key
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

### Addon Management
- `GET /api/supervisor_gateway/addons` - List all addons
- `GET /api/supervisor_gateway/addons/{slug}` - Get addon info
- `POST /api/supervisor_gateway/addons/{slug}/update` - Update addon
- `POST /api/supervisor_gateway/addons/{slug}/start` - Start addon
- `POST /api/supervisor_gateway/addons/{slug}/stop` - Stop addon
- `POST /api/supervisor_gateway/addons/{slug}/restart` - Restart addon

## Authentication

This integration supports **dual authentication** for maximum security:

### Required: Home Assistant Long-Lived Token

1. In Home Assistant, click your profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Copy the token and use it in the `Authorization: Bearer TOKEN` header

### Optional: x-api-key Header

For additional security, you can require a custom API key:

1. Add `api_key` to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key-here"
   ```

2. Include the `x-api-key` header in all API requests:
   ```javascript
   headers: {
     "Authorization": "Bearer YOUR_HA_TOKEN",
     "x-api-key": "your-secret-api-key-here"
   }
   ```

**Why use x-api-key?**
- Adds an extra layer of security beyond HA authentication
- Useful when you want to limit access to specific external applications
- Can be changed independently of your HA token
- If not configured, only HA token is required

## Benefits

✅ Clean URLs - No ingress tokens in URLs
✅ No port forwarding needed
✅ Works through Nabu Casa automatically
✅ Uses HA's native authentication
✅ Zero configuration after installation
✅ Tokens managed from HA profile

## Security

### ⚠️ Important Security Considerations

This integration exposes Supervisor API endpoints which allow **addon management operations** (start, stop, restart, update). While this is useful for external dashboards, be aware:

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

**Best practices:**
- 🔐 Use the optional `api_key` for external access
- 🔐 Keep your HA tokens secure and never commit them to version control
- 🔐 Regularly rotate your tokens
- 🔐 Monitor your HA logs for suspicious activity
- 🔐 Only share tokens with trusted applications

## Version

2.0.3 - Custom Integration Release
- Added optional x-api-key header authentication for extra security
- Improved supervisor token access handling
- Bug fixes and stability improvements
