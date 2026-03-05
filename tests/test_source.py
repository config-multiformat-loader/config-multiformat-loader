from hamcrest import assert_that, is_, none
from pytest import mark

from config.constants import SOURCE


@mark.parametrize(
    ("name", "expected"),
    [
        ("json", SOURCE.json),
        ("yaml", SOURCE.yaml),
        ("memory", SOURCE.memory),
        ("stub", SOURCE.stub),
        (None, None),
        ("unknown", None),
        ("", None),
        ("JSON", None),
    ],
    ids=[
        "json",
        "yaml",
        "memory",
        "stub",
        "none_input",
        "unknown_string",
        "empty_string",
        "uppercase_json",
    ],
)
def test_source_get(name: str | None, expected: SOURCE | None) -> None:
    result = SOURCE.get(name)

    if expected is None:
        assert_that(result, is_(none()))
    else:
        assert_that(result, is_(expected))


@mark.parametrize(
    "member",
    [SOURCE.json, SOURCE.yaml, SOURCE.memory, SOURCE.stub],
    ids=["json", "yaml", "memory", "stub"],
)
def test_source_value_matches_name(member: SOURCE) -> None:
    assert_that(member.value, is_(member.name))
