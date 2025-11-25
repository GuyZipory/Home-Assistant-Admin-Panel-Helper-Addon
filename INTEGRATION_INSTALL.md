# Installation Guide - Custom Integration (Recommended)

## What You Get

**Clean API URLs through Nabu Casa with NO port forwarding:**

```
https://your-instance.ui.nabu.casa/api/supervisor_gateway/addons
https://your-instance.ui.nabu.casa/api/supervisor_gateway/health
```

Uses Home Assistant long-lived tokens - simple and secure!

## Installation Steps

### Step 1: Install the Custom Integration

#### Option A: HACS (Easiest)

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

#### Option B: Manual Installation

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

### Step 2: Enable the Integration

1. Edit your `/config/configuration.yaml`

2. Add configuration (with optional API key for extra security):
   ```yaml
   supervisor_gateway:
     api_key: "your-secret-api-key-here"  # Optional but recommended
   ```

   Or minimal (no extra API key):
   ```yaml
   supervisor_gateway:
   ```

3. Save the file

**💡 What's the `api_key` for?**
- Adds an extra layer of security beyond HA authentication
- External requests must include both:
  - `Authorization: Bearer YOUR_HA_TOKEN` (Home Assistant auth)
  - `x-api-key: YOUR_API_KEY` (Your custom API key)
- If not configured, only HA token is required

### Step 3: Restart Home Assistant

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart Home Assistant**

### Step 4: Verify It's Working

Visit (replace with your Nabu Casa URL):
```
https://your-instance.ui.nabu.casa/api/supervisor_gateway
```

You should see JSON documentation of available endpoints.

### Step 5: Create Long-Lived Access Token

1. Click your **profile** (bottom left in HA)
2. Scroll to "**Long-Lived Access Tokens**"
3. Click "**Create Token**"
4. Name it: "External Dashboard"
5. **Copy the token** (starts with `eyJ...`)

### Step 6: Use in Your External Dashboard

```javascript
const HA_URL = "https://your-instance.ui.nabu.casa";
const HA_TOKEN = "your-long-lived-token-here";
const API_KEY = "your-api-key-from-config";  // If configured

// List addons
fetch(`${HA_URL}/api/supervisor_gateway/addons`, {
  headers: {
    "Authorization": `Bearer ${HA_TOKEN}`,
    "x-api-key": API_KEY,  // Include if you configured api_key
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

## Done!

You now have clean API access through Nabu Casa with:
- ✅ No port forwarding
- ✅ No ingress tokens in URLs
- ✅ Home Assistant authentication
- ✅ Works immediately through Nabu Casa

## Troubleshooting

**"404 Not Found"** - Integration not loaded. Check:
1. Files are in `/config/custom_components/supervisor_gateway/`
2. `supervisor_gateway:` is in `configuration.yaml`
3. Home Assistant has been restarted

**"401 Unauthorized"** - Token issue. Check:
1. Token is valid (create new one from profile)
2. `Authorization: Bearer TOKEN` header is set correctly

**Check logs:**
Settings → System → Logs → Search for "supervisor_gateway"
