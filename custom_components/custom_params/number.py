"""Number parameters."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import (
    CONF_MAX,
    CONF_MIN,
    CONF_MODE,
    CONF_STEP,
    CONF_UNIT,
    DEFAULT_MAX,
    DEFAULT_MIN,
    DEFAULT_STEP,
    TYPE_NUMBER,
)
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(entry, hass, async_add_entities, TYPE_NUMBER, CustomParamNumber)


class CustomParamNumber(CustomParamEntity, NumberEntity):
    _native_unit_supported = True

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._attr_native_min_value = float(self._param.get(CONF_MIN, DEFAULT_MIN))
        self._attr_native_max_value = float(self._param.get(CONF_MAX, DEFAULT_MAX))
        self._attr_native_step = float(self._param.get(CONF_STEP, DEFAULT_STEP))
        self._attr_mode = NumberMode(self._param.get(CONF_MODE, NumberMode.BOX))
        self._attr_native_unit_of_measurement = self._param.get(CONF_UNIT) or None

    @property
    def native_value(self) -> float | None:
        try:
            return float(self._raw_value) if self._raw_value is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        self._save_raw_value(value)
