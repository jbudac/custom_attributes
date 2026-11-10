"""Selection (list of options) parameters."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import CONF_OPTIONS, TYPE_SELECT
from .entity import CustomParamEntity, setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CustomParamsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    setup_platform_entities(
        entry, hass, async_add_entities, TYPE_SELECT, CustomParamSelect
    )


class CustomParamSelect(CustomParamEntity, SelectEntity):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._attr_options = [str(o) for o in self._param.get(CONF_OPTIONS, [])]

    @property
    def current_option(self) -> str | None:
        raw = self._raw_value
        return raw if raw in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        self._save_raw_value(option)
