import warnings
from os import environ as env

from . import json, memory, stub, yaml
from .baseclasses import ConfigInterface
from .constants import SOURCE

__version__ = "1.0.0"


class Config(ConfigInterface):
    def __new__(cls, *args, **kwargs):
        match SOURCE.get(env.get("APP_CONFIG_SOURCE")):
            case SOURCE.json:
                return json.Config(*args, **kwargs)
            case SOURCE.yaml:
                return yaml.Config(*args, **kwargs)
            case SOURCE.stub:
                return stub.Config(*args, **kwargs)
            case SOURCE.memory:
                return memory.Config(*args, **kwargs)
            case _:
                raw = env.get("APP_CONFIG_SOURCE")
                if raw is not None:
                    warnings.warn(
                        f"Unknown APP_CONFIG_SOURCE={raw!r}, falling back to json.Config. Valid values: {[s.value for s in SOURCE]}",
                        UserWarning,
                        stacklevel=2,
                    )
                return json.Config(*args, **kwargs)
