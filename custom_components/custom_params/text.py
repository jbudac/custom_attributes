"""Text parameters."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import CONF_MAX_LENGTH, DEFAULT_MAX_LENGTH, TYPE_TEXT
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(entry, hass, async_add_entities, TYPE_TEXT, CustomParamText)


class CustomParamText(CustomParamEntity, TextEntity):
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._attr_native_max = int(self._param.get(CONF_MAX_LENGTH, DEFAULT_MAX_LENGTH))

    @property
    def native_value(self) -> str | None:
        raw = self._raw_value
        return None if raw is None else str(raw)

    async def async_set_value(self, value: str) -> None:
        self._save_raw_value(value if value != "" else None)
