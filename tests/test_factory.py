import warnings
from collections.abc import MutableMapping

from hamcrest import assert_that, instance_of, is_
from pytest import mark

from config import Config
from config.json import Config as JsonConfig
from config.memory import Config as MemoryConfig
from config.stub import Config as StubConfig
from config.yaml import Config as YamlConfig

from .constants import MEMORY_CONFIG_DATA


def test_factory_stub_source(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "stub"

    cfg = Config()

    assert_that(cfg, instance_of(StubConfig))


def test_factory_memory_source(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "memory"

    cfg = Config(data=MEMORY_CONFIG_DATA)

    assert_that(cfg, instance_of(MemoryConfig))


@mark.usefixtures("json_ctx")
def test_factory_json_source(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "json"

    cfg = Config()

    assert_that(cfg, instance_of(JsonConfig))
    assert_that(cfg.host, is_("localhost"))


@mark.usefixtures("yaml_ctx")
def test_factory_yaml_source(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "yaml"

    cfg = Config()

    assert_that(cfg, instance_of(YamlConfig))
    assert_that(cfg.service, is_("test-service"))


@mark.usefixtures("json_ctx")
def test_factory_default_is_json(env: MutableMapping[str, str]) -> None:
    env.pop("APP_CONFIG_SOURCE", None)

    cfg = Config()

    assert_that(cfg, instance_of(JsonConfig))
    assert_that(cfg.host, is_("localhost"))


@mark.usefixtures("json_ctx")
def test_factory_unknown_source_warns_and_falls_back(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "typo"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cfg = Config()

    assert_that(cfg, instance_of(JsonConfig))
    assert_that(len(caught), is_(1))
    assert_that(issubclass(caught[0].category, UserWarning), is_(True))
    assert_that("Unknown APP_CONFIG_SOURCE" in str(caught[0].message), is_(True))


@mark.usefixtures("json_ctx")
def test_factory_no_warning_when_source_unset(env: MutableMapping[str, str]) -> None:
    env.pop("APP_CONFIG_SOURCE", None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Config()

    user_warnings = [w for w in caught if "APP_CONFIG_SOURCE" in str(w.message)]
    assert_that(len(user_warnings), is_(0))


def test_factory_memory_with_data(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "memory"

    cfg = Config(data=dict(MEMORY_CONFIG_DATA))

    assert_that(cfg, instance_of(MemoryConfig))
    assert_that(cfg.host, is_("127.0.0.1"))


def test_factory_memory_accepts_extra_kwargs(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "memory"
    data = {"api": {"host": "localhost", "port": 8080}}

    cfg = Config(data=data, section="ignored", uppercase=False)

    assert_that(cfg, instance_of(MemoryConfig))


@mark.usefixtures("json_ctx")
def test_factory_passes_section_to_json(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "json"

    cfg = Config(section="database")

    assert_that(cfg.name, is_("testdb"))


@mark.usefixtures("yaml_ctx")
def test_factory_passes_section_to_yaml(env: MutableMapping[str, str]) -> None:
    env["APP_CONFIG_SOURCE"] = "yaml"

    cfg = Config(section="logging")

    assert_that(cfg.level, is_("DEBUG"))
