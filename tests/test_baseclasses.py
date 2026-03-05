import typing as t

import warnings

from hamcrest import (
    assert_that,
    calling,
    has_key,
    instance_of,
    is_,
    is_not,
    none,
    raises,
)
from pytest import mark

from config.baseclasses import BaseConfig
from config.constants import RESERVED_CLASS_NAMES
from config.json import Config as JsonConfig

from .constants import GET_DEFAULT, NON_STRING_KEY, PORT
from .utils import ConcreteConfig


def test_new_sets_instance_props(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg()

    assert_that(cfg.uppercase, is_(False))
    assert_that(cfg.section, is_(none()))
    assert_that(cfg.configfile, is_(none()))


def test_new_sets_uppercase(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(uppercase=True)

    assert_that(cfg.uppercase, is_(True))


def test_new_sets_section(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(section="api")

    assert_that(cfg.section, is_("api"))


def test_apply_dict_sets_attributes(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(data={"host": "localhost", "port": PORT})

    assert_that(cfg.host, is_("localhost"))
    assert_that(cfg.port, is_(PORT))


def test_apply_dict_uppercase(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(uppercase=True)
    cfg._apply_dict({"host": "localhost", "port": PORT})  # noqa: SLF001

    assert_that(cfg.HOST, is_("localhost"))
    assert_that(cfg.PORT, is_(PORT))


def test_apply_dict_skips_non_dict(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg()
    cfg._apply_dict("not a dict")  # type: ignore[arg-type]  # noqa: SLF001

    assert_that(cfg.to_dict(), is_({}))


def test_apply_dict_skips_none(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg()
    cfg._apply_dict(None)  # type: ignore[arg-type]  # noqa: SLF001

    assert_that(cfg.to_dict(), is_({}))


def test_apply_dict_warns_on_reserved_name(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cfg._apply_dict({"reload": "value", "host": "ok"})  # noqa: SLF001

    assert_that(cfg.host, is_("ok"))
    assert_that(len(caught), is_(1))
    assert_that("reserved" in str(caught[0].message).lower(), is_(True))


@mark.parametrize(
    "reserved_name",
    sorted(RESERVED_CLASS_NAMES),
    ids=sorted(RESERVED_CLASS_NAMES),
)
def test_apply_dict_skips_all_reserved_names(concrete_cfg: t.Callable[..., ConcreteConfig], reserved_name: str) -> None:
    cfg = concrete_cfg()

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        cfg._apply_dict({reserved_name: "should_be_skipped", "safe_key": "ok"})  # noqa: SLF001

    assert_that(cfg.safe_key, is_("ok"))
    assert_that(cfg.to_dict(), is_not(has_key(reserved_name)))


def test_get_existing_key(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})

    assert_that(cfg.get("host"), is_("localhost"))


def test_get_missing_key_returns_default(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg()

    assert_that(cfg.get("missing"), is_(none()))
    assert_that(cfg.get("missing", GET_DEFAULT), is_(GET_DEFAULT))


def test_get_respects_uppercase(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(data={"host": "localhost"}, uppercase=True)

    assert_that(cfg.get("host"), is_("localhost"))


def test_to_dict_returns_data_only(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"host": "localhost", "port": 8080})
    result = cfg.to_dict()

    assert_that(result, is_({"host": "localhost", "port": 8080}))
    assert_that("uppercase" not in result, is_(True))
    assert_that("section" not in result, is_(True))
    assert_that("configfile" not in result, is_(True))


def test_to_dict_with_prefix(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(data={"db_host": "localhost", "db_port": 5432, "cache_ttl": 60})
    result = cfg.to_dict("db_")

    assert_that(result, is_({"db_host": "localhost", "db_port": 5432}))


def test_to_dict_with_prefix_uppercase(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"db_host": "localhost", "db_port": 5432}, uppercase=True)
    result = cfg.to_dict("db_")

    assert_that(result, is_({"DB_HOST": "localhost", "DB_PORT": 5432}))


def test_to_dict_prefix_no_match(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})
    result = cfg.to_dict("zz_")

    assert_that(result, is_({}))


def test_convert_case_lowercase(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg()

    assert_that(cfg.convert_case("host"), is_("host"))


def test_convert_case_uppercase(concrete_cfg: t.Callable[..., ConcreteConfig]) -> None:
    cfg = concrete_cfg(uppercase=True)

    assert_that(cfg.convert_case("host"), is_("HOST"))


@mark.parametrize(
    ("name", "expected"),
    [
        ("_private", True),
        ("__dunder", True),
        ("__dunder__", True),
        ("public", False),
        ("", False),
    ],
    ids=["single_underscore", "double_underscore", "dunder", "public", "empty_string"],
)
def test_is_private(name: str, expected: bool) -> None:
    assert_that(BaseConfig.is_private(name), is_(expected))


def test_getitem_returns_attribute(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})

    assert_that(cfg["host"], is_("localhost"))


def test_getitem_raises_on_missing(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg()

    assert_that(
        calling(cfg.__getitem__).with_args("missing"),
        raises(AttributeError),
    )


@mark.usefixtures("json_ctx")
def test_extract_creates_new_instance() -> None:
    cfg = JsonConfig()
    extracted = cfg.extract("database")

    assert_that(extracted, instance_of(JsonConfig))
    assert_that(extracted.name, is_("testdb"))


def test_extract_returns_self_on_non_string(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})
    result = cfg.extract(NON_STRING_KEY)  # type: ignore[arg-type]

    assert_that(result is cfg, is_(True))


@mark.usefixtures("json_ctx")
def test_extract_preserves_uppercase() -> None:
    cfg = JsonConfig(uppercase=True)
    extracted = cfg.extract("database")

    assert_that(extracted.uppercase, is_(True))


@mark.usefixtures("json_ctx")
def test_extract_overrides_uppercase() -> None:
    cfg = JsonConfig(uppercase=False)
    extracted = cfg.extract("database", uppercase=True)

    assert_that(extracted.uppercase, is_(True))


def test_skipped_filters_properties(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})
    result = cfg.to_dict()

    assert_that("_properties" not in result, is_(True))
    assert_that("uppercase" not in result, is_(True))
    assert_that("section" not in result, is_(True))
    assert_that("configfile" not in result, is_(True))


def test_skipped_filters_private_attrs(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg(data={"host": "localhost"})
    cfg._custom_private = "hidden"  # noqa: SLF001
    result = cfg.to_dict()

    assert_that("_custom_private" not in result, is_(True))


def test_base_config_reload_raises(
    concrete_cfg: t.Callable[..., ConcreteConfig],
) -> None:
    cfg = concrete_cfg()

    assert_that(
        calling(BaseConfig.reload).with_args(cfg),
        raises(NotImplementedError),
    )
