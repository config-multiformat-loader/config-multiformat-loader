from config.baseclasses import BaseConfig
from config.interfaces import EmptyType


class ConcreteConfig(BaseConfig, metaclass=EmptyType):
    def reload(self) -> None:  # noqa: PLR6301, WPS324
        return None  # noqa: WPS324
