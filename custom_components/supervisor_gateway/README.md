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

### Method 1: Manual Installation

1. Copy the `supervisor_gateway` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/supervisor_gateway/
   ```

2. Add to your `configuration.yaml`:
   ```yaml
   supervisor_gateway:
   ```

3. Restart Home Assistant

4. Done! The API endpoints are now available.

### Method 2: HACS (Coming Soon)

Will be available through HACS custom repository.

## Usage

### From Your External Dashboard

```javascript
const HA_URL = "https://your-instance.ui.nabu.casa";
const HA_TOKEN = "your-long-lived-access-token";

// List all addons
fetch(`${HA_URL}/api/supervisor_gateway/addons`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
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

Use your Home Assistant long-lived access token:

1. In Home Assistant, click your profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Use it in the `Authorization: Bearer TOKEN` header

## Benefits

✅ Clean URLs - No ingress tokens in URLs
✅ No port forwarding needed
✅ Works through Nabu Casa automatically
✅ Uses HA's native authentication
✅ Zero configuration after installation
✅ Tokens managed from HA profile

## Security

- Uses Home Assistant's built-in authentication
- All requests go through HA's auth middleware
- No additional attack surface
- Tokens can be revoked from your HA profile
- Works only with Supervisor API (no direct system access)

## Version

2.0.0 - Custom Integration Release
