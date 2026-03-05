import typing as t

import json
import os
import shutil
from pathlib import Path

from hamcrest import assert_that, calling, instance_of, is_, raises
from pytest import mark

from config.json import Config as JsonConfig
from config.json import JSONType

from .constants import JSON_CONFIG_DATA, PORT, SECTION_KEY
from .fixtures import DATA_DIR


@mark.usefixtures("json_ctx")
def test_load_from_file() -> None:
    cfg = JsonConfig()

    assert_that(cfg.host, is_("localhost"))
    assert_that(cfg.port, is_(PORT))
    assert_that(cfg.debug, is_(True))


@mark.usefixtures("json_ctx")
def test_load_with_section() -> None:
    cfg = JsonConfig(section=SECTION_KEY)

    assert_that(cfg.name, is_("testdb"))
    assert_that(cfg.user, is_("admin"))
    assert_that(cfg.password, is_("secret"))


@mark.usefixtures("json_ctx")
def test_load_missing_section_raises() -> None:
    assert_that(
        calling(JsonConfig).with_args(section="nonexistent"),
        raises(ValueError),
    )


@mark.usefixtures("json_ctx")
def test_load_nested_section() -> None:
    cfg = JsonConfig(section="nested.level1.level2")

    assert_that(cfg.value, is_("deep"))


@mark.usefixtures("json_ctx")
def test_load_with_uppercase() -> None:
    cfg = JsonConfig(uppercase=True)

    assert_that(cfg.HOST, is_("localhost"))
    assert_that(cfg.PORT, is_(PORT))


@mark.usefixtures("json_ctx")
def test_to_dict() -> None:
    cfg = JsonConfig(section=SECTION_KEY)
    result = cfg.to_dict()

    assert_that(result, is_({"name": "testdb", "user": "admin", "password": "secret"}))


@mark.usefixtures("json_ctx")
def test_extract() -> None:
    cfg = JsonConfig()
    extracted = cfg.extract(SECTION_KEY)

    assert_that(extracted, instance_of(JsonConfig))
    assert_that(extracted.name, is_("testdb"))


def test_reload(tmp_path: Path) -> None:
    config_path = tmp_path / "configuration.json"
    shutil.copy(DATA_DIR / "configuration.json", config_path)
    old_path = JSONType.context.get("path", "")
    JSONType.context["path"] = str(config_path)
    try:
        cfg = JsonConfig()

        assert_that(cfg.host, is_("localhost"))

        new_data = {**JSON_CONFIG_DATA, "host": "newhost"}
        config_path.write_text(json.dumps(new_data), encoding="utf-8")
        cfg.reload()

        assert_that(cfg.host, is_("newhost"))
    finally:
        JSONType.context["path"] = old_path


def test_file_not_found_raises() -> None:
    old_path = JSONType.context.get("path", "")
    JSONType.context["path"] = "/nonexistent/path/config.json"
    try:
        assert_that(
            calling(JsonConfig),
            raises(FileNotFoundError),
        )
    finally:
        JSONType.context["path"] = old_path


def test_file_discovery_by_filename() -> None:
    old_path = JSONType.context.get("path", "")
    JSONType.context["path"] = ""
    original_cwd = Path.cwd()
    os.chdir(DATA_DIR)
    try:
        cfg = JsonConfig()
        assert_that(cfg.host, is_("localhost"))
    finally:
        os.chdir(original_cwd)
        JSONType.context["path"] = old_path


def test_json_type_extension() -> None:
    class DummyMeta(JSONType):
        context: t.ClassVar[dict] = {}

    assert_that(DummyMeta.extension.fget(DummyMeta), is_("json"))  # type: ignore[union-attr]


@mark.usefixtures("json_ctx")
def test_getitem() -> None:
    cfg = JsonConfig()

    assert_that(cfg["host"], is_("localhost"))
    assert_that(cfg["port"], is_(PORT))
