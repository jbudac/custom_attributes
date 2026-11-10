"""Date parameters."""

from __future__ import annotations

from datetime import date

from homeassistant.components.date import DateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import TYPE_DATE
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(entry, hass, async_add_entities, TYPE_DATE, CustomParamDate)


class CustomParamDate(CustomParamEntity, DateEntity):
    @property
    def native_value(self) -> date | None:
        try:
            return date.fromisoformat(str(self._raw_value)[:10]) if self._raw_value else None
        except ValueError:
            return None

    async def async_set_value(self, value: date) -> None:
        self._save_raw_value(value.isoformat())
