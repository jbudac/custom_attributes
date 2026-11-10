"""Date & time parameters."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import CustomParamsConfigEntry
from .const import TYPE_DATETIME
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(
        entry, hass, async_add_entities, TYPE_DATETIME, CustomParamDateTime
    )


class CustomParamDateTime(CustomParamEntity, DateTimeEntity):
    @property
    def native_value(self) -> datetime | None:
        if not self._raw_value:
            return None
        parsed = dt_util.parse_datetime(str(self._raw_value))
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
        return parsed

    async def async_set_value(self, value: datetime) -> None:
        self._save_raw_value(dt_util.as_utc(value).isoformat())
