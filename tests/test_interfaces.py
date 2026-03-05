from collections.abc import MutableMapping

from hamcrest import assert_that, calling, is_, none, raises

from config.constants import DEFAULT_CONFIG_FILENAME
from config.interfaces import EmptyType, FileType


def test_empty_type_container_is_none() -> None:
    class Dummy(metaclass=EmptyType):
        """A dummy class to test EmptyType metaclass."""

    assert_that(Dummy.container, is_(none()))


def test_file_type_creates_context() -> None:
    class TestType(FileType):
        @property
        def extension(cls):  # noqa: N805
            return "test"

    class DummyConfig(metaclass=TestType):
        container = "SOME_ENV_VAR"
        filename = "myconfig"

    assert_that(TestType.context["filename"], is_("myconfig"))


def test_file_type_default_filename() -> None:
    class TestType2(FileType):
        @property
        def extension(cls):  # noqa: N805
            return "test"

    class DummyConfig2(metaclass=TestType2):
        container = "ANOTHER_ENV_VAR"

    assert_that(TestType2.context["filename"], is_(DEFAULT_CONFIG_FILENAME))


def test_file_type_container_raises_when_file_not_found() -> None:
    class TestType3(FileType):
        @property
        def extension(cls):  # noqa: N805
            return "xyz"

    class DummyConfig3(metaclass=TestType3):
        container = "NONEXISTENT_ENV_VAR_12345"

    assert_that(
        calling(lambda: DummyConfig3.container),
        raises(FileNotFoundError),
    )


def test_file_type_scan_rules_format(env: MutableMapping[str, str]) -> None:
    env["TEST_SCAN_ENV"] = ""

    class TestType4(FileType):
        @property
        def extension(cls):  # noqa: N805
            return "json"

    class DummyConfig4(metaclass=TestType4):
        container = "TEST_SCAN_ENV"
        filename = "app"

    rules = DummyConfig4.scan_rules
    assert_that(len(rules) > 0, is_(True))

    has_filename_rule = any("app.json" in r for r in rules)
    assert_that(has_filename_rule, is_(True))
