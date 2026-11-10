from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.custom_params.const import DOMAIN


async def test_http_flows(hass: HomeAssistant, hass_client) -> None:
    assert await async_setup_component(hass, "config", {})
    client = await hass_client()
    r = await client.post("/api/config/config_entries/flow",
                          json={"handler": DOMAIN, "show_advanced_options": False})
    body = await r.json()
    assert r.status == 200, body
    r = await client.post(f"/api/config/config_entries/flow/{body['flow_id']}", json={})
    body = await r.json()
    assert body["type"] == "create_entry", body
    entry_id = body["result"]["entry_id"]
    await hass.async_block_till_done()
    r = await client.post("/api/config/config_entries/subentries/flow",
                          json={"handler": [entry_id, "parameter"], "show_advanced_options": False})
    body = await r.json()
    assert r.status == 200, body
    assert body["step_id"] == "user"
