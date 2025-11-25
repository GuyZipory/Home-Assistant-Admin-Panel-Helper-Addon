#!/usr/bin/env python3
"""
Secure API Gateway for Home Assistant Supervisor API - V1
WARNING: This addon exposes privileged Supervisor API endpoints externally.
Use with extreme caution and only with proper security configurations.
"""

import os
import json
import logging
import hashlib
import secrets
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from typing import Dict, List, Tuple, Optional

from flask import Flask, request, jsonify, Response, render_template_string
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
CONFIG_PATH = "/data/options.json"
KEYS_DB_PATH = "/data/keys.json"

# Get Supervisor token from multiple possible sources
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
if not SUPERVISOR_TOKEN:
    SUPERVISOR_TOKEN = os.environ.get("HASSIO_TOKEN")
if not SUPERVISOR_TOKEN:
    try:
        with open("/run/secrets/SUPERVISOR_TOKEN", "r") as f:
            SUPERVISOR_TOKEN = f.read().strip()
    except:
        pass

SUPERVISOR_URL = "http://supervisor"
HOMEASSISTANT_URL = "http://supervisor/core"

# Security state
rate_limit_store: Dict[str, List[datetime]] = defaultdict(list)
config = {}
keys_db = {}  # API key database with metadata


# =============================================================================
# KEY MANAGEMENT SYSTEM
# =============================================================================

def hash_key(key: str) -> str:
    """Hash API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key(length: int = 64) -> str:
    """Generate a cryptographically secure random API key"""
    return secrets.token_urlsafe(length)


def load_keys_db():
    """Load API keys database from disk"""
    global keys_db
    try:
        if os.path.exists(KEYS_DB_PATH):
            with open(KEYS_DB_PATH, 'r') as f:
                keys_db = json.load(f)
            logger.info(f"Keys database loaded: {len(keys_db)} keys")
        else:
            keys_db = {}
            logger.info("No keys database found, starting fresh")
    except Exception as e:
        logger.error(f"Failed to load keys database: {e}")
        keys_db = {}


def save_keys_db():
    """Save API keys database to disk"""
    try:
        with open(KEYS_DB_PATH, 'w') as f:
            json.dump(keys_db, f, indent=2)
        logger.info("Keys database saved")
        return True
    except Exception as e:
        logger.error(f"Failed to save keys database: {e}")
        return False


def add_key(key: str, name: str = "unnamed", description: str = "") -> Dict:
    """
    Add a new API key to the database
    Returns the key metadata
    """
    key_hash = hash_key(key)

    key_data = {
        "hash": key_hash,
        "name": name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "last_used": None,
        "status": "active",  # active, deprecated, revoked
        "usage_count": 0
    }

    keys_db[key_hash] = key_data
    save_keys_db()

    logger.info(f"New API key added: {name} (hash: {key_hash[:16]}...)")
    return key_data


def find_key(provided_key: str) -> Optional[Dict]:
    """
    Find a key in the database by comparing hashes
    Returns key metadata if found and active
    """
    key_hash = hash_key(provided_key)

    if key_hash in keys_db:
        key_data = keys_db[key_hash]

        # Update last used timestamp
        key_data["last_used"] = datetime.now().isoformat()
        key_data["usage_count"] = key_data.get("usage_count", 0) + 1
        save_keys_db()

        return key_data

    return None


def revoke_key(key_hash: str) -> bool:
    """Revoke an API key"""
    if key_hash in keys_db:
        keys_db[key_hash]["status"] = "revoked"
        keys_db[key_hash]["revoked_at"] = datetime.now().isoformat()
        save_keys_db()
        logger.warning(f"API key revoked: {key_hash[:16]}...")
        return True
    return False


def deprecate_key(key_hash: str, grace_hours: int = 24) -> bool:
    """Mark a key as deprecated (still works but scheduled for revocation)"""
    if key_hash in keys_db:
        keys_db[key_hash]["status"] = "deprecated"
        keys_db[key_hash]["deprecated_at"] = datetime.now().isoformat()
        keys_db[key_hash]["grace_until"] = (
            datetime.now() + timedelta(hours=grace_hours)
        ).isoformat()
        save_keys_db()
        logger.warning(f"API key deprecated: {key_hash[:16]}... (grace: {grace_hours}h)")
        return True
    return False


def cleanup_expired_keys():
    """Automatically revoke keys past their grace period"""
    now = datetime.now()
    revoked_count = 0

    for key_hash, key_data in keys_db.items():
        if key_data["status"] == "deprecated":
            grace_until = datetime.fromisoformat(key_data["grace_until"])
            if now > grace_until:
                key_data["status"] = "revoked"
                key_data["revoked_at"] = now.isoformat()
                revoked_count += 1

    if revoked_count > 0:
        save_keys_db()
        logger.info(f"Auto-revoked {revoked_count} expired keys")


def migrate_legacy_keys():
    """
    Migrate old plain-text keys from config to new hashed system
    This runs once on startup if config has plain string keys
    """
    legacy_keys = config.get('api_keys', [])

    if not legacy_keys:
        return

    # Check if they're legacy format (plain strings)
    for i, key in enumerate(legacy_keys):
        if isinstance(key, str):  # Legacy format
            key_hash = hash_key(key)

            # Don't re-add if already exists
            if key_hash not in keys_db:
                add_key(
                    key=key,
                    name=f"Migrated Key {i+1}",
                    description="Auto-migrated from legacy config"
                )
                logger.info(f"Migrated legacy key #{i+1}")


# =============================================================================
# HOME ASSISTANT TOKEN VALIDATION
# =============================================================================

def validate_ha_token(token: str) -> bool:
    """
    Validate a Home Assistant long-lived access token
    Returns True if valid, False otherwise
    """
    try:
        response = requests.get(
            f"{HOMEASSISTANT_URL}/api/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            # HA API returns {"message": "API running."} for valid tokens
            if data.get("message") == "API running.":
                logger.debug("Home Assistant token validated successfully")
                return True

        logger.warning(f"HA token validation failed: {response.status_code}")
        return False

    except Exception as e:
        logger.error(f"Error validating HA token: {e}")
        return False


# =============================================================================
# CONFIGURATION & STARTUP
# =============================================================================

def load_config():
    """Load addon configuration"""
    global config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)

        # Set log level
        log_level = config.get('log_level', 'info').upper()
        logger.setLevel(getattr(logging, log_level))

        logger.info("Configuration loaded successfully")
        logger.info(f"IP Whitelist: {len(config.get('ip_whitelist', []))} IPs configured")
        logger.info(f"Rate limit: {config.get('rate_limit_per_minute')}/min, {config.get('rate_limit_per_hour')}/hour")

        return True
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False


def get_client_ip() -> str:
    """Get the real client IP (handles proxies)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def is_private_ip(ip: str) -> bool:
    """Check if an IP address is private/internal"""
    try:
        # Split IP into octets
        octets = [int(x) for x in ip.split('.')]

        # Check private IP ranges
        # 10.0.0.0 - 10.255.255.255
        if octets[0] == 10:
            return True
        # 172.16.0.0 - 172.31.255.255
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True
        # 192.168.0.0 - 192.168.255.255
        if octets[0] == 192 and octets[1] == 168:
            return True
        # 127.0.0.0 - 127.255.255.255 (localhost)
        if octets[0] == 127:
            return True

        return False
    except:
        return False


def check_emergency_disable():
    """Check if emergency disable is activated"""
    if config.get('enable_emergency_disable', False):
        logger.critical("EMERGENCY DISABLE ACTIVATED - All requests blocked")
        return True
    return False


def check_ip_whitelist(client_ip: str) -> bool:
    """Check if client IP is whitelisted"""
    whitelist = config.get('ip_whitelist', [])

    if not whitelist:
        return True

    for allowed_ip in whitelist:
        if client_ip == allowed_ip:
            return True

    return False


def check_rate_limit(client_id: str) -> Tuple[bool, Optional[str]]:
    """Check rate limiting for client"""
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    hour_ago = now - timedelta(hours=1)

    rate_limit_store[client_id] = [
        ts for ts in rate_limit_store[client_id]
        if ts > hour_ago
    ]

    requests_last_minute = sum(1 for ts in rate_limit_store[client_id] if ts > minute_ago)
    requests_last_hour = len(rate_limit_store[client_id])

    limit_per_minute = config.get('rate_limit_per_minute', 30)
    limit_per_hour = config.get('rate_limit_per_hour', 500)

    if requests_last_minute >= limit_per_minute:
        return False, f"Rate limit exceeded: {limit_per_minute} requests per minute"

    if requests_last_hour >= limit_per_hour:
        return False, f"Rate limit exceeded: {limit_per_hour} requests per hour"

    rate_limit_store[client_id].append(now)
    return True, None


def authenticate_request() -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Authenticate incoming request using either API keys or HA tokens based on auth_mode
    Returns: (authenticated, error_message, key_metadata)
    """
    # Check if request comes through Home Assistant ingress
    # Ingress already authenticated the user, so we trust it
    ingress_path = request.headers.get('X-Ingress-Path')
    hassio_key = request.headers.get('X-Hassio-Key')

    if ingress_path is not None:
        # Request comes through HA ingress - already authenticated by HA
        logger.debug("Request authenticated via Home Assistant ingress")
        ingress_token_data = {
            "name": "Home Assistant Ingress",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat()
        }
        return True, None, ingress_token_data

    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return False, "Missing or invalid Authorization header", None

    provided_token = auth_header[7:]
    auth_mode = config.get('auth_mode', 'api_key')

    # Try API key authentication
    if auth_mode in ['api_key', 'both']:
        key_data = find_key(provided_token)

        if key_data:
            # Check key status
            if key_data["status"] == "revoked":
                return False, "API key has been revoked", None

            if key_data["status"] == "deprecated":
                # Still allow but warn
                logger.warning(f"Deprecated key used: {key_data['name']}")
                # Check if past grace period
                grace_until = datetime.fromisoformat(key_data["grace_until"])
                if datetime.now() > grace_until:
                    # Auto-revoke
                    key_hash = hash_key(provided_token)
                    revoke_key(key_hash)
                    return False, "API key has expired (past grace period)", None

            logger.debug(f"Authenticated via API key: {key_data['name']}")
            return True, None, key_data

    # Try Home Assistant token authentication
    if auth_mode in ['homeassistant', 'both']:
        if validate_ha_token(provided_token):
            # Create a pseudo key_data for HA tokens
            ha_token_data = {
                "name": "Home Assistant Token",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
            logger.debug("Authenticated via Home Assistant token")
            return True, None, ha_token_data

    # If we get here, authentication failed
    if auth_mode == 'api_key':
        return False, "Invalid API key", None
    elif auth_mode == 'homeassistant':
        return False, "Invalid Home Assistant token", None
    else:  # both
        return False, "Invalid API key or Home Assistant token", None


def audit_log(endpoint: str, method: str, client_ip: str, status: str,
              message: str = "", key_name: str = "unknown"):
    """Log all API access attempts"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "method": method,
        "client_ip": client_ip,
        "key_name": key_name,
        "status": status,
        "message": message
    }

    if status == "success":
        logger.info(f"API Access: {json.dumps(log_entry)}")
    elif status == "auth_failed":
        logger.warning(f"AUTH FAILED: {json.dumps(log_entry)}")
    elif status == "rate_limited":
        logger.warning(f"RATE LIMITED: {json.dumps(log_entry)}")
    elif status == "blocked":
        logger.error(f"BLOCKED: {json.dumps(log_entry)}")
    else:
        logger.error(f"ERROR: {json.dumps(log_entry)}")


def security_middleware(f):
    """Apply all security checks before processing request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        endpoint = request.path
        method = request.method

        # Check if request comes through ingress (already authenticated by HA)
        from_ingress = request.headers.get('X-Ingress-Path') is not None

        # 1. Emergency disable check
        if check_emergency_disable():
            audit_log(endpoint, method, client_ip, "blocked", "Emergency disable active")
            return jsonify({"error": "Service temporarily disabled"}), 503

        # 2. IP whitelist check (skip for ingress requests - HA already authenticated)
        if not from_ingress and not check_ip_whitelist(client_ip):
            audit_log(endpoint, method, client_ip, "blocked", "IP not whitelisted")
            return jsonify({"error": "Access denied: IP not whitelisted"}), 403

        # 3. Authentication check (now with key metadata)
        authenticated, auth_error, key_data = authenticate_request()
        if not authenticated:
            audit_log(endpoint, method, client_ip, "auth_failed", auth_error)
            return jsonify({"error": auth_error}), 401

        key_name = key_data.get("name", "unknown") if key_data else "unknown"

        # 4. Rate limiting check
        client_id = f"{client_ip}:{key_name}"
        allowed, rate_error = check_rate_limit(client_id)
        if not allowed:
            audit_log(endpoint, method, client_ip, "rate_limited", rate_error, key_name)
            return jsonify({"error": rate_error}), 429

        # All checks passed
        audit_log(endpoint, method, client_ip, "success", key_name=key_name)

        # Add key metadata to request context for handlers to use if needed
        request.key_metadata = key_data

        return f(*args, **kwargs)

    return decorated_function


# Special auth for management endpoints (requires master_key from config)
def management_auth(f):
    """Special authentication for key management endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        master_key = config.get('master_key')

        if not master_key:
            return jsonify({
                "error": "Master key not configured",
                "hint": "Add 'master_key' to addon configuration"
            }), 503

        auth_header = request.headers.get('X-Master-Key', '')

        if auth_header != master_key:
            logger.error(f"Failed master key auth attempt from {get_client_ip()}")
            return jsonify({"error": "Invalid master key"}), 403

        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# KEY MANAGEMENT ENDPOINTS
# =============================================================================

@app.route('/manage/rotate-key', methods=['POST'])
@management_auth
def rotate_key():
    """
    Rotate API key - generates new key and deprecates old one
    Requires: X-Master-Key header
    Body: {"old_key_hash": "...", "grace_hours": 24}
    """
    try:
        data = request.get_json() or {}
        old_key_hash = data.get('old_key_hash')
        grace_hours = data.get('grace_hours', 24)

        if not old_key_hash:
            return jsonify({"error": "old_key_hash required"}), 400

        # Deprecate old key
        if old_key_hash not in keys_db:
            return jsonify({"error": "Key not found"}), 404

        old_key_data = keys_db[old_key_hash]
        deprecate_key(old_key_hash, grace_hours)

        # Generate new key
        new_key = generate_api_key(64)
        new_key_data = add_key(
            key=new_key,
            name=f"{old_key_data['name']} (rotated)",
            description=f"Rotated from {old_key_hash[:16]}... on {datetime.now().isoformat()}"
        )

        logger.warning(f"Key rotated: {old_key_data['name']}")

        return jsonify({
            "success": True,
            "new_key": new_key,  # ONLY TIME WE RETURN THE ACTUAL KEY
            "new_key_hash": new_key_data["hash"],
            "old_key_hash": old_key_hash,
            "old_key_deprecated_until": keys_db[old_key_hash]["grace_until"],
            "message": f"New key generated. Old key will be revoked in {grace_hours} hours."
        })

    except Exception as e:
        logger.error(f"Key rotation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/manage/auto-rotate', methods=['POST'])
@management_auth
def auto_rotate_key():
    """
    Fully automatic key rotation
    1. Generate new key
    2. Update addon configuration via Supervisor API (adds to api_keys)
    3. Schedule addon restart
    4. Return new key to dashboard

    This allows one-click rotation from your dashboard!

    Requires: X-Master-Key header
    Body: {
        "old_key_hash": "...",
        "grace_hours": 0,  # Optional, default 0 (immediate)
        "addon_slug": "supervisor_api_gateway"  # Optional, auto-detected
    }
    """
    try:
        data = request.get_json() or {}
        old_key_hash = data.get('old_key_hash')
        grace_hours = data.get('grace_hours', 0)
        addon_slug = data.get('addon_slug') or os.environ.get('ADDON_SLUG', 'supervisor_api_gateway')

        if not old_key_hash:
            return jsonify({"error": "old_key_hash required"}), 400

        if old_key_hash not in keys_db:
            return jsonify({"error": "Key not found"}), 404

        old_key_data = keys_db[old_key_hash]

        # 1. Generate new key
        new_key = generate_api_key(64)
        new_key_hash = hash_key(new_key)

        logger.info(f"Auto-rotation started for: {old_key_data['name']}")

        # 2. Get current addon configuration
        try:
            response = requests.get(
                f"{SUPERVISOR_URL}/addons/{addon_slug}/options/config",
                headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
                timeout=10
            )

            if not response.ok:
                logger.error(f"Failed to read config: {response.status_code} {response.text}")
                return jsonify({
                    "error": "Failed to read current addon configuration",
                    "details": response.text,
                    "hint": "Check that hassio_role: manager is set in config.yaml"
                }), 500

            current_config = response.json()['data']
            logger.debug(f"Current config: {current_config}")

        except Exception as e:
            logger.error(f"Error reading addon config: {e}")
            return jsonify({
                "error": "Failed to access Supervisor API",
                "details": str(e)
            }), 500

        # 3. Update configuration with new key
        if 'api_keys' not in current_config:
            current_config['api_keys'] = []

        # Add new key (will be auto-migrated on restart)
        current_config['api_keys'].append(new_key)

        # Optionally remove old keys from config (they'll still be in keys_db)
        # This keeps config clean, but keys_db is source of truth
        # current_config['api_keys'] = [new_key]  # Uncomment to replace entirely

        # Write updated config
        try:
            response = requests.post(
                f"{SUPERVISOR_URL}/addons/{addon_slug}/options",
                headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
                json={"options": current_config},
                timeout=10
            )

            if not response.ok:
                logger.error(f"Failed to update config: {response.status_code} {response.text}")
                return jsonify({
                    "error": "Failed to update addon configuration",
                    "details": response.text
                }), 500

            logger.info("Addon configuration updated successfully")

        except Exception as e:
            logger.error(f"Error updating addon config: {e}")
            return jsonify({
                "error": "Failed to write configuration",
                "details": str(e)
            }), 500

        # 4. Add new key to database
        add_key(
            key=new_key,
            name=f"{old_key_data['name']} (auto-rotated)",
            description=f"Auto-rotated from {old_key_hash[:16]}... on {datetime.now().isoformat()}"
        )

        # 5. Deprecate/revoke old key
        if grace_hours > 0:
            deprecate_key(old_key_hash, grace_hours)
            logger.info(f"Old key deprecated with {grace_hours}h grace period")
        else:
            revoke_key(old_key_hash)
            logger.info("Old key revoked immediately")

        # 6. Schedule addon restart (async, after response is sent)
        def restart_addon():
            time.sleep(2)  # Give time for response to be sent
            try:
                logger.warning(f"Restarting addon {addon_slug}...")
                response = requests.post(
                    f"{SUPERVISOR_URL}/addons/{addon_slug}/restart",
                    headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
                    timeout=10
                )
                if response.ok:
                    logger.info("Addon restart initiated successfully")
                else:
                    logger.error(f"Addon restart failed: {response.text}")
            except Exception as e:
                logger.error(f"Error restarting addon: {e}")

        # Start restart in background thread
        threading.Thread(target=restart_addon, daemon=True).start()

        logger.warning(f"Auto-rotation complete for {old_key_data['name']}, restarting in 2s...")

        # 7. Return response immediately (before restart)
        return jsonify({
            "success": True,
            "new_key": new_key,  # ONLY TIME WE RETURN THE ACTUAL KEY
            "new_key_hash": new_key_hash,
            "old_key_hash": old_key_hash,
            "old_key_status": "revoked" if grace_hours == 0 else "deprecated",
            "grace_until": keys_db[old_key_hash].get("grace_until") if grace_hours > 0 else None,
            "message": "Key rotated successfully. Addon restarting in 2 seconds.",
            "restart_in_seconds": 2,
            "instructions": {
                "1": "Save the new key immediately",
                "2": "Wait 5-10 seconds for addon to restart",
                "3": "Test the new key with a /health request",
                "4": "Update your dashboard configuration"
            }
        })

    except Exception as e:
        logger.error(f"Auto-rotation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.route('/manage/generate-key', methods=['POST'])
@management_auth
def generate_key():
    """
    Generate a new API key
    Requires: X-Master-Key header
    Body: {"name": "...", "description": "..."}
    """
    try:
        data = request.get_json() or {}
        name = data.get('name', f'Key-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        description = data.get('description', '')

        # Generate new key
        new_key = generate_api_key(64)
        key_data = add_key(key=new_key, name=name, description=description)

        logger.info(f"New API key generated: {name}")

        return jsonify({
            "success": True,
            "key": new_key,  # ONLY TIME WE RETURN THE ACTUAL KEY
            "key_hash": key_data["hash"],
            "name": name,
            "created_at": key_data["created_at"],
            "warning": "Save this key securely. It won't be shown again."
        })

    except Exception as e:
        logger.error(f"Key generation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/manage/revoke-key', methods=['POST'])
@management_auth
def revoke_key_endpoint():
    """
    Revoke an API key immediately
    Requires: X-Master-Key header
    Body: {"key_hash": "..."}
    """
    try:
        data = request.get_json() or {}
        key_hash = data.get('key_hash')

        if not key_hash:
            return jsonify({"error": "key_hash required"}), 400

        if revoke_key(key_hash):
            return jsonify({
                "success": True,
                "message": "Key revoked successfully"
            })
        else:
            return jsonify({"error": "Key not found"}), 404

    except Exception as e:
        logger.error(f"Key revocation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/manage/list-keys', methods=['GET'])
@management_auth
def list_keys():
    """
    List all API keys (without revealing actual keys)
    Requires: X-Master-Key header
    """
    keys_list = []
    for key_hash, key_data in keys_db.items():
        keys_list.append({
            "hash": key_hash,
            "hash_short": key_hash[:16] + "...",
            "name": key_data["name"],
            "description": key_data.get("description", ""),
            "status": key_data["status"],
            "created_at": key_data["created_at"],
            "last_used": key_data.get("last_used"),
            "usage_count": key_data.get("usage_count", 0),
            "grace_until": key_data.get("grace_until") if key_data["status"] == "deprecated" else None
        })

    return jsonify({
        "keys": keys_list,
        "total": len(keys_list)
    })


# Simple HTML UI for key management
KEY_MANAGEMENT_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>API Key Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .warning { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }
        .success { background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }
        .error { background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; }
        input, button { padding: 10px; margin: 5px 0; font-size: 14px; }
        input[type="text"], input[type="password"] { width: 100%; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px; }
        button:hover { background: #0056b3; }
        button.danger { background: #dc3545; }
        button.danger:hover { background: #c82333; }
        .key-list { margin: 20px 0; }
        .key-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border: 1px solid #dee2e6; }
        .key-item.deprecated { border-left: 4px solid #ffc107; }
        .key-item.revoked { border-left: 4px solid #dc3545; opacity: 0.6; }
        .status { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .status.active { background: #28a745; color: white; }
        .status.deprecated { background: #ffc107; color: black; }
        .status.revoked { background: #dc3545; color: white; }
        .form-section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 4px; }
        code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .key-display { background: #212529; color: #0f0; padding: 15px; border-radius: 4px; font-family: monospace; word-break: break-all; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 API Key Management</h1>

        <div class="warning">
            <strong>⚠️ Security Notice:</strong> All operations require the Master Key from your addon configuration.
        </div>

        <div class="form-section">
            <h3>Master Key</h3>
            <input type="password" id="masterKey" placeholder="Enter your master key" />
            <p style="font-size: 12px; color: #666;">Set in addon config as <code>master_key</code></p>
        </div>

        <div class="form-section">
            <h3>Generate New API Key</h3>
            <input type="text" id="keyName" placeholder="Key name (e.g., 'Production Dashboard')" />
            <input type="text" id="keyDesc" placeholder="Description (optional)" />
            <button onclick="generateKey()">🔑 Generate New Key</button>
            <div id="generateResult"></div>
        </div>

        <div class="form-section">
            <h3>Rotate Existing Key</h3>
            <input type="text" id="rotateKeyHash" placeholder="Key hash to rotate (from list below)" />
            <input type="number" id="rotateGraceHours" placeholder="Grace period (hours)" value="24" />
            <button onclick="rotateKey()">🔄 Rotate Key</button>
            <p style="font-size: 12px; color: #666;">Old key will continue working during grace period</p>
            <div id="rotateResult"></div>
        </div>

        <h3>Existing Keys</h3>
        <button onclick="listKeys()">🔍 Refresh Key List</button>
        <div id="keysList" class="key-list"></div>

    </div>

    <script>
        const API_BASE = window.location.origin;

        function getMasterKey() {
            const mk = document.getElementById('masterKey').value;
            if (!mk) {
                alert('Please enter master key first');
                return null;
            }
            return mk;
        }

        async function generateKey() {
            const masterKey = getMasterKey();
            if (!masterKey) return;

            const name = document.getElementById('keyName').value || 'Unnamed Key';
            const description = document.getElementById('keyDesc').value;

            try {
                const response = await fetch(API_BASE + '/manage/generate-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Master-Key': masterKey
                    },
                    body: JSON.stringify({ name, description })
                });

                const data = await response.json();

                if (response.ok) {
                    document.getElementById('generateResult').innerHTML =
                        '<div class="success">' +
                        '<strong>✅ Key Generated Successfully!</strong><br>' +
                        '<p style="margin:10px 0"><strong>⚠️ SAVE THIS KEY - IT WON\'T BE SHOWN AGAIN:</strong></p>' +
                        '<div class="key-display">' + data.key + '</div>' +
                        '<p>Name: ' + data.name + '</p>' +
                        '<p>Hash: <code>' + data.key_hash.substring(0, 16) + '...</code></p>' +
                        '</div>';
                    listKeys();
                } else {
                    document.getElementById('generateResult').innerHTML =
                        '<div class="error">❌ Error: ' + data.error + '</div>';
                }
            } catch (e) {
                document.getElementById('generateResult').innerHTML =
                    '<div class="error">❌ Error: ' + e.message + '</div>';
            }
        }

        async function rotateKey() {
            const masterKey = getMasterKey();
            if (!masterKey) return;

            const oldKeyHash = document.getElementById('rotateKeyHash').value;
            const graceHours = parseInt(document.getElementById('rotateGraceHours').value) || 24;

            if (!oldKeyHash) {
                alert('Please enter the key hash to rotate');
                return;
            }

            try {
                const response = await fetch(API_BASE + '/manage/rotate-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Master-Key': masterKey
                    },
                    body: JSON.stringify({ old_key_hash: oldKeyHash, grace_hours: graceHours })
                });

                const data = await response.json();

                if (response.ok) {
                    document.getElementById('rotateResult').innerHTML =
                        '<div class="success">' +
                        '<strong>✅ Key Rotated Successfully!</strong><br>' +
                        '<p style="margin:10px 0"><strong>⚠️ NEW KEY (save it now):</strong></p>' +
                        '<div class="key-display">' + data.new_key + '</div>' +
                        '<p>Old key deprecated until: ' + data.old_key_deprecated_until + '</p>' +
                        '<p>Update your dashboard to use the new key before grace period expires.</p>' +
                        '</div>';
                    listKeys();
                } else {
                    document.getElementById('rotateResult').innerHTML =
                        '<div class="error">❌ Error: ' + data.error + '</div>';
                }
            } catch (e) {
                document.getElementById('rotateResult').innerHTML =
                    '<div class="error">❌ Error: ' + e.message + '</div>';
            }
        }

        async function revokeKey(keyHash, keyName) {
            if (!confirm('Are you sure you want to revoke key: ' + keyName + '?')) {
                return;
            }

            const masterKey = getMasterKey();
            if (!masterKey) return;

            try {
                const response = await fetch(API_BASE + '/manage/revoke-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Master-Key': masterKey
                    },
                    body: JSON.stringify({ key_hash: keyHash })
                });

                const data = await response.json();

                if (response.ok) {
                    alert('✅ Key revoked successfully');
                    listKeys();
                } else {
                    alert('❌ Error: ' + data.error);
                }
            } catch (e) {
                alert('❌ Error: ' + e.message);
            }
        }

        async function listKeys() {
            const masterKey = getMasterKey();
            if (!masterKey) return;

            try {
                const response = await fetch(API_BASE + '/manage/list-keys', {
                    method: 'GET',
                    headers: {
                        'X-Master-Key': masterKey
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    let html = '<p>Total keys: ' + data.total + '</p>';

                    data.keys.forEach(key => {
                        const statusClass = key.status;
                        html += '<div class="key-item ' + statusClass + '">';
                        html += '<strong>' + key.name + '</strong> ';
                        html += '<span class="status ' + statusClass + '">' + key.status.toUpperCase() + '</span>';
                        html += '<br>';
                        html += '<small>Hash: <code>' + key.hash_short + '</code></small><br>';
                        html += '<small>Created: ' + key.created_at + '</small><br>';
                        html += '<small>Last used: ' + (key.last_used || 'Never') + ' (Count: ' + key.usage_count + ')</small><br>';
                        if (key.grace_until) {
                            html += '<small style="color: #ffc107;">⏳ Deprecated until: ' + key.grace_until + '</small><br>';
                        }
                        if (key.description) {
                            html += '<small>' + key.description + '</small><br>';
                        }
                        if (key.status !== 'revoked') {
                            html += '<button class="danger" style="margin-top: 10px;" onclick="revokeKey(\'' + key.hash + '\', \'' + key.name + '\')">🗑️ Revoke</button>';
                        }
                        html += '</div>';
                    });

                    document.getElementById('keysList').innerHTML = html;
                } else {
                    document.getElementById('keysList').innerHTML =
                        '<div class="error">❌ Error: ' + data.error + '</div>';
                }
            } catch (e) {
                document.getElementById('keysList').innerHTML =
                    '<div class="error">❌ Error: ' + e.message + '</div>';
            }
        }

        // Auto-load keys on page load if master key is entered
        window.onload = function() {
            const saved = localStorage.getItem('temp_master_key');
            if (saved) {
                document.getElementById('masterKey').value = saved;
            }

            // Save master key to localStorage temporarily for convenience (WARNING: not secure for production)
            document.getElementById('masterKey').addEventListener('change', function() {
                localStorage.setItem('temp_master_key', this.value);
            });
        };
    </script>
</body>
</html>
"""

@app.route('/manage', methods=['GET'])
def management_ui():
    """Simple web UI for key management"""
    return render_template_string(KEY_MANAGEMENT_UI)


# =============================================================================
# PROXY ENDPOINTS (same as before)
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (no auth required)"""
    return jsonify({
        "status": "healthy",
        "addon": "supervisor-api-gateway",
        "version": "1.0.0",
        "keys_active": sum(1 for k in keys_db.values() if k["status"] == "active")
    })


@app.route('/my-ip', methods=['GET'])
def get_my_ip():
    """
    Return the client's IP address (no auth required)
    Useful for determining which IP to add to the whitelist
    """
    client_ip = get_client_ip()

    response = {
        "your_ip": client_ip,
        "headers": {
            "X-Forwarded-For": request.headers.get('X-Forwarded-For'),
            "X-Real-IP": request.headers.get('X-Real-IP'),
            "Remote-Addr": request.remote_addr
        },
        "help": "Add this IP to your ip_whitelist configuration in the addon settings"
    }

    # Warn if private IP detected
    if is_private_ip(client_ip):
        response["warning"] = "Private IP detected! You are accessing from internal network."
        response["suggestion"] = "Access via your Nabu Casa URL (https://xxxxx.ui.nabu.casa:8099/my-ip) to see your real external IP for whitelisting."

    return jsonify(response)


@app.route('/addons', methods=['GET'])
@security_middleware
def get_addons():
    """Get list of all addons"""
    try:
        response = requests.get(
            f"{SUPERVISOR_URL}/addons",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=10
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/addons/<addon_slug>', methods=['GET'])
@security_middleware
def get_addon_info(addon_slug):
    """Get specific addon information"""
    try:
        response = requests.get(
            f"{SUPERVISOR_URL}/addons/{addon_slug}/info",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=10
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/addons/<addon_slug>/update', methods=['POST'])
@security_middleware
def update_addon(addon_slug):
    """Update an addon"""
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/addons/{addon_slug}/update",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/addons/<addon_slug>/start', methods=['POST'])
@security_middleware
def start_addon(addon_slug):
    """Start an addon"""
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/addons/{addon_slug}/start",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=60
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/addons/<addon_slug>/stop', methods=['POST'])
@security_middleware
def stop_addon(addon_slug):
    """Stop an addon"""
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/addons/{addon_slug}/stop",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=60
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/addons/<addon_slug>/restart', methods=['POST'])
@security_middleware
def restart_addon(addon_slug):
    """Restart an addon"""
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/addons/{addon_slug}/restart",
            headers={"Authorization": f"Bearer {SUPERVISOR_TOKEN}"},
            timeout=60
        )
        return Response(response.content, status=response.status_code, content_type='application/json')
    except Exception as e:
        logger.error(f"Error proxying to Supervisor API: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    """Block all non-whitelisted endpoints"""
    return jsonify({
        "error": "Endpoint not allowed",
        "message": "This endpoint is not exposed through the gateway"
    }), 403


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Supervisor API Gateway V1 Starting")
    logger.info("=" * 60)
    logger.warning("WARNING: This addon exposes Supervisor API externally")
    logger.warning("Ensure proper security configuration before use")
    logger.info("=" * 60)

    # Load configuration
    if not load_config():
        logger.critical("Failed to load configuration. Exiting.")
        exit(1)

    # Load keys database
    load_keys_db()

    # Migrate legacy keys if needed
    migrate_legacy_keys()

    # Cleanup expired deprecated keys
    cleanup_expired_keys()

    # Validate configuration
    if not keys_db:
        logger.critical("NO API KEYS CONFIGURED!")
        logger.critical("Use the management UI at /manage to generate keys")
        logger.critical("Or add legacy keys to config and restart")

    if not config.get('ip_whitelist'):
        logger.warning("NO IP WHITELIST CONFIGURED!")
        logger.warning("Consider adding IP whitelist for extra security")

    if not SUPERVISOR_TOKEN:
        logger.critical("SUPERVISOR_TOKEN not found!")
        logger.critical("Checked locations:")
        logger.critical("  - Environment: SUPERVISOR_TOKEN")
        logger.critical("  - Environment: HASSIO_TOKEN")
        logger.critical("  - File: /run/secrets/SUPERVISOR_TOKEN")
        logger.critical("")
        logger.critical("ALL available environment variables:")
        for key in sorted(os.environ.keys()):
            value = os.environ[key]
            # Truncate long values
            if len(value) > 50:
                value = value[:50] + "..."
            logger.critical(f"  {key} = {value}")
        logger.critical("")
        logger.critical("Troubleshooting:")
        logger.critical("1. Verify config.yaml has 'hassio_api: true'")
        logger.critical("2. Verify addon has been fully restarted")
        logger.critical("3. Check Home Assistant Supervisor logs")
        logger.critical("4. Try rebuilding the addon")
        logger.warning("Attempting to continue WITHOUT token (might fail)...")
        # Don't exit, let's try to continue and see what happens
        # exit(1)

    logger.info("Security configuration:")
    logger.info(f"  - Active Keys: {sum(1 for k in keys_db.values() if k['status'] == 'active')}")
    logger.info(f"  - Deprecated Keys: {sum(1 for k in keys_db.values() if k['status'] == 'deprecated')}")
    logger.info(f"  - Revoked Keys: {sum(1 for k in keys_db.values() if k['status'] == 'revoked')}")
    logger.info(f"  - IP Whitelist: {len(config.get('ip_whitelist', []))} IPs")
    logger.info(f"  - Rate Limit: {config.get('rate_limit_per_minute')}/min, {config.get('rate_limit_per_hour')}/hour")
    logger.info(f"  - Master Key Set: {'Yes' if config.get('master_key') else 'No (required for key management)'}")
    logger.info(f"  - Management UI: http://YOUR_HA_IP:8099/manage")

    logger.info("=" * 60)
    logger.info("Starting Flask server on 0.0.0.0:8099")
    logger.info("=" * 60)

    app.run(host='0.0.0.0', port=8099, debug=False)
