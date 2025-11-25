# Supervisor API Gateway

**Secure API gateway for exposing Home Assistant Supervisor API endpoints externally.**

## WARNING: Security Notice

This addon exposes privileged Supervisor API endpoints to external access. The Supervisor API has **full control** over your Home Assistant instance including:
- Updating and managing addons
- Modifying system configurations
- Restarting services
- Accessing sensitive information

**Use this addon ONLY if you:**
1. Understand the security risks
2. Have configured strong authentication
3. Have enabled IP whitelisting
4. Monitor logs regularly for suspicious activity
5. Keep your API keys secret and secure

**DO NOT:**
- Share your API keys with anyone
- Commit API keys to version control
- Use weak or short API keys
- Disable security features
- Expose this without Nabu Casa or proper SSL

## Use Case

This addon provides secure external access to Home Assistant Supervisor API endpoints. It allows you to:
- Monitor addon status remotely
- Check for and update addons via API
- Start/stop/restart addons programmatically
- Manage your HA instance from external applications

## Security Features

This addon implements multiple layers of security:

1. **API Key Authentication**: Long random API keys (64+ characters recommended)
2. **IP Whitelisting**: Only allow requests from specific IP addresses
3. **Rate Limiting**: Prevent brute force attacks (configurable per minute/hour)
4. **Endpoint Whitelist**: Only specific Supervisor API endpoints are exposed
5. **Comprehensive Audit Logging**: All access attempts are logged with IP, timestamp, and status
6. **Emergency Kill Switch**: Instantly disable all access if needed
7. **Request Validation**: Input sanitization and validation

## Installation

### Method 1: Local Addon (Recommended for Testing)

1. Copy the `supervisor-api-gateway` folder to your Home Assistant addons directory:
   ```bash
   /addons/supervisor-api-gateway/
   ```

2. In Home Assistant, go to **Settings** > **Add-ons** > **Add-on Store**

3. Click the menu (three dots) and select **Check for updates**

4. You should see "Supervisor API Gateway" in the local add-ons section

5. Click on it and install

### Method 2: GitHub Repository (For Multiple Instances)

1. Create a GitHub repository for this addon

2. Push all files to the repository

3. In Home Assistant, add the repository URL:
   - Go to **Settings** > **Add-ons** > **Add-on Store**
   - Click menu > **Repositories**
   - Add your repository URL

## Configuration

### Generate Secure API Key

Generate a strong random API key (64+ characters):

```bash
# Linux/Mac
openssl rand -base64 64 | tr -d '\n' && echo

# Or using Python
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

**IMPORTANT**: Save this key securely. You'll need it to authenticate API requests.

### Configure the Addon

Example configuration:

```yaml
api_keys:
  - "your-super-long-random-api-key-here-64-plus-characters-minimum"
  - "optional-second-api-key-for-backup-or-different-client"
master_key: "your-master-key-for-key-management-endpoints"  # Optional
ip_whitelist:
  - "203.0.113.45"        # Your home IP
  - "198.51.100.0/24"     # Your office network (CIDR notation)
rate_limit_per_minute: 30
rate_limit_per_hour: 500
enable_emergency_disable: false
log_level: info
```

**💡 Tip: Don't know your IP?**

For accurate external IP detection:
```bash
# Use your Nabu Casa URL (recommended)
curl https://xxxxx.ui.nabu.casa:8099/my-ip

# Or visit in browser
https://xxxxx.ui.nabu.casa:8099/my-ip
```

This shows your real external IP that you should add to `ip_whitelist`.

⚠️ **Important:** Don't use `http://homeassistant.local:8099/my-ip` - it will show your internal network IP (like 192.168.x.x) which won't work for external access!

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_keys` | list | `[]` | List of API keys for authentication (64+ chars recommended) |
| `master_key` | string | `""` | Master key for key management endpoints (optional, 64+ chars) |
| `ip_whitelist` | list | `[]` | List of allowed IP addresses or CIDR ranges |
| `rate_limit_per_minute` | int | `30` | Maximum requests per minute per client |
| `rate_limit_per_hour` | int | `500` | Maximum requests per hour per client |
| `enable_emergency_disable` | bool | `false` | Set to `true` to instantly block all requests |
| `log_level` | string | `info` | Logging level: debug, info, warning, error |

## Key Management (Optional)

The addon includes built-in key management features for rotating and managing API keys.

### Setup Master Key

To use key management, add a `master_key` to your configuration:

```bash
# Generate master key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Add to configuration:
```yaml
master_key: "your-generated-master-key-here"
```

### Web UI

Access the key management UI at `http://YOUR_HA_IP:8099/manage` or via the addon's "Open Web UI" button.

Features:
- Generate new API keys
- Rotate keys with grace period
- Revoke keys
- View key usage statistics

### API Endpoints

All management endpoints require `X-Master-Key` header:

**Generate New Key:**
```bash
curl -X POST http://YOUR_HA_IP:8099/manage/generate-key \
  -H "X-Master-Key: YOUR_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "New API Key", "description": "Description"}'
```

**List All Keys:**
```bash
curl -X GET http://YOUR_HA_IP:8099/manage/list-keys \
  -H "X-Master-Key: YOUR_MASTER_KEY"
```

**Rotate Key (Automatic):**
```bash
curl -X POST http://YOUR_HA_IP:8099/manage/auto-rotate \
  -H "X-Master-Key: YOUR_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"old_key_hash": "hash-from-list-keys", "grace_hours": 0}'
```

This automatically updates the addon config and restarts with the new key.

**Revoke Key:**
```bash
curl -X POST http://YOUR_HA_IP:8099/manage/revoke-key \
  -H "X-Master-Key: YOUR_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key_hash": "hash-to-revoke"}'
```

## Exposing via Nabu Casa

1. Start the addon and ensure it's running

2. In Home Assistant, go to **Settings** > **System** > **Network**

3. Scroll to **Home Assistant Cloud** settings

4. Enable port forwarding for port **8099** (the gateway port)

5. Your external URL will be: `https://your-instance.ui.nabu.casa:8099`

## API Usage

### Authentication

All requests must include an `Authorization` header with your API key:

```
Authorization: Bearer your-super-long-random-api-key-here
```

### Available Endpoints

#### 1. Get All Addons

```bash
curl -X GET https://your-instance.ui.nabu.casa:8099/addons \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "data": {
    "addons": [
      {
        "name": "Example Addon",
        "slug": "example_addon",
        "version": "1.0.0",
        "state": "started"
      }
    ]
  }
}
```

#### 2. Get Specific Addon Info

```bash
curl -X GET https://your-instance.ui.nabu.casa:8099/addons/example_addon \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 3. Update Addon

```bash
curl -X POST https://your-instance.ui.nabu.casa:8099/addons/example_addon/update \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 4. Start/Stop/Restart Addon

```bash
# Start
curl -X POST https://your-instance.ui.nabu.casa:8099/addons/example_addon/start \
  -H "Authorization: Bearer YOUR_API_KEY"

# Stop
curl -X POST https://your-instance.ui.nabu.casa:8099/addons/example_addon/stop \
  -H "Authorization: Bearer YOUR_API_KEY"

# Restart
curl -X POST https://your-instance.ui.nabu.casa:8099/addons/example_addon/restart \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Note:** Install and uninstall endpoints are intentionally not exposed for safety.

### Example with Python

```python
import requests

API_URL = "https://your-instance.ui.nabu.casa:8099"
API_KEY = "your-super-long-random-api-key-here"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Get all addons
response = requests.get(f"{API_URL}/addons", headers=headers)
addons = response.json()

# Update an addon
response = requests.post(
    f"{API_URL}/addons/example_addon/update",
    headers=headers
)
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Invalid API key"
}
```

### 403 Forbidden (IP Not Whitelisted)
```json
{
  "error": "Access denied: IP not whitelisted"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded: 30 requests per minute"
}
```

### 503 Service Unavailable (Emergency Disable)
```json
{
  "error": "Service temporarily disabled"
}
```

## Adding More Endpoints

To expose additional Supervisor API endpoints:

1. Open `app.py` in the addon files

2. Add a new route handler after the existing endpoint handlers (around line 1176):
   ```python
   @app.route('/supervisor/info', methods=['GET'])
   @security_middleware
   def get_supervisor_info():
       """Get supervisor information"""
       try:
           response = requests.get(
               f"{SUPERVISOR_URL}/supervisor/info",
               headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
               timeout=10
           )
           return Response(response.content, status=response.status_code,
                         content_type='application/json')
       except Exception as e:
           logger.error(f"Error proxying to Supervisor API: {e}")
           return jsonify({"error": "Internal server error"}), 500
   ```

3. Rebuild and restart the addon

**Note:** The `@security_middleware` decorator automatically applies all security checks (IP whitelist, API key auth, rate limiting) to your new endpoint.

## Monitoring & Logs

### View Logs

In Home Assistant:
1. Go to **Settings** > **Add-ons**
2. Click on "Supervisor API Gateway"
3. Click the **Log** tab

### What to Monitor

Watch for these in logs:

**Normal Activity**:
```
INFO - API Access: {"timestamp":"2024-01-15T10:30:00","endpoint":"/addons","method":"GET","client_ip":"203.0.113.45","status":"success"}
```

**Suspicious Activity**:
```
WARNING - AUTH FAILED: {"timestamp":"2024-01-15T10:30:00","endpoint":"/addons","method":"GET","client_ip":"192.0.2.100","status":"auth_failed","message":"Invalid API key"}
```

```
WARNING - RATE LIMITED: {"timestamp":"2024-01-15T10:30:00","endpoint":"/addons","method":"GET","client_ip":"203.0.113.45","status":"rate_limited","message":"Rate limit exceeded: 30 requests per minute"}
```

### Emergency Response

If you suspect compromise:

1. **Immediately** set `enable_emergency_disable: true` in addon configuration
2. Save configuration to block all requests instantly
3. Regenerate your API keys
4. Review logs for unauthorized access
5. Check for any unauthorized changes to addons/system
6. Re-enable with new keys only when safe

## Troubleshooting

### "No API keys configured in addon"

Add at least one API key to the configuration:
```yaml
api_keys:
  - "your-generated-api-key-here"
```

### "Access denied: IP not whitelisted"

Add your IP address to the whitelist:
```yaml
ip_whitelist:
  - "YOUR.IP.ADDRESS.HERE"
```

Find your IP using the addon's endpoint (recommended):
```bash
# Via Nabu Casa (shows your real external IP)
curl https://xxxxx.ui.nabu.casa:8099/my-ip

# Or use external service
curl ifconfig.me
```

### "Rate limit exceeded"

Increase rate limits in configuration:
```yaml
rate_limit_per_minute: 60
rate_limit_per_hour: 1000
```

### Connection Timeout

Increase timeout in `app.py` for specific endpoints (e.g., install/update operations already have 300s timeout).

## Security Best Practices

1. **Use Long API Keys**: Minimum 64 characters, random generated
2. **Enable IP Whitelisting**: Always restrict to known IPs
3. **Monitor Logs Daily**: Watch for failed auth attempts
4. **Rotate Keys Regularly**: Change API keys every 90 days
5. **Use HTTPS Only**: Never expose via plain HTTP
6. **Limit Exposed Endpoints**: Only add endpoints you actually need
7. **Keep Addon Updated**: Watch for security updates
8. **Use Nabu Casa**: Don't expose directly without proper SSL/proxy
9. **Document Your Setup**: Keep notes on configuration and authorized IPs
10. **Test Emergency Disable**: Verify kill switch works before relying on it

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/GuyZipory/Home-Assistant-Admin-Panel-Helper-Addon/issues
- Home Assistant Community: https://community.home-assistant.io/

## License

MIT License - Use at your own risk

---

**Remember**: With great power comes great responsibility. This addon gives external access to privileged APIs. Use wisely and securely.
