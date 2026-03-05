import typing as t

import warnings

from hamcrest import (
    assert_that,
    calling,
    instance_of,
    is_,
    none,
    raises,
)

from config.memory import Config as MemoryConfig

from .constants import DB_PORT, MEMORY_CONFIG_DATA, TIMEOUT
from .reducers import memory as r


def test_init_with_data(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg.host, is_("127.0.0.1"))
    assert_that(cfg.port, is_(DB_PORT))
    assert_that(cfg.name, is_("memdb"))
    assert_that(cfg.timeout, is_(TIMEOUT))


def test_init_empty(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = r.empty(memory_cfg)
    assert_that(cfg.raw, is_({}))


def test_init_none_data() -> None:
    cfg = MemoryConfig(data=None)

    assert_that(cfg.raw, is_({}))


def test_init_non_dict_data() -> None:
    cfg = MemoryConfig(data="not a dict")  # type: ignore[arg-type]

    assert_that(cfg.raw, is_({}))


def test_init_deepcopy() -> None:
    original: dict = {"key": "value", "nested": {"a": 1}}
    cfg = MemoryConfig(data=original)

    original["key"] = "changed"
    original["nested"]["a"] = 999

    assert_that(cfg.raw["key"], is_("value"))
    assert_that(cfg.raw["nested"]["a"], is_(1))


def test_init_uppercase() -> None:
    cfg = MemoryConfig(data={"host": "localhost", "port": 5432}, uppercase=True)

    assert_that(cfg.raw, is_({"HOST": "localhost", "PORT": 5432}))
    assert_that(cfg.uppercase, is_(True))


def test_init_accepts_extra_kwargs() -> None:
    cfg = MemoryConfig(data=dict(MEMORY_CONFIG_DATA), section="api", uppercase=False, extra="ignored")

    assert_that(cfg.host, is_("127.0.0.1"))


def test_getattr_existing_key(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg.host, is_("127.0.0.1"))


def test_getattr_missing_key_raises(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(
        calling(getattr).with_args(cfg, "nonexistent"),
        raises(AttributeError),
    )


def test_getitem(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg["host"], is_("127.0.0.1"))


def test_getitem_missing_raises(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(
        calling(cfg.__getitem__).with_args("missing"),
        raises(AttributeError),
    )


def test_get_existing(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg.get("host"), is_("127.0.0.1"))


def test_get_missing_returns_default(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg.get("missing"), is_(none()))
    assert_that(cfg.get("missing", "fallback"), is_("fallback"))


def test_to_dict_returns_copy(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    result = cfg.to_dict()

    assert_that(result, is_(MEMORY_CONFIG_DATA))
    assert_that(result is not cfg.raw, is_(True))


def test_to_dict_with_prefix() -> None:
    cfg = MemoryConfig(data={"db_host": "localhost", "db_port": 5432, "cache_ttl": 60})
    result = cfg.to_dict("db_")

    assert_that(result, is_({"db_host": "localhost", "db_port": 5432}))


def test_to_dict_with_prefix_uppercase() -> None:
    cfg = MemoryConfig(data={"db_host": "localhost", "db_port": 5432}, uppercase=True)
    result = cfg.to_dict("db_")

    assert_that(result, is_({"DB_HOST": "localhost", "DB_PORT": 5432}))


def test_to_dict_prefix_no_match(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    result = cfg.to_dict("zz_")

    assert_that(result, is_({}))


def test_all_delegates_to_to_dict(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = memory_cfg()
    assert_that(cfg.all(), is_(cfg.to_dict()))


def test_all_with_prefix() -> None:
    cfg = MemoryConfig(data={"db_host": "localhost", "db_port": 5432, "cache_ttl": 60})

    assert_that(cfg.all("db_"), is_({"db_host": "localhost", "db_port": 5432}))


def test_extract_section(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = r.nested(memory_cfg)
    extracted = cfg.extract("database")

    assert_that(extracted, instance_of(MemoryConfig))
    assert_that(extracted.name, is_("testdb"))
    assert_that(extracted.user, is_("admin"))


def test_extract_missing_section_raises(
    memory_cfg: t.Callable[..., MemoryConfig],
) -> None:
    cfg = memory_cfg()
    assert_that(
        calling(cfg.extract).with_args("nonexistent"),
        raises(ValueError),
    )


def test_extract_preserves_uppercase() -> None:
    extracted = MemoryConfig(data={"db": {"host": "localhost"}}).extract("db", uppercase=True)
    assert_that(extracted.uppercase, is_(True))


def test_extract_overrides_uppercase() -> None:
    cfg = MemoryConfig(data={"db": {"host": "localhost"}}, uppercase=False)
    extracted = cfg.extract("db", uppercase=True)

    assert_that(extracted.uppercase, is_(True))


def test_extract_keeps_parent_uppercase() -> None:
    cfg = MemoryConfig(data={"db": {"host": "localhost"}}, uppercase=True)
    # uppercase keys in raw: "DB" -> {"host": "localhost"}
    extracted = cfg.extract("DB")

    assert_that(extracted.uppercase, is_(True))


def test_convert_case_lowercase() -> None:
    cfg = MemoryConfig(data={})

    assert_that(cfg.convert_case("host"), is_("host"))


def test_convert_case_uppercase(memory_cfg: t.Callable[..., MemoryConfig]) -> None:
    cfg = r.uppercase(memory_cfg)
    assert_that(cfg.convert_case("host"), is_("HOST"))


def test_reload_warns() -> None:
    cfg = MemoryConfig(data={})

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cfg.reload()

    assert_that(len(caught), is_(1))
    assert_that(issubclass(caught[0].category, UserWarning), is_(True))
    assert_that("memory.Config.reload()" in str(caught[0].message), is_(True))
