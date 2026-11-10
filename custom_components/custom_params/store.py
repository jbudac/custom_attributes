"""Persistent storage of parameter values."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

_DATA_STORE = f"{DOMAIN}_store"


class ValueStore:
    """Keeps values as {subentry_id: {target_key: value}}.

    One instance lives for the whole HA run (not per config entry load), so that
    a pending delayed save is never lost when the entry is reloaded.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, dict[str, Any]]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )
        self.data: dict[str, dict[str, Any]] = {}
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        self.data = await self._store.async_load() or {}
        self._loaded = True

    def get(self, subentry_id: str, target_key: str) -> Any:
        return self.data.get(subentry_id, {}).get(target_key)

    def set(self, subentry_id: str, target_key: str, value: Any) -> None:
        values = self.data.setdefault(subentry_id, {})
        if value is None:
            values.pop(target_key, None)
        else:
            values[target_key] = value
        self._schedule_save()

    def prune(self, valid_subentry_ids: set[str]) -> None:
        """Drop values of parameters that no longer exist."""
        stale = [sid for sid in self.data if sid not in valid_subentry_ids]
        if not stale:
            return
        for sid in stale:
            del self.data[sid]
        self._schedule_save()

    async def async_remove(self) -> None:
        self.data = {}
        await self._store.async_remove()

    def _schedule_save(self) -> None:
        self._store.async_delay_save(lambda: self.data, 1)


async def async_get_store(hass: HomeAssistant) -> ValueStore:
    if (store := hass.data.get(_DATA_STORE)) is None:
        store = hass.data[_DATA_STORE] = ValueStore(hass)
    await store.async_load()
    return store
