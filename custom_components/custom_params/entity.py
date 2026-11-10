"""Base entity for parameter values."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CustomParamsConfigEntry
from .const import CONF_ICON, CONF_KEY, CONF_NAME, CONF_TYPE, CONF_UNIT
from .store import ValueStore
from .targets import Target


class CustomParamEntity(Entity):
    """Holds the value of one parameter for one device or entity."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        hass: HomeAssistant,
        subentry: ConfigSubentry,
        target: Target,
        store: ValueStore,
    ) -> None:
        self._store = store
        self._subentry_id = subentry.subentry_id
        self._param: dict[str, Any] = dict(subentry.data)
        self._target = target
        param_name: str = self._param[CONF_NAME]

        self._attr_unique_id = f"{subentry.subentry_id}_{target.key}"
        if icon := self._param.get(CONF_ICON):
            self._attr_icon = icon

        device = dr.async_get(hass).async_get(target.device_id) if target.device_id else None
        if device is not None:
            # Link to the existing device without taking ownership of it.
            self.device_entry = device
            self._attr_has_entity_name = True
            self._attr_name = (
                f"{target.entity_name} {param_name}" if target.entity_name else param_name
            )
        else:
            self._attr_has_entity_name = False
            self._attr_name = f"{target.entity_name} {param_name}"

        attrs: dict[str, Any] = {"parameter": self._param[CONF_KEY]}
        if target.entity_id:
            attrs["target_entity_id"] = target.entity_id
        if target.device_id:
            attrs["target_device_id"] = target.device_id
        if (unit := self._param.get(CONF_UNIT)) and not self._native_unit_supported:
            attrs["unit"] = unit
        self._attr_extra_state_attributes = attrs

    _native_unit_supported = False

    @property
    def _raw_value(self) -> Any:
        return self._store.get(self._subentry_id, self._target.key)

    def _save_raw_value(self, value: Any) -> None:
        self._store.set(self._subentry_id, self._target.key, value)
        self.async_write_ha_state()


def setup_platform_entities(
    entry: CustomParamsConfigEntry,
    hass: HomeAssistant,
    async_add_entities: AddConfigEntryEntitiesCallback,
    param_type: str,
    factory: Callable[[HomeAssistant, ConfigSubentry, Target, ValueStore], Entity],
) -> None:
    """Add entities of one parameter type, grouped under their subentry."""
    runtime = entry.runtime_data
    for subentry in entry.subentries.values():
        if subentry.data.get(CONF_TYPE) != param_type:
            continue
        targets = runtime.targets.get(subentry.subentry_id, [])
        if not targets:
            continue
        async_add_entities(
            [factory(hass, subentry, target, runtime.store) for target in targets],
            config_subentry_id=subentry.subentry_id,
        )
