"""Platform for number integration."""
from __future__ import annotations

import logging
import asyncio

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
)
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
    """Set up Chlorinator number entities from a config entry."""
    data: ChlorinatorData = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ChlorinatorPhSetpoint(data.coordinator),
        ChlorinatorChlorineSetpoint(data.coordinator),
        ChlorinatorAcidDosingInhibitPeriod(data.coordinator),
    ]
    async_add_entities(entities)


class ChlorinatorPhSetpoint(
    CoordinatorEntity[ChlorinatorDataUpdateCoordinator], NumberEntity
):
    """Number entity for pH setpoint."""

    _attr_icon = "mdi:ph"
    _attr_name = "pH Setpoint"
    _attr_unique_id = "pool01_ph_setpoint_number"
    _attr_native_min_value = 6.0
    _attr_native_max_value = 8.0
    _attr_native_step = 0.1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator: ChlorinatorDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo | None:
        return DEVICE_INFO

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("ph_control_setpoint")

    async def async_set_native_value(self, value: float) -> None:
        """Set the pH setpoint."""
        async with self.coordinator._ble_lock:
            await self.coordinator.chlorinator.async_write_setup(
                ph_control_setpoint=round(value, 1)
            )
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class ChlorinatorChlorineSetpoint(
    CoordinatorEntity[ChlorinatorDataUpdateCoordinator], NumberEntity
):
    """Number entity for chlorine output setpoint (manual mode, 0-8)."""

    _attr_icon = "mdi:beaker-check-outline"
    _attr_name = "Chlorine Output"
    _attr_unique_id = "pool01_chlorine_setpoint_number"
    _attr_native_min_value = 0
    _attr_native_max_value = 8
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator: ChlorinatorDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo | None:
        return DEVICE_INFO

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("chlorine_control_setpoint")

    async def async_set_native_value(self, value: float) -> None:
        """Set the chlorine output level."""
        async with self.coordinator._ble_lock:
            await self.coordinator.chlorinator.async_write_setup(
                chlorine_control_setpoint=int(value)
            )
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class ChlorinatorAcidDosingInhibitPeriod(
    CoordinatorEntity[ChlorinatorDataUpdateCoordinator], NumberEntity
):
    """Number entity for acid dosing inhibit period in minutes."""

    _attr_icon = "mdi:timer-outline"
    _attr_name = "Acid Dosing Inhibit Period"
    _attr_unique_id = "pool01_acid_dosing_inhibit_period_number"
    _attr_native_min_value = 0
    _attr_native_max_value = 1440
    _attr_native_step = 15
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator: ChlorinatorDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo | None:
        return DEVICE_INFO

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("acid_dosing_inhibit_time_remaining")

    async def async_set_native_value(self, value: float) -> None:
        """Set the acid dosing inhibit period."""
        from pychlorinator.chlorinator_parsers import ChlorinatorActions
        async with self.coordinator._ble_lock:
            await self.coordinator.chlorinator.async_write_action(
                ChlorinatorActions.DisableAcidDosingForPeriod,
                period_minutes=int(value),
            )
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()