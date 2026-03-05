from .baseclasses import BaseConfig
from .interfaces import EmptyType


class Config(BaseConfig, metaclass=EmptyType):
    def extract(self, section: str, *_args, **_kwargs):  # noqa: ARG002
        # Return a fresh stub instance — same silent behaviour, but a distinct
        # object so callers that expect a new instance are not surprised.
        return type(self).__new__(type(self))

    def get(self, key: str, default=None):  # noqa: PLR6301, ARG002
        return default

    def __getattr__(self, name: str):  # noqa: WPS324
        # Intentionally returns None for any attribute — stub is a silent no-op.
        # Note: hasattr() always returns True for any name because AttributeError
        # is never raised. Callers must not rely on hasattr() to detect key presence.
        return None  # noqa: WPS324

    def reload(self):  # noqa: WPS324,PLR6301
        return None  # noqa: WPS324
