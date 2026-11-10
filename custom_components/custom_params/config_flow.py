"""Config flow: one entry, each parameter definition is a subentry."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_DOMAINS,
    CONF_ICON,
    CONF_KEY,
    CONF_MAX,
    CONF_MAX_LENGTH,
    CONF_MIN,
    CONF_MODE,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_STEP,
    CONF_TARGET,
    CONF_TYPE,
    CONF_UNIT,
    DEFAULT_MAX,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MIN,
    DEFAULT_STEP,
    DOMAIN,
    DOMAIN_CHOICES,
    NUMBER_MODES,
    PARAM_TYPES,
    SUBENTRY_TYPE,
    TARGET_DEVICE,
    TARGET_ENTITY,
    TYPE_NUMBER,
    TYPE_SELECT,
    TYPE_TEXT,
)

# Keys that belong only to a specific type; removed when the type does not match.
_TYPE_SPECIFIC_KEYS = {
    TYPE_NUMBER: {CONF_MIN, CONF_MAX, CONF_STEP, CONF_MODE},
    TYPE_SELECT: {CONF_OPTIONS},
    TYPE_TEXT: {CONF_MAX_LENGTH},
}


def _base_schema(include_key: bool) -> vol.Schema:
    fields: dict[Any, Any] = {vol.Required(CONF_NAME): selector.TextSelector()}
    if include_key:
        fields[vol.Optional(CONF_KEY)] = selector.TextSelector()
    fields.update(
        {
            vol.Required(CONF_TYPE, default=TYPE_NUMBER): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PARAM_TYPES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="param_type",
                )
            ),
            vol.Optional(CONF_UNIT): selector.TextSelector(),
            vol.Required(CONF_TARGET, default=TARGET_DEVICE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[TARGET_DEVICE, TARGET_ENTITY],
                    mode=selector.SelectSelectorMode.LIST,
                    translation_key="target",
                )
            ),
            vol.Required(CONF_DOMAINS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DOMAIN_CHOICES,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="domains",
                )
            ),
            vol.Optional(CONF_ICON): selector.IconSelector(),
        }
    )
    return vol.Schema(fields)


NUMBER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MIN, default=DEFAULT_MIN): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
        ),
        vol.Required(CONF_MAX, default=DEFAULT_MAX): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
        ),
        vol.Required(CONF_STEP, default=DEFAULT_STEP): selector.NumberSelector(
            selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
        ),
        vol.Required(CONF_MODE, default="box"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=NUMBER_MODES,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="number_mode",
            )
        ),
    }
)

SELECT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPTIONS): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[], multiple=True, custom_value=True
            )
        ),
    }
)

TEXT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAX_LENGTH, default=DEFAULT_MAX_LENGTH): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=255, step=1, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }
)


class CustomParamsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the (single) Custom Parameters entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Custom Parameters", data={})
        return self.async_show_form(step_id="user")

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_TYPE: ParameterSubentryFlow}


class ParameterSubentryFlow(ConfigSubentryFlow):
    """Add or edit a parameter definition."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @property
    def _is_reconfigure(self) -> bool:
        return self.source == SOURCE_RECONFIGURE

    def _existing(self) -> dict[str, Any]:
        return dict(self._get_reconfigure_subentry().data) if self._is_reconfigure else {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            key = slugify(user_input.get(CONF_KEY) or user_input[CONF_NAME])
            used = {sub.unique_id for sub in self._get_entry().subentries.values()}
            if not key:
                errors[CONF_KEY] = "invalid_key"
            elif key in used:
                errors[CONF_KEY] = "key_exists"
            elif not user_input.get(CONF_DOMAINS):
                errors[CONF_DOMAINS] = "no_domains"
            else:
                self._data = {**user_input, CONF_KEY: key}
                return await self._async_step_type_specific()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                _base_schema(include_key=True), user_input or {}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        existing = self._existing()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_DOMAINS):
                errors[CONF_DOMAINS] = "no_domains"
            else:
                # Keep type-specific settings as defaults for the next step.
                self._data = {
                    **{k: v for k, v in existing.items() if k not in (CONF_UNIT, CONF_ICON)},
                    **user_input,
                    CONF_KEY: existing[CONF_KEY],
                }
                return await self._async_step_type_specific()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _base_schema(include_key=False), user_input or existing
            ),
            errors=errors,
            description_placeholders={"key": existing.get(CONF_KEY, "")},
        )

    async def _async_step_type_specific(self) -> SubentryFlowResult:
        param_type = self._data[CONF_TYPE]
        if param_type == TYPE_NUMBER:
            return await self.async_step_number()
        if param_type == TYPE_SELECT:
            return await self.async_step_select()
        if param_type == TYPE_TEXT:
            return await self.async_step_text()
        return self._async_finish()

    async def async_step_number(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_MIN] >= user_input[CONF_MAX]:
                errors["base"] = "min_max"
            elif user_input[CONF_STEP] <= 0:
                errors[CONF_STEP] = "step"
            else:
                self._data.update(user_input)
                return self._async_finish()
        return self.async_show_form(
            step_id="number",
            data_schema=self.add_suggested_values_to_schema(
                NUMBER_SCHEMA, user_input or self._data
            ),
            errors=errors,
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            options = [str(o).strip() for o in user_input.get(CONF_OPTIONS, [])]
            options = [o for o in dict.fromkeys(options) if o]
            if not options:
                errors[CONF_OPTIONS] = "no_options"
            else:
                self._data[CONF_OPTIONS] = options
                return self._async_finish()
        return self.async_show_form(
            step_id="select",
            data_schema=self.add_suggested_values_to_schema(
                SELECT_SCHEMA, user_input or self._data
            ),
            errors=errors,
        )

    async def async_step_text(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        if user_input is not None:
            self._data[CONF_MAX_LENGTH] = int(user_input[CONF_MAX_LENGTH])
            return self._async_finish()
        return self.async_show_form(
            step_id="text",
            data_schema=self.add_suggested_values_to_schema(TEXT_SCHEMA, self._data),
        )

    @callback
    def _async_finish(self) -> SubentryFlowResult:
        param_type = self._data[CONF_TYPE]
        data = {
            k: v
            for k, v in self._data.items()
            if not any(
                k in keys
                for t, keys in _TYPE_SPECIFIC_KEYS.items()
                if t != param_type
            )
            and v not in (None, "")
        }
        title = data[CONF_NAME]
        if self._is_reconfigure:
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                title=title,
                data=data,
            )
        return self.async_create_entry(title=title, data=data, unique_id=data[CONF_KEY])
