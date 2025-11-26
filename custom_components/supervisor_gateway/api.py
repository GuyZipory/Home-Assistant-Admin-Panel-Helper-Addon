"""API views for Supervisor Gateway."""
import logging
import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "supervisor_gateway"
SUPERVISOR_URL = "http://supervisor"


def validate_api_key(hass: HomeAssistant, request) -> bool:
    """Validate x-api-key header (required)."""
    if DOMAIN not in hass.data:
        _LOGGER.error("Supervisor Gateway not configured - api_key required in configuration.yaml")
        return False

    configured_key = hass.data[DOMAIN].get("api_key")
    if not configured_key:
        _LOGGER.error("api_key not configured in configuration.yaml - this is required")
        return False

    # Check x-api-key header
    provided_key = request.headers.get("x-api-key")
    if not provided_key:
        _LOGGER.warning(f"Missing x-api-key header from {request.remote}")
        return False

    if provided_key != configured_key:
        _LOGGER.warning(f"Invalid x-api-key from {request.remote}")
        return False

    return True


def get_client_ip(request) -> str:
    """Get real client IP from request headers (Nabu Casa compatible)."""
    # Check X-Forwarded-For header (Nabu Casa uses this)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # First IP is the original client
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (alternative)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to request.remote (direct connection)
    return request.remote


def validate_ip_whitelist(hass: HomeAssistant, request) -> bool:
    """Validate client IP against whitelist if configured."""
    if DOMAIN not in hass.data:
        return True

    whitelist = hass.data[DOMAIN].get("ip_whitelist", [])
    if not whitelist or len(whitelist) == 0:
        return True  # No whitelist = allow all (optional feature)

    client_ip = get_client_ip(request)
    if client_ip not in whitelist:
        _LOGGER.warning(f"Public IP {client_ip} not in whitelist - access denied")
        return False

    _LOGGER.debug(f"Public IP {client_ip} validated against whitelist")
    return True


async def async_setup(hass: HomeAssistant):
    """Set up API views."""
    hass.http.register_view(SupervisorGatewayView())
    hass.http.register_view(SupervisorGatewayHealthView())
    hass.http.register_view(SupervisorGatewayMyIPView())
    hass.http.register_view(SupervisorGatewayAddonsView(hass))
    hass.http.register_view(SupervisorGatewayAddonView(hass))
    hass.http.register_view(SupervisorGatewayAddonActionView(hass))


class SupervisorGatewayView(HomeAssistantView):
    """Root API view."""

    url = "/api/supervisor_gateway"
    name = "api:supervisor_gateway"
    requires_auth = True

    async def get(self, request):
        """Handle GET request."""
        return self.json({
            "message": "Supervisor Gateway API",
            "version": "3.1.0",
            "available_endpoints": {
                "utility": [
                    "GET /api/supervisor_gateway/health",
                    "GET /api/supervisor_gateway/my-ip",
                ],
                "addon_management": [
                    "GET /api/supervisor_gateway/addons",
                    "GET /api/supervisor_gateway/addons/{slug}",
                    "POST /api/supervisor_gateway/addons/{slug}/update",
                    "POST /api/supervisor_gateway/addons/{slug}/start",
                    "POST /api/supervisor_gateway/addons/{slug}/stop",
                    "POST /api/supervisor_gateway/addons/{slug}/restart"
                ]
            },
            "authentication": {
                "ha_token": "Required - Use 'Authorization: Bearer YOUR_HA_TOKEN' header",
                "x_api_key": "Required - Use 'x-api-key: YOUR_API_KEY' header - Must be configured in configuration.yaml"
            }
        })


class SupervisorGatewayHealthView(HomeAssistantView):
    """Health check view."""

    url = "/api/supervisor_gateway/health"
    name = "api:supervisor_gateway:health"
    requires_auth = False  # Allow health checks without auth

    async def get(self, request):
        """Handle GET request."""
        return self.json({
            "status": "healthy",
            "service": "supervisor-gateway",
            "version": "3.1.0"
        })


class SupervisorGatewayMyIPView(HomeAssistantView):
    """My IP helper view - shows public IP for whitelist configuration."""

    url = "/api/supervisor_gateway/my-ip"
    name = "api:supervisor_gateway:my_ip"
    requires_auth = True  # HA token required, NOT x-api-key

    async def get(self, request):
        """Return client's public IP address."""
        client_ip = get_client_ip(request)

        # Determine source of IP
        if request.headers.get("X-Forwarded-For"):
            source = "X-Forwarded-For"
        elif request.headers.get("X-Real-IP"):
            source = "X-Real-IP"
        else:
            source = "request.remote"

        return self.json({
            "ip": client_ip,
            "message": "This is your public IP address. Add it to ip_whitelist in configuration.yaml if you want IP restrictions.",
            "source": source
        })


class SupervisorGatewayAddonsView(HomeAssistantView):
    """Addons list view."""

    url = "/api/supervisor_gateway/addons"
    name = "api:supervisor_gateway:addons"
    requires_auth = True

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        self.hass = hass

    async def get(self, request):
        """Handle GET request - list all addons."""
        # Validate IP whitelist if configured
        if not validate_ip_whitelist(self.hass, request):
            return self.json_message("Access denied: IP not whitelisted", 403)

        # Validate x-api-key header
        if not validate_api_key(self.hass, request):
            return self.json_message("Invalid or missing x-api-key header", 401)

        try:
            # Get supervisor token from environment or hassio data
            import os
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

            if not supervisor_token:
                # Try getting from hassio integration
                if "hassio" in self.hass.data:
                    supervisor_token = self.hass.data["hassio"].get("supervisor_token")

            if not supervisor_token:
                _LOGGER.error("Cannot access Supervisor token")
                return self.json_message("Supervisor token not available", 500)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SUPERVISOR_URL}/addons",
                    headers={"Authorization": f"Bearer {supervisor_token}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    return self.json(data, status_code=resp.status)

        except Exception as e:
            _LOGGER.error(f"Error fetching addons: {e}")
            return self.json_message(f"Error: {str(e)}", 500)


class SupervisorGatewayAddonView(HomeAssistantView):
    """Single addon view."""

    url = "/api/supervisor_gateway/addons/{addon_slug}"
    name = "api:supervisor_gateway:addon"
    requires_auth = True

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        self.hass = hass

    async def get(self, request, addon_slug):
        """Handle GET request - get addon info."""
        # Validate IP whitelist if configured
        if not validate_ip_whitelist(self.hass, request):
            return self.json_message("Access denied: IP not whitelisted", 403)

        # Validate x-api-key header
        if not validate_api_key(self.hass, request):
            return self.json_message("Invalid or missing x-api-key header", 401)

        try:
            # Get supervisor token from environment or hassio data
            import os
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

            if not supervisor_token and "hassio" in self.hass.data:
                supervisor_token = self.hass.data["hassio"].get("supervisor_token")

            if not supervisor_token:
                return self.json_message("Supervisor token not available", 500)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SUPERVISOR_URL}/addons/{addon_slug}/info",
                    headers={"Authorization": f"Bearer {supervisor_token}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    return self.json(data, status_code=resp.status)

        except Exception as e:
            _LOGGER.error(f"Error fetching addon {addon_slug}: {e}")
            return self.json_message(f"Error: {str(e)}", 500)


class SupervisorGatewayAddonActionView(HomeAssistantView):
    """Addon actions view."""

    url = "/api/supervisor_gateway/addons/{addon_slug}/{action}"
    name = "api:supervisor_gateway:addon:action"
    requires_auth = True

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        self.hass = hass

    async def post(self, request, addon_slug, action):
        """Handle POST request - perform addon action."""
        # Validate IP whitelist if configured
        if not validate_ip_whitelist(self.hass, request):
            return self.json_message("Access denied: IP not whitelisted", 403)

        # Validate x-api-key header
        if not validate_api_key(self.hass, request):
            return self.json_message("Invalid or missing x-api-key header", 401)

        allowed_actions = ["update", "start", "stop", "restart"]

        if action not in allowed_actions:
            return self.json_message(f"Invalid action. Allowed: {', '.join(allowed_actions)}", 400)

        try:
            # Get supervisor token from environment or hassio data
            import os
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

            if not supervisor_token and "hassio" in self.hass.data:
                supervisor_token = self.hass.data["hassio"].get("supervisor_token")

            if not supervisor_token:
                return self.json_message("Supervisor token not available", 500)

            # Use longer timeout for update operations
            timeout = 300 if action == "update" else 30

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SUPERVISOR_URL}/addons/{addon_slug}/{action}",
                    headers={"Authorization": f"Bearer {supervisor_token}"},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    data = await resp.json()
                    return self.json(data, status_code=resp.status)

        except Exception as e:
            _LOGGER.error(f"Error performing {action} on addon {addon_slug}: {e}")
            return self.json_message(f"Error: {str(e)}", 500)
