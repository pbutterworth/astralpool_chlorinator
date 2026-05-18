"""The Astral Pool Viron eQuilibrium Chlorinator BLE integration."""

from __future__ import annotations

import logging

from bleak_retry_connector import get_device
from pychlorinator.chlorinator import ChlorinatorAPI

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import ChlorinatorDataUpdateCoordinator
from .models import ChlorinatorData

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chlorinator from a config entry."""

    address: str = entry.data[CONF_ADDRESS]
    accesscode: str = entry.data[CONF_ACCESS_TOKEN]
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), True
    ) or await get_device(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find chlorinator device with address {address}"
        )

    _LOGGER.debug("async_setup_entry address:  %s accesscode %s", address, accesscode)

    chlorinator = ChlorinatorAPI(ble_device, accesscode)
    coordinator = ChlorinatorDataUpdateCoordinator(hass, chlorinator, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ChlorinatorData(
        entry.title, chlorinator, coordinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Add listener to reload entry when options change
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = True
    for platform in PLATFORMS:
        if not await hass.config_entries.async_forward_entry_unload(entry, platform):
            unload_ok = False

    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)