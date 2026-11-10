"""Custom Parameters: user-defined parameters attached to devices and entities."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_call_later

from .const import CONF_TYPE, DOMAIN, PLATFORMS, SUBENTRY_TYPE, TYPE_TO_PLATFORM
from .store import ValueStore, async_get_store
from .targets import Target, compute_targets

_LOGGER = logging.getLogger(__name__)

REGISTRY_DEBOUNCE_SECONDS = 5


@dataclass
class RuntimeData:
    store: ValueStore
    targets: dict[str, list[Target]] = field(default_factory=dict)


type CustomParamsConfigEntry = ConfigEntry[RuntimeData]


def _parameter_subentries(entry: ConfigEntry):
    return [
        sub for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE
    ]


def _compute_all_targets(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, list[Target]]:
    return {
        sub.subentry_id: compute_targets(hass, sub.data)
        for sub in _parameter_subentries(entry)
    }


@callback
def _async_remove_stale_entities(
    hass: HomeAssistant, entry: ConfigEntry, targets: dict[str, list[Target]]
) -> None:
    """Remove value entities whose target or parameter no longer exists."""
    ent_reg = er.async_get(hass)
    expected: set[tuple[str, str]] = set()
    for sub in _parameter_subentries(entry):
        platform = TYPE_TO_PLATFORM[sub.data[CONF_TYPE]]
        for target in targets.get(sub.subentry_id, []):
            expected.add((str(platform), f"{sub.subentry_id}_{target.key}"))

    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if (reg_entry.domain, reg_entry.unique_id) not in expected:
            _LOGGER.debug("Removing stale parameter entity %s", reg_entry.entity_id)
            ent_reg.async_remove(reg_entry.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: CustomParamsConfigEntry) -> bool:
    store = await async_get_store(hass)
    store.prune({sub.subentry_id for sub in _parameter_subentries(entry)})

    targets = _compute_all_targets(hass, entry)
    entry.runtime_data = RuntimeData(store=store, targets=targets)

    _async_remove_stale_entities(hass, entry, targets)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _async_watch_registries(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CustomParamsConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Integration removed completely: drop stored values."""
    store = await async_get_store(hass)
    await store.async_remove()


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """A parameter was added, edited or deleted."""
    hass.config_entries.async_schedule_reload(entry.entry_id)


@callback
def _async_watch_registries(hass: HomeAssistant, entry: CustomParamsConfigEntry) -> None:
    """Reload when devices/entities appear, disappear or get renamed."""
    cancel_timer: CALLBACK_TYPE | None = None

    @callback
    def _check(_now=None) -> None:
        nonlocal cancel_timer
        cancel_timer = None
        if _compute_all_targets(hass, entry) != entry.runtime_data.targets:
            _LOGGER.debug("Targets changed, reloading %s", entry.entry_id)
            hass.config_entries.async_schedule_reload(entry.entry_id)

    @callback
    def _schedule(event: Event) -> None:
        nonlocal cancel_timer
        # Ignore changes of our own entities
        if (
            event.event_type == er.EVENT_ENTITY_REGISTRY_UPDATED
            and event.data.get("entity_id")
        ):
            reg_entry = er.async_get(hass).async_get(event.data["entity_id"])
            if reg_entry is not None and reg_entry.platform == DOMAIN:
                return
        if cancel_timer is not None:
            cancel_timer()
        cancel_timer = async_call_later(hass, REGISTRY_DEBOUNCE_SECONDS, _check)

    @callback
    def _cancel() -> None:
        if cancel_timer is not None:
            cancel_timer()

    entry.async_on_unload(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _schedule)
    )
    entry.async_on_unload(
        hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, _schedule)
    )
    entry.async_on_unload(_cancel)
