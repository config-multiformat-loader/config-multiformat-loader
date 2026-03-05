from __future__ import annotations

from enum import Enum

DEFAULT_CONFIG_FILENAME = "configuration"

DEFAULT_ATTRIBUTE_CONTAINER = "container"
DEFAULT_ATTRIBUTE_FILENAME = "filename"

# Private names (starting with '_') are protected via BaseConfig.is_private() and
# are excluded from config data regardless. Only public names that would conflict
# with config keys need to be listed here.
RESERVED_CLASS_NAMES: frozenset[str] = frozenset((
    "all",
    "convert_case",
    "extract",
    "get",
    "is_private",
    "reload",
    "to_dict",
))


class SOURCE(Enum):
    json = "json"
    yaml = "yaml"
    memory = "memory"
    stub = "stub"

    @staticmethod
    def get(name: str | None) -> SOURCE | None:
        try:
            return SOURCE(name)
        except ValueError:
            return None
