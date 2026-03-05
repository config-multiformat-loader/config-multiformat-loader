from __future__ import annotations

import typing as t

import warnings
from abc import abstractmethod

from .constants import RESERVED_CLASS_NAMES

T = t.TypeVar("T")


class ConfigInterface:
    """
    Abstract interface for all config backends.

    Instances expose config values as **dynamic attributes** — there is no
    fixed schema. Any key present in the config source becomes an attribute
    on the object at load time::

        cfg = Config()          # loads source automatically
        cfg.database_host       # attribute from config
        cfg.get("timeout", 30)  # safe access with default
        cfg.to_dict()           # {key: value, ...} — only config data,
                                # no methods or internal attributes

    Backends:
        - ``json.Config``   — JSON5 file (env: APP_CONFIG_FILE)
        - ``yaml.Config``   — YAML file  (env: APP_CONFIG_FILE)
        - ``stub.Config``   — silent no-op, every key returns ``None``
        - ``memory.Config`` — in-memory dict, intended for tests

    The concrete backend is selected automatically by the factory
    ``config.Config`` based on the ``APP_CONFIG_SOURCE`` env variable.
    """

    @abstractmethod
    def reload(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def extract(self: T, section: str, uppercase: bool | None = None) -> T:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str, default: t.Any = None) -> t.Any:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self, prefix: str | None = None) -> dict:
        raise NotImplementedError


class BaseConfig(ConfigInterface):
    uppercase: bool
    container: str
    section: str | None
    configfile: str

    _properties: tuple[str, ...]

    def __new__(cls, *_args, section=None, uppercase=None, **_kwargs):
        uppercase = uppercase if isinstance(uppercase, bool) else False
        configfile = cls.container

        obj = super().__new__(cls)
        obj._set_instance_props(section=section, uppercase=uppercase, configfile=configfile)
        obj.reload()
        return obj

    def _set_instance_props(self, *, section, uppercase, configfile):
        """Write constructor parameters onto the instance (not the class)."""
        object.__setattr__(self, "uppercase", uppercase)  # noqa: PLC2801
        object.__setattr__(self, "section", section)  # noqa: PLC2801
        object.__setattr__(self, "configfile", configfile)  # noqa: PLC2801
        object.__setattr__(self, "_properties", ("uppercase", "section", "configfile"))  # noqa: PLC2801

    def extract(self, section: str, uppercase: bool | None = None):
        if not isinstance(section, str):
            return self

        uppercase = uppercase if isinstance(uppercase, bool) else self.uppercase
        return type(self).__new__(type(self), section=section, uppercase=uppercase)

    def get(self, key: str, default: t.Any = None) -> t.Any:
        return getattr(self, self.convert_case(key), default)

    def to_dict(self, prefix: str | None = None) -> dict:
        return {f: getattr(self, f) for f in vars(self) if not self._skipped(f, prefix)}  # noqa: WPS421

    def convert_case(self, key):
        return key.upper() if self.uppercase else key

    def _apply_dict(self, cfg: dict) -> None:
        if not isinstance(cfg, dict):
            return

        for key, value in cfg.items():
            attr_name = self.convert_case(key)
            if attr_name in RESERVED_CLASS_NAMES:
                warnings.warn(
                    f"Config key '{key}' conflicts with reserved attribute "
                    f"'{attr_name}' and will be skipped. "
                    f"Rename the key in your config file.",
                    UserWarning,
                    stacklevel=3,
                )
                continue
            if attr_name.startswith("_") or attr_name in self._properties:
                warnings.warn(
                    f"Config key '{key}' is not valid and will be skipped. Rename the key in your config file.",
                    UserWarning,
                    stacklevel=3,
                )
                continue
            setattr(self, attr_name, value)

    def _skipped(self, item, prefix=None):
        prefix = "" if prefix is None else self.convert_case(prefix)

        if item in self._properties or self.is_private(item):
            return True

        return bool(prefix) and not item.startswith(prefix)

    @staticmethod
    def is_private(name: str) -> bool:
        return name.startswith("_")

    def reload(self):
        raise NotImplementedError

    def __getitem__(self, key: str) -> t.Any:
        return getattr(self, key)
