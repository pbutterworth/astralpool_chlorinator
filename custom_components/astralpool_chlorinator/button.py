"""Platform for button integration."""
from __future__ import annotations

import logging

from pychlorinator.chlorinator_parsers import ChlorinatorActions

from homeassistant.components.button import ButtonEntity
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChlorinatorDataUpdateCoordinator
from .models import ChlorinatorData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_INFO = {
    "identifiers": {(DOMAIN, "POOL01")},
    "name": "POOL01",
    "model": "Viron eQuilibrium",
    "manufacturer": "Astral Pool",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chlorinator button entities from a config entry."""
    data: ChlorinatorData = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ChlorinatorDismissInfoMessageButton(data.coordinator),
        ChlorinatorDisableAcidDosingIndefinitelyButton(data.coordinator),
        ChlorinatorReenableAcidDosingButton(data.coordinator),
        ChlorinatorResetStatisticsButton(data.coordinator),
        ChlorinatorTriggerCellReversalButton(data.coordinator),
    ]
    async_add_entities(entities)


class ChlorinatorButtonBase(
    CoordinatorEntity[ChlorinatorDataUpdateCoordinator], ButtonEntity
):
    """Base class for Chlorinator button entities."""

    _action: ChlorinatorActions = ChlorinatorActions.NoAction

    def __init__(self, coordinator: ChlorinatorDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo | None:
        return DEVICE_INFO

    async def async_press(self) -> None:
        """Handle the button press."""
        async with self.coordinator._ble_lock:
            await self.coordinator.chlorinator.async_write_action(self._action)
        await self.coordinator.async_request_refresh()


class ChlorinatorDismissInfoMessageButton(ChlorinatorButtonBase):
    """Button to dismiss the current info message."""

    _attr_icon = "mdi:close-circle-outline"
    _attr_name = "Dismiss Info Message"
    _attr_unique_id = "pool01_dismiss_info_message_button"
    _action = ChlorinatorActions.DismissInfoMessage


class ChlorinatorDisableAcidDosingIndefinitelyButton(ChlorinatorButtonBase):
    """Button to disable acid dosing indefinitely."""

    _attr_icon = "mdi:beaker-off-outline"
    _attr_name = "Disable Acid Dosing"
    _attr_unique_id = "pool01_disable_acid_dosing_indefinitely_button"
    _action = ChlorinatorActions.DisableAcidDosingIndefinitely


class ChlorinatorReenableAcidDosingButton(ChlorinatorButtonBase):
    """Button to re-enable acid dosing by sending period=0."""

    _attr_icon = "mdi:beaker-check-outline"
    _attr_name = "Re-enable Acid Dosing"
    _attr_unique_id = "pool01_reenable_acid_dosing_button"

    async def async_press(self) -> None:
        """Send DisableAcidDosingForPeriod with period=0 to cancel inhibit."""
        async with self.coordinator._ble_lock:
            await self.coordinator.chlorinator.async_write_action(
                ChlorinatorActions.DisableAcidDosingForPeriod,
                period_minutes=0,
            )
        await self.coordinator.async_request_refresh()


class ChlorinatorResetStatisticsButton(ChlorinatorButtonBase):
    """Button to reset chlorinator statistics."""

    _attr_icon = "mdi:chart-bar"
    _attr_name = "Reset Statistics"
    _attr_unique_id = "pool01_reset_statistics_button"
    _action = ChlorinatorActions.ResetStatistics


class ChlorinatorTriggerCellReversalButton(ChlorinatorButtonBase):
    """Button to trigger cell reversal."""

    _attr_icon = "mdi:swap-horizontal"
    _attr_name = "Trigger Cell Reversal"
    _attr_unique_id = "pool01_trigger_cell_reversal_button"
    _action = ChlorinatorActions.TriggerCellReversal