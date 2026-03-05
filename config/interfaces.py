from __future__ import annotations

import typing as t

from abc import abstractmethod
from os import environ as env
from pathlib import Path

from .constants import DEFAULT_ATTRIBUTE_CONTAINER, DEFAULT_ATTRIBUTE_FILENAME, DEFAULT_CONFIG_FILENAME


class FileType(type):
    context: t.ClassVar[dict[str, t.Any]]

    def __new__(cls, name: str, bases: tuple[t.Any, ...], attrs: dict[str, t.Any]):
        cls.context = {
            "path": env.get(attrs.pop(DEFAULT_ATTRIBUTE_CONTAINER, ""), ""),
            "filename": attrs.pop(DEFAULT_ATTRIBUTE_FILENAME, DEFAULT_CONFIG_FILENAME),
        }
        return super().__new__(cls, name, bases, attrs)

    @property
    @abstractmethod
    def extension(cls):
        raise NotImplementedError

    @property
    def container(cls):
        # NOTE: this property performs filesystem I/O on every access.
        # It is called once during class body evaluation (inside __new__),
        # so the result is cached as configfile on the instance.
        for rule in cls.scan_rules:
            if not (configpath := Path(rule.format(cls.context.get("path", "")))).is_file():
                continue
            if configpath.suffix.lstrip(".") != cls.extension:
                continue
            return configpath.absolute()
        raise FileNotFoundError("Can't find container file")

    @property
    def scan_rules(cls) -> tuple[str, ...]:
        # {{}} is a literal brace in the f-string, producing {} in the output.
        # The resulting strings contain a single '{}' placeholder that is later
        # filled by rule.format(path) in the container property above.
        return (  # noqa: WPS227
            "{}",
            f"{{}}.{cls.extension}",
            f"{cls.context.get('filename', DEFAULT_CONFIG_FILENAME)}.{cls.extension}",
            "../data/{{}}",
            f"../data/{{}}.{cls.extension}",
            f"../data/{cls.context.get('filename', DEFAULT_CONFIG_FILENAME)}.{cls.extension}",
        )


class EmptyType(type):
    @property
    def container(cls) -> None:  # noqa: WPS324
        return None  # noqa: WPS324
