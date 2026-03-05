from __future__ import annotations

import typing as t

from pathlib import Path

import yaml as _yaml

from .baseclasses import BaseConfig
from .interfaces import FileType
from .utils import tree_extract

__all__ = ["Config"]


class YAMLType(FileType):
    context: t.ClassVar[dict[str, t.Any]] = {}

    @property
    def extension(self):
        return "yml"


class Config(BaseConfig, metaclass=YAMLType):
    container = "APP_CONFIG_FILE"
    filename = "configuration"

    configfile: str
    section: str | None

    def reload(self):
        with Path(self.configfile).open("r", encoding="utf-8") as config:
            cfg = _yaml.safe_load(config)

        if self.section and (cfg := tree_extract(self.section, cfg)) is None:
            raise ValueError(f"Can't find section '{self.section}' in file")

        self._apply_dict(cfg)
