from datetime import timedelta

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.custom_params.const import DOMAIN, SUBENTRY_TYPE


def _make_device(hass, src_entry, name, domain, uid):
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    dev = dev_reg.async_get_or_create(
        config_entry_id=src_entry.entry_id, identifiers={("demo", uid)}, name=name
    )
    ent = ent_reg.async_get_or_create(
        domain, "demo", uid, device_id=dev.id, config_entry=src_entry,
        has_entity_name=True, original_name=None,
    )
    return dev, ent


async def _setup(hass: HomeAssistant):
    src = MockConfigEntry(domain="demo")
    src.add_to_hass(hass)
    lamp, lamp_ent = _make_device(hass, src, "Kitchen Lamp", "light", "lamp")
    plug, plug_ent = _make_device(hass, src, "Plug", "switch", "plug")
    blinds, blinds_ent = _make_device(hass, src, "Blinds", "cover", "blinds")
    loose = er.async_get(hass).async_get_or_create(
        "light", "demo", "loose", original_name="Garden light"
    )

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    return entry, dict(lamp=lamp, plug=plug, blinds=blinds, lamp_ent=lamp_ent,
                       plug_ent=plug_ent, blinds_ent=blinds_ent, loose=loose, src=src)


async def _add_param(hass, entry, base, extra=None):
    flow = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE), context={"source": SOURCE_USER}
    )
    assert flow["type"] is FlowResultType.FORM and flow["step_id"] == "user"
    res = await hass.config_entries.subentries.async_configure(flow["flow_id"], base)
    if extra is not None:
        assert res["type"] is FlowResultType.FORM, res
        res = await hass.config_entries.subentries.async_configure(flow["flow_id"], extra)
    await hass.async_block_till_done()
    return res


def _our_entities(hass, entry):
    return er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)


async def test_full_lifecycle(hass: HomeAssistant) -> None:
    entry, d = await _setup(hass)

    # --- number parameter on devices with light/switch
    res = await _add_param(
        hass, entry,
        {"name": "Príkon", "type": "number", "unit": "W", "target": "device",
         "domains": ["light", "switch"]},
        {"min": 0, "max": 5000, "step": 0.5, "mode": "box"},
    )
    assert res["type"] is FlowResultType.CREATE_ENTRY
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    sub = next(iter(entry.subentries.values()))
    assert sub.unique_id == "prikon"

    ents = _our_entities(hass, entry)
    assert {e.device_id for e in ents} == {d["lamp"].id, d["plug"].id}
    lamp_num = next(e for e in ents if e.device_id == d["lamp"].id)
    assert lamp_num.entity_id == "number.kitchen_lamp_prikon"
    assert lamp_num.entity_category is EntityCategory.CONFIG
    assert lamp_num.config_subentry_id == sub.subentry_id
    state = hass.states.get(lamp_num.entity_id)
    assert state.state == "unknown"
    assert state.attributes["unit_of_measurement"] == "W"
    assert state.attributes["step"] == 0.5
    # we must not take ownership of the device
    assert dr.async_get(hass).async_get(d["lamp"].id).config_entry_id == d["src"].entry_id

    # --- set value and survive reload
    await hass.services.async_call("number", "set_value",
        {"entity_id": lamp_num.entity_id, "value": 60}, blocking=True)
    assert hass.states.get(lamp_num.entity_id).state == "60.0"
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(lamp_num.entity_id).state == "60.0"

    # --- duplicate key is rejected
    flow = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE), context={"source": SOURCE_USER})
    res = await hass.config_entries.subentries.async_configure(flow["flow_id"],
        {"name": "Prikon", "type": "text", "target": "device", "domains": ["light"]})
    assert res["errors"] == {"key": "key_exists"}
    hass.config_entries.subentries.async_abort(flow["flow_id"])

    # --- select parameter per entity on covers
    res = await _add_param(
        hass, entry,
        {"name": "Strana", "key": "side", "type": "select", "target": "entity",
         "domains": ["cover"]},
        {"options": ["Juh", "Sever", "Juh"]},
    )
    assert res["type"] is FlowResultType.CREATE_ENTRY
    st = hass.states.get("select.blinds_strana")
    assert st is not None, [e.entity_id for e in _our_entities(hass, entry)]
    assert st.attributes["options"] == ["Juh", "Sever"]
    assert st.attributes["target_entity_id"] == d["blinds_ent"].entity_id
    await hass.services.async_call("select", "select_option",
        {"entity_id": "select.blinds_strana", "option": "Sever"}, blocking=True)
    assert hass.states.get("select.blinds_strana").state == "Sever"

    # --- text / date / boolean on entity incl. entity without device
    res = await _add_param(hass, entry,
        {"name": "Poznámka", "type": "text", "unit": "km", "target": "entity", "domains": ["light"]},
        {"max_length": 100})
    assert res["type"] is FlowResultType.CREATE_ENTRY
    st = hass.states.get("text.garden_light_poznamka")
    assert st is not None, [e.entity_id for e in _our_entities(hass, entry)]
    assert st.attributes["unit"] == "km"
    await hass.services.async_call("text", "set_value",
        {"entity_id": "text.garden_light_poznamka", "value": "ahoj"}, blocking=True)
    assert hass.states.get("text.garden_light_poznamka").state == "ahoj"

    res = await _add_param(hass, entry,
        {"name": "Výmena batérie", "type": "date", "target": "device", "domains": ["cover"]})
    assert res["type"] is FlowResultType.CREATE_ENTRY
    await hass.services.async_call("date", "set_value",
        {"entity_id": "date.blinds_vymena_baterie", "date": "2026-03-01"}, blocking=True)
    assert hass.states.get("date.blinds_vymena_baterie").state == "2026-03-01"

    res = await _add_param(hass, entry,
        {"name": "Inštalované", "type": "datetime", "target": "device", "domains": ["switch"]})
    await hass.services.async_call("datetime", "set_value",
        {"entity_id": "datetime.plug_instalovane", "datetime": "2026-03-01 10:00:00"}, blocking=True)
    assert hass.states.get("datetime.plug_instalovane").state.startswith("2026-03-01")

    res = await _add_param(hass, entry,
        {"name": "Záruka", "type": "boolean", "target": "device", "domains": ["switch"]})
    await hass.services.async_call("switch", "turn_on",
        {"entity_id": "switch.plug_zaruka"}, blocking=True)
    assert hass.states.get("switch.plug_zaruka").state == "on"

    # --- reconfigure: number param only for lights now
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    flow = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": sub.subentry_id})
    assert flow["step_id"] == "reconfigure"
    res = await hass.config_entries.subentries.async_configure(flow["flow_id"],
        {"name": "Príkon", "type": "number", "unit": "kW", "target": "device", "domains": ["light"]})
    assert res["step_id"] == "number"
    res = await hass.config_entries.subentries.async_configure(flow["flow_id"],
        {"min": 0, "max": 10, "step": 0.1, "mode": "slider"})
    assert res["type"] is FlowResultType.ABORT and res["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert hass.states.get("number.plug_prikon") is None
    assert er.async_get(hass).async_get("number.plug_prikon") is None
    st = hass.states.get("number.kitchen_lamp_prikon")
    assert st.attributes["unit_of_measurement"] == "kW"
    assert st.state == "60.0"  # value kept (out of range now but kept)

    # --- new device appears -> gets parameter automatically
    new_dev, _ = _make_device(hass, d["src"], "Hall Lamp", "light", "hall")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert hass.states.get("number.hall_lamp_prikon") is not None

    # --- delete parameter
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert hass.config_entries.async_remove_subentry(entry, sub.subentry_id)
    await hass.async_block_till_done()
    assert hass.states.get("number.kitchen_lamp_prikon") is None
    assert er.async_get(hass).async_get("number.kitchen_lamp_prikon") is None
    # others still there
    assert hass.states.get("select.blinds_strana").state == "Sever"


async def test_readme_template(hass: HomeAssistant) -> None:
    from homeassistant.helpers.template import Template
    entry, d = await _setup(hass)
    await _add_param(hass, entry,
        {"name": "Príkon", "type": "number", "unit": "W", "target": "device", "domains": ["light"]},
        {"min": 0, "max": 5000, "step": 1, "mode": "box"})
    await hass.services.async_call("number", "set_value",
        {"entity_id": "number.kitchen_lamp_prikon", "value": 60}, blocking=True)
    hass.states.async_set("light.kitchen_lamp", "on")
    hass.states.async_set(d["loose"].entity_id, "on")
    tpl = Template(
        "{{ states.light | selectattr('state','eq','on')"
        " | map(attribute='entity_id') | map('device_id')"
        " | map('device_entities') | sum(start=[])"
        " | select('match','number\\..*_prikon$')"
        " | map('states') | map('float', 0) | sum }}", hass)
    assert float(tpl.async_render()) == 60.0
