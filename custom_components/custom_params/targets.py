"""Resolve which devices / entities a parameter applies to."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import CONF_DOMAINS, DOMAIN, TARGET_DEVICE, TARGET_ENTITY, get_targets


@dataclass(frozen=True, slots=True)
class Target:
    """A device or entity that gets a parameter value."""

    key: str  # stable storage key: "device_<device id>" / "entity_<registry id>"
    device_id: str | None  # device the value entity is attached to
    entity_id: str | None  # source entity (entity mode only)
    entity_name: str | None  # name of the source entity (entity mode only)
    suffix: str | None = None  # appended after the parameter name


def _entity_display_name(hass: HomeAssistant, entry: er.RegistryEntry) -> str:
    if entry.name:
        return entry.name
    if (state := hass.states.get(entry.entity_id)) is not None:
        if friendly := state.attributes.get("friendly_name"):
            return str(friendly)
    return entry.original_name or entry.entity_id


def compute_targets(hass: HomeAssistant, data: Mapping[str, Any]) -> list[Target]:
    """Return the targets for one parameter definition."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    domains = set(data.get(CONF_DOMAINS) or [])

    entries = [
        entry
        for entry in ent_reg.entities.values()
        if entry.platform != DOMAIN
        and entry.domain in domains
        and entry.disabled_by is None
    ]

    kinds = get_targets(data)
    targets: list[Target] = []

    if TARGET_DEVICE in kinds:
        seen: set[str] = set()
        for entry in entries:
            if not entry.device_id or entry.device_id in seen:
                continue
            seen.add(entry.device_id)
            device = dev_reg.async_get(entry.device_id)
            if device is None or device.disabled:
                continue
            targets.append(
                Target(
                    key=f"device_{device.id}",
                    device_id=device.id,
                    entity_id=None,
                    entity_name=None,
                )
            )

    if TARGET_ENTITY in kinds:
        both = TARGET_DEVICE in kinds
        for entry in entries:
            device_id = entry.device_id
            if device_id and (device := dev_reg.async_get(device_id)) is not None:
                if device.disabled:
                    continue
                # Name relative to the device ("Ceiling" -> "<Device> Ceiling <param>")
                entity_name = entry.name or entry.original_name
                suffix = None
                if entity_name is None and both:
                    # Main entity of the device: tell it apart from the device value
                    suffix = f"({entry.entity_id})"
            else:
                device_id = None
                entity_name = _entity_display_name(hass, entry)
                suffix = None
            targets.append(
                Target(
                    key=f"entity_{entry.id}",
                    device_id=device_id,
                    entity_id=entry.entity_id,
                    entity_name=entity_name,
                    suffix=suffix,
                )
            )

    return sorted(targets, key=lambda t: t.key)
