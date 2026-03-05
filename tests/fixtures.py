import typing as t

from collections.abc import MutableMapping
from os import environ
from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from config.json import JSONType
from config.memory import Config as MemoryConfig
from config.yaml import YAMLType

from .constants import MEMORY_CONFIG_DATA
from .utils import ConcreteConfig

DATA_DIR = Path(__file__).parent / "data"


@fixture(name="env")
def env() -> t.Generator[MutableMapping[str, str], None, None]:
    original = environ.copy()
    yield environ
    environ.clear()
    environ.update(original)


@fixture(name="concrete_cfg")
def concrete_cfg() -> t.Callable[..., ConcreteConfig]:
    def factory(data: dict | None = None, section: str | None = None, uppercase: bool = False) -> ConcreteConfig:
        with patch.object(ConcreteConfig, "reload", return_value=None):
            cfg = ConcreteConfig.__new__(ConcreteConfig, section=section, uppercase=uppercase)
        if data:
            cfg._apply_dict(data)  # noqa: SLF001
        return cfg

    return factory


@fixture(name="memory_cfg")
def memory_cfg() -> t.Callable[..., MemoryConfig]:
    def factory(data: t.Any = MEMORY_CONFIG_DATA, **kwargs: t.Any) -> MemoryConfig:
        return MemoryConfig(data=dict(data), **kwargs)

    return factory


@fixture(name="json_ctx")
def json_ctx() -> t.Generator[None, None, None]:
    old_path = JSONType.context.get("path", "")
    JSONType.context["path"] = str(DATA_DIR / "configuration.json")
    yield
    JSONType.context["path"] = old_path


@fixture(name="yaml_ctx")
def yaml_ctx() -> t.Generator[None, None, None]:
    old_path = YAMLType.context.get("path", "")
    YAMLType.context["path"] = str(DATA_DIR / "configuration.yml")
    yield
    YAMLType.context["path"] = old_path
