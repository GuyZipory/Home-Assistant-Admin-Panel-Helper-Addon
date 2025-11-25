# Supervisor Gateway API

**Clean API access to Home Assistant Supervisor through Nabu Casa - No ports, no ingress tokens!**

A Home Assistant custom integration that provides clean REST API access to Supervisor endpoints for managing addons remotely through your external dashboards.

## What You Get

- ✅ Clean URLs: `https://your-instance.ui.nabu.casa/api/supervisor_gateway/addons`
- ✅ No port forwarding needed
- ✅ Works through Nabu Casa automatically
- ✅ Simple authentication with HA tokens
- ✅ Optional extra security with x-api-key
- ✅ Manage addons from external dashboards

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the **3 dots** menu (top right)
3. Select **Custom repositories**
4. Add repository URL:
   ```
   https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon
   ```
5. Select category: **Integration**
6. Click **Add**
7. Find "**Supervisor Gateway API**" in HACS
8. Click **Download**
9. Restart Home Assistant

### Method 2: Manual Installation

1. Download the `custom_components/supervisor_gateway` folder from this repository

2. Copy it to your Home Assistant config directory:
   ```
   /config/custom_components/supervisor_gateway/
   ```

3. Your structure should look like:
   ```
   /config/
     custom_components/
       supervisor_gateway/
         __init__.py
         api.py
         manifest.json
         README.md
   ```

4. Restart Home Assistant

### Configuration

Edit your `/config/configuration.yaml` and add:

```yaml
supervisor_gateway:
  api_key: "your-secret-api-key-here"  # Optional but recommended
```

Or minimal configuration (no extra API key):
```yaml
supervisor_gateway:
```

**💡 What's the `api_key` for?**
- Adds an extra layer of security beyond HA authentication
- External requests must include both:
  - `Authorization: Bearer YOUR_HA_TOKEN` (Home Assistant auth)
  - `x-api-key: YOUR_API_KEY` (Your custom API key)
- If not configured, only HA token is required

### Restart Home Assistant

Go to **Settings** → **System** → **Restart** and click **Restart Home Assistant**

### Verify It's Working

Visit (replace with your Nabu Casa URL):
```
https://your-instance.ui.nabu.casa/api/supervisor_gateway
```

You should see JSON documentation of available endpoints.

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

---

## Authentication

The integration supports **dual authentication** for maximum security:

### 1. Home Assistant Long-Lived Token (Required)

Create a token for your external dashboard:

1. Click your **profile** (bottom left in HA)
2. Scroll to "**Long-Lived Access Tokens**"
3. Click "**Create Token**"
4. Name it: "External Dashboard"
5. **Copy the token** (starts with `eyJ...`)

### 2. x-api-key Header (Optional but Recommended)

Additional security layer configured in `configuration.yaml`

---

## Usage Example

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

### ⚠️ Important: What This Integration Does

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

### 🔐 Best Practices

1. **Use the x-api-key configuration** for external access:
   ```yaml
   supervisor_gateway:
     api_key: "use-a-long-random-string-here"
   ```

2. **Keep tokens secure**:
   - Never commit tokens to version control
   - Don't share tokens in screenshots or logs
   - Use different tokens for different applications

3. **Rotate tokens regularly**:
   - Create new tokens every 90 days
   - Delete old tokens from your HA profile

4. **Monitor access**:
   - Check HA logs regularly: Settings → System → Logs
   - Search for "supervisor_gateway" to see API activity
   - Watch for unexpected addon changes

5. **Limit token permissions** (if possible):
   - Create dedicated user accounts for external apps
   - Use the principle of least privilege

### 🚨 Suspicious Activity & Response

**Watch for these indicators:**
- Addons restarting unexpectedly
- Addon updates you didn't initiate
- Failed authentication attempts in logs
- Unknown activity patterns

**If compromised:**
1. **Immediately revoke** the HA token (Profile → Long-Lived Access Tokens)
2. **Change** the `api_key` in configuration.yaml
3. **Restart** Home Assistant
4. **Review** recent addon changes in logs
5. **Check** HA logs for unauthorized access patterns

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

## Documentation

- **[Changelog](CHANGELOG.md)** - Version history and changes

---

## Support

- **Issues**: [GitHub Issues](https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon/issues)
- **Community**: [Home Assistant Community](https://community.home-assistant.io/)

---

## Version

**Current Version**: 2.0.3

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

**Remember**: This integration provides external access to addon management capabilities. Use it responsibly and follow security best practices.
