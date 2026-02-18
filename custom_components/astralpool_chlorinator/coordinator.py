"""Data coordinator for receiving Chlorinator updates."""

from datetime import timedelta
import logging
from typing import Any

from pychlorinator.chlorinator import ChlorinatorAPI

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ChlorinatorDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data coordinator for getting Chlorinator updates."""

    def __init__(self, hass: HomeAssistant, chlorinator: ChlorinatorAPI) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.data = {}
        self.chlorinator = chlorinator
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, "1234")},
            manufacturer="Astral Pool",
            name="POOL01",
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            data = await self.chlorinator.async_gatherdata()
        except Exception as exc:
            _LOGGER.warning("Failed _gatherdata")
            data = {}
            raise UpdateFailed("Error communicating with API") from exc
        if data != {}:
            self.data = data
        return self.data
