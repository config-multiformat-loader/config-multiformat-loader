import typing as t

import os
import shutil
from pathlib import Path

import yaml
from hamcrest import assert_that, calling, instance_of, is_, raises
from pytest import mark

from config.yaml import Config as YamlConfig
from config.yaml import YAMLType

from .constants import YAML_CONFIG_DATA, YAML_PORT
from .fixtures import DATA_DIR


@mark.usefixtures("yaml_ctx")
def test_load_from_file() -> None:
    cfg = YamlConfig()

    assert_that(cfg.service, is_("test-service"))
    assert_that(cfg.port, is_(YAML_PORT))


@mark.usefixtures("yaml_ctx")
def test_load_with_section() -> None:
    cfg = YamlConfig(section="logging")

    assert_that(cfg.level, is_("DEBUG"))
    assert_that(cfg.file, is_("/var/log/test.log"))


@mark.usefixtures("yaml_ctx")
def test_load_missing_section_raises() -> None:
    assert_that(
        calling(YamlConfig).with_args(section="nonexistent"),
        raises(ValueError),
    )


@mark.usefixtures("yaml_ctx")
def test_load_with_uppercase() -> None:
    cfg = YamlConfig(uppercase=True)

    assert_that(cfg.SERVICE, is_("test-service"))
    assert_that(cfg.PORT, is_(YAML_PORT))


@mark.usefixtures("yaml_ctx")
def test_to_dict() -> None:
    cfg = YamlConfig(section="logging")
    result = cfg.to_dict()

    assert_that(result, is_({"level": "DEBUG", "file": "/var/log/test.log"}))


@mark.usefixtures("yaml_ctx")
def test_extract() -> None:
    cfg = YamlConfig()
    extracted = cfg.extract("logging")

    assert_that(extracted, instance_of(YamlConfig))
    assert_that(extracted.level, is_("DEBUG"))


def test_reload(tmp_path: Path) -> None:
    config_path = tmp_path / "configuration.yml"
    shutil.copy(DATA_DIR / "configuration.yml", config_path)
    old_path = YAMLType.context.get("path", "")
    YAMLType.context["path"] = str(config_path)
    try:
        cfg = YamlConfig()

        assert_that(cfg.service, is_("test-service"))

        new_data = {**YAML_CONFIG_DATA, "service": "updated-service"}
        config_path.write_text(yaml.dump(new_data), encoding="utf-8")
        cfg.reload()

        assert_that(cfg.service, is_("updated-service"))
    finally:
        YAMLType.context["path"] = old_path


def test_file_not_found_raises() -> None:
    old_path = YAMLType.context.get("path", "")
    YAMLType.context["path"] = "/nonexistent/path/config.yml"
    try:
        assert_that(
            calling(YamlConfig),
            raises(FileNotFoundError),
        )
    finally:
        YAMLType.context["path"] = old_path


def test_file_discovery_by_filename() -> None:
    old_path = YAMLType.context.get("path", "")
    YAMLType.context["path"] = ""
    original_cwd = Path.cwd()
    os.chdir(DATA_DIR)
    try:
        cfg = YamlConfig()
        assert_that(cfg.service, is_("test-service"))
    finally:
        os.chdir(original_cwd)
        YAMLType.context["path"] = old_path


def test_yaml_type_extension() -> None:
    class DummyMeta(YAMLType):
        context: t.ClassVar[dict] = {}

    assert_that(DummyMeta.extension.fget(DummyMeta), is_("yml"))  # type: ignore[union-attr]


@mark.usefixtures("yaml_ctx")
def test_getitem() -> None:
    cfg = YamlConfig()

    assert_that(cfg["service"], is_("test-service"))
    assert_that(cfg["port"], is_(YAML_PORT))
