import typing as t

from config.memory import Config as MemoryConfig

from ..constants import JSON_CONFIG_DATA


def empty(make: t.Callable[..., MemoryConfig]) -> MemoryConfig:
    return make(data={})


def uppercase(make: t.Callable[..., MemoryConfig]) -> MemoryConfig:
    return make(uppercase=True)


def nested(make: t.Callable[..., MemoryConfig]) -> MemoryConfig:
    return make(data=dict(JSON_CONFIG_DATA))
