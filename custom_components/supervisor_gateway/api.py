"""API views for Supervisor Gateway."""
import logging
import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_URL = "http://supervisor"


async def async_setup(hass: HomeAssistant):
    """Set up API views."""
    hass.http.register_view(SupervisorGatewayView(hass))
    hass.http.register_view(SupervisorGatewayHealthView(hass))
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
            "version": "2.0.0",
            "available_endpoints": {
                "utility": [
                    "GET /api/supervisor_gateway/health",
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
            "authentication": "Use your Home Assistant long-lived access token"
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
            "version": "2.0.0"
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
        try:
            supervisor_token = self.hass.data.get("hassio_auth_token") or request.headers.get("X-Supervisor-Token")

            if not supervisor_token:
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
        try:
            supervisor_token = self.hass.data.get("hassio_auth_token") or request.headers.get("X-Supervisor-Token")

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
        allowed_actions = ["update", "start", "stop", "restart"]

        if action not in allowed_actions:
            return self.json_message(f"Invalid action. Allowed: {', '.join(allowed_actions)}", 400)

        try:
            supervisor_token = self.hass.data.get("hassio_auth_token") or request.headers.get("X-Supervisor-Token")

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
