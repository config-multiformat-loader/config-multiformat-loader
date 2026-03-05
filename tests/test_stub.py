from hamcrest import assert_that, instance_of, is_, none
from pytest import mark

from config.stub import Config as StubConfig


def test_getattr_returns_none() -> None:
    cfg = StubConfig()

    assert_that(cfg.any_key, is_(none()))
    assert_that(cfg.another_key, is_(none()))
    assert_that(cfg.nested_deep_key, is_(none()))


def test_get_returns_default() -> None:
    cfg = StubConfig()

    assert_that(cfg.get("host"), is_(none()))
    assert_that(cfg.get("host", "fallback"), is_("fallback"))


@mark.parametrize(
    ("key", "default", "expected"),
    [
        ("host", None, None),
        ("host", "fallback", "fallback"),
        ("port", 8080, 8080),
        ("debug", False, False),
    ],
    ids=["none_default", "string_default", "int_default", "bool_default"],
)
def test_get_with_various_defaults(key: str, default: object, expected: object) -> None:
    cfg = StubConfig()
    result = cfg.get(key, default)

    assert_that(result, is_(expected))


def test_reload_returns_none() -> None:
    cfg = StubConfig()
    result = cfg.reload()

    assert_that(result, is_(none()))


def test_extract_returns_new_instance() -> None:
    cfg = StubConfig()
    extracted = cfg.extract("any_section")

    assert_that(extracted, instance_of(StubConfig))
    assert_that(extracted is not cfg, is_(True))


def test_extract_result_behaves_as_stub() -> None:
    cfg = StubConfig()
    extracted = cfg.extract("section")

    assert_that(extracted.any_key, is_(none()))
    assert_that(extracted.get("key", "default"), is_("default"))


def test_hasattr_always_true() -> None:
    cfg = StubConfig()

    assert_that(hasattr(cfg, "anything"), is_(True))
    assert_that(hasattr(cfg, "nonexistent_attribute"), is_(True))
    assert_that(hasattr(cfg, "deeply_nested_thing"), is_(True))


def test_stub_created_via_metaclass() -> None:
    cfg = StubConfig()

    assert_that(type(type(cfg)).__name__, is_("EmptyType"))
