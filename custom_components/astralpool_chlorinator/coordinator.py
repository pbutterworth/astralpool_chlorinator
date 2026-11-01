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
from homeassistant.util import dt as dt_util

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

    # BLE reads intermittently return garbled data (e.g. "N is not a valid
    # Modes"), which used to mark every entity unavailable for a poll.
    # Retry once, then keep serving the last good data until failures have
    # persisted for MAX_STALE.
    RETRY_DELAY = 3  # seconds before the in-poll retry
    MAX_STALE = timedelta(minutes=5)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with self._ble_lock:
            last_exc = None
            for attempt in (1, 2):
                try:
                    data = await self.chlorinator.async_gatherdata()
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    _LOGGER.debug("Failed _gatherdata (attempt %s): %s", attempt, exc)
                    if attempt == 1:
                        await asyncio.sleep(self.RETRY_DELAY)
                    continue
                if data != {}:
                    self.data = data
                    self._last_success = dt_util.utcnow()
                    self._consecutive_failures = 0
                return self.data

            self._consecutive_failures = getattr(self, "_consecutive_failures", 0) + 1
            last_success = getattr(self, "_last_success", None)
            if (
                self.data
                and last_success is not None
                and dt_util.utcnow() - last_success < self.MAX_STALE
            ):
                _LOGGER.info(
                    "Chlorinator read failed (%s in a row), keeping last good data: %s",
                    self._consecutive_failures,
                    last_exc,
                )
                return self.data
            _LOGGER.warning(
                "Failed _gatherdata %s times in a row: %s",
                self._consecutive_failures,
                last_exc,
                exc_info=last_exc,
            )
            raise UpdateFailed("Error communicating with API") from last_exc
