"""Supervisor Gateway API Integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "supervisor_gateway"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Supervisor Gateway component."""
    from . import api

    # Register API views
    await api.async_setup(hass)

    _LOGGER.info("Supervisor Gateway API endpoints registered")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True
