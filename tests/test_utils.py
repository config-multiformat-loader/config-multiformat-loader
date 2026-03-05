from hamcrest import assert_that, is_, none
from pytest import mark

from config.utils import tree_extract


@mark.parametrize(
    ("key", "values", "expected"),
    [
        ("host", {"host": "localhost"}, "localhost"),
        ("db", {"db": {"name": "test"}}, {"name": "test"}),
        ("a.b", {"a": {"b": "value"}}, "value"),
        ("a.b.c", {"a": {"b": {"c": 42}}}, 42),
        ("missing", {"host": "localhost"}, None),
        ("a.missing", {"a": {"b": 1}}, None),
        ("a.b", {"a": "not_a_dict"}, None),
        ("a.b.c", {"a": {"b": "string"}}, None),
        ("only", {}, None),
        ("a.b", {"a": {"b": None}}, None),
        ("a.b", {"a": {"b": 0}}, 0),
        ("a.b", {"a": {"b": False}}, False),
        ("a.b", {"a": {"b": ""}}, ""),
        ("a.b", {"a": {"b": []}}, []),
    ],
    ids=[
        "top_level_key",
        "top_level_returns_dict",
        "two_level_nested",
        "three_level_nested",
        "missing_top_level",
        "missing_nested_key",
        "intermediate_not_dict_str",
        "intermediate_not_dict_deep",
        "empty_dict",
        "value_is_none",
        "value_is_zero",
        "value_is_false",
        "value_is_empty_string",
        "value_is_empty_list",
    ],
)
def test_tree_extract(key: str, values: dict, expected: object) -> None:
    result = tree_extract(key, values)

    if expected is None:
        assert_that(result, is_(none()))
    else:
        assert_that(result, is_(expected))
