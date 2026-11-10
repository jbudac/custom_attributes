"""Boolean (yes/no) parameters."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import TYPE_BOOLEAN
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(
        entry, hass, async_add_entities, TYPE_BOOLEAN, CustomParamSwitch
    )


class CustomParamSwitch(CustomParamEntity, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value
        return None if raw is None else bool(raw)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._save_raw_value(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._save_raw_value(False)
