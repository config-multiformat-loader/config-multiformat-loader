from __future__ import annotations

import typing as t

import warnings
from copy import deepcopy

from .baseclasses import ConfigInterface
from .interfaces import EmptyType
from .utils import tree_extract


class Config(ConfigInterface, metaclass=EmptyType):
    raw: dict[str, t.Any]

    def __init__(self, data: dict | None = None, *, uppercase: bool = False, **_kwargs) -> None:
        self.uppercase = uppercase
        raw: dict = deepcopy(data) if isinstance(data, dict) else {}
        self.raw = {k.upper(): v for k, v in raw.items()} if uppercase else raw

    def extract(self, section: str, uppercase: bool | None = None) -> Config:
        if (cfg := tree_extract(section, self.raw)) is None:
            raise ValueError(f"Can't find section '{section}' in file")

        eff_uppercase = uppercase if isinstance(uppercase, bool) else self.uppercase
        return type(self)(cfg, uppercase=eff_uppercase)

    def get(self, key: str, default=None):
        return self.raw.get(self.convert_case(key), default)

    def __getattr__(self, name: str):
        try:
            return self.raw[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, key: str) -> t.Any:
        return getattr(self, key)

    def convert_case(self, key: str) -> str:
        return key.upper() if self.uppercase else key

    def reload(self) -> None:  # noqa: PLR6301
        warnings.warn(
            "memory.Config.reload() has no effect — the in-memory store "
            "is not backed by an external source. "
            "Create a new Config(data) instance to update data.",
            UserWarning,
            stacklevel=2,
        )

    def all(self, prefix: str | None = None) -> dict:
        return self.to_dict(prefix)

    def to_dict(self, prefix: str | None = None) -> dict:
        if prefix is None:
            return dict(self.raw)
        pfx = self.convert_case(prefix)
        return {k: v for k, v in self.raw.items() if k.startswith(pfx)}
