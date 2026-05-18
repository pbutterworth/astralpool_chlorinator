"""Data coordinator for receiving Chlorinator updates."""

from datetime import timedelta
import asyncio
import logging
from typing import Any

from pychlorinator.chlorinator import ChlorinatorAPI

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ChlorinatorDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data coordinator for getting Chlorinator updates."""

    def __init__(self, hass: HomeAssistant, chlorinator: ChlorinatorAPI, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        poll_interval = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.data = {}
        self._entry = entry
        self.chlorinator = chlorinator
        self._ble_lock = asyncio.Lock()
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, "1234")},
            manufacturer="Astral Pool",
            name="POOL01",
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with self._ble_lock:
            try:
                data = await self.chlorinator.async_gatherdata()
            except Exception as exc:
                _LOGGER.warning("Failed _gatherdata: %s", exc, exc_info=True)
                data = {}
                raise UpdateFailed("Error communicating with API") from exc
            if data != {}:
                self.data = data
            return self.data