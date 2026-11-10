"""Constants for the Custom Parameters integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "custom_params"
SUBENTRY_TYPE = "parameter"
STORAGE_KEY = f"{DOMAIN}.values"
STORAGE_VERSION = 1

CONF_NAME = "name"
CONF_KEY = "key"
CONF_TYPE = "type"
CONF_UNIT = "unit"
CONF_ICON = "icon"
CONF_TARGET = "target"
CONF_DOMAINS = "domains"
CONF_MIN = "min"
CONF_MAX = "max"
CONF_STEP = "step"
CONF_MODE = "mode"
CONF_OPTIONS = "options"
CONF_MAX_LENGTH = "max_length"

TYPE_NUMBER = "number"
TYPE_TEXT = "text"
TYPE_DATE = "date"
TYPE_DATETIME = "datetime"
TYPE_BOOLEAN = "boolean"
TYPE_SELECT = "select"

PARAM_TYPES = [
    TYPE_NUMBER,
    TYPE_TEXT,
    TYPE_DATE,
    TYPE_DATETIME,
    TYPE_BOOLEAN,
    TYPE_SELECT,
]

TYPE_TO_PLATFORM: dict[str, Platform] = {
    TYPE_NUMBER: Platform.NUMBER,
    TYPE_TEXT: Platform.TEXT,
    TYPE_DATE: Platform.DATE,
    TYPE_DATETIME: Platform.DATETIME,
    TYPE_BOOLEAN: Platform.SWITCH,
    TYPE_SELECT: Platform.SELECT,
}

PLATFORMS: list[Platform] = list(dict.fromkeys(TYPE_TO_PLATFORM.values()))

TARGET_DEVICE = "device"
TARGET_ENTITY = "entity"

# Domains offered in the UI. Any other domain can be typed in manually.
DOMAIN_CHOICES = [
    "light",
    "switch",
    "cover",
    "climate",
    "fan",
    "sensor",
    "binary_sensor",
    "lock",
    "media_player",
    "vacuum",
    "camera",
    "valve",
    "water_heater",
    "humidifier",
    "alarm_control_panel",
    "button",
    "number",
    "select",
    "siren",
    "lawn_mower",
    "update",
    "event",
    "device_tracker",
]

NUMBER_MODES = ["box", "slider"]

DEFAULT_MIN = 0.0
DEFAULT_MAX = 1000000.0
DEFAULT_STEP = 1.0
DEFAULT_MAX_LENGTH = 255
