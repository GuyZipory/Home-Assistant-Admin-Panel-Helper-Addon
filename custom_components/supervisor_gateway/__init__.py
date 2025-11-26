"""Supervisor Gateway API Integration."""
import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "supervisor_gateway"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("api_key"): cv.string,
                vol.Optional("ip_whitelist", default=[]): vol.All(cv.ensure_list, [cv.string]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Supervisor Gateway component."""
    from . import api

    # Store config
    conf = config.get(DOMAIN, {})
    hass.data[DOMAIN] = {
        "api_key": conf.get("api_key"),
        "ip_whitelist": conf.get("ip_whitelist", [])
    }

    # Register API views
    await api.async_setup(hass)

    _LOGGER.info("Supervisor Gateway API endpoints registered with required x-api-key protection")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True
