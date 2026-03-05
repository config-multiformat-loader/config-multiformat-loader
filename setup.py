#!/usr/bin/env python
from pathlib import Path

from app_cli import Cli, Command, echo
from tomlkit import dumps as toml_dump
from tomlkit import load as toml_load
from yaml import safe_load as yaml_loads


def create_cli() -> Cli:
    cli = Cli(__file__)
    cli.add_command("get-version", get_version())
    cli.add_command("update-poetry", update_poetry())

    return cli


def get_version() -> Command:
    def _version() -> None:
        with Path(".config/meta.yml").open(encoding="utf-8") as meta:
            project = yaml_loads(meta)
            echo(project["version"])

    return Command(
        name="get-version",
        callback=_version,
        help="Print current version of application",
    )


def update_poetry() -> Command:  # noqa: WPS231
    def _update() -> None:  # noqa: WPS231
        with Path("pyproject.toml").open(encoding="utf-8") as pypf:
            pyproject: dict = toml_load(pypf)

        project = pyproject["project"]
        poetry = pyproject["tool"]["poetry"]

        with Path(".config/meta.yml").open(encoding="utf-8") as f_meta:
            meta = yaml_loads(f_meta)
            project["name"] = meta["name"]
            project["description"] = meta["description"]
            project["authors"] = []
            project["authors"].extend(meta["authors"])

            project["dependencies"] = []
            for name, version in meta.get("deps", {}).items():
                if isinstance(version, str):
                    project["dependencies"].append(f"{name} ~= {version}")
                    continue
                if "custom" in version:
                    project["dependencies"].append(f"{name} {version['custom']}")
                    continue
                if "version" in version:
                    project["dependencies"].append(f"{name} == {version['version']}")

            project["urls"]["repository"] = meta["link"]

            if poetry.get("group") is None:
                poetry["group"] = {
                    "dev": {"dependencies": {}},
                    "linter": {"dependencies": {}},
                    "tests": {"dependencies": {}},
                }
            if "dev" not in poetry["group"]:
                poetry["group"]["dev"] = {"dependencies": {}}
            if "linter" not in poetry["group"]:
                poetry["group"]["linter"] = {"dependencies": {}}
            if "tests" not in poetry["group"]:
                poetry["group"]["tests"] = {"dependencies": {}}
            poetry["group"]["dev"]["dependencies"] = meta.get("dev", {}).get("deps", {})
            poetry["group"]["linter"]["dependencies"] = {
                **meta.get("linters", {}).get("types", {}),
                **meta.get("linters", {}).get("deps", {}),
            }
            poetry["group"]["tests"]["dependencies"] = meta.get("tests", {}).get("deps", {})

        Path("pyproject.toml").write_text(toml_dump(pyproject), encoding="utf-8")

    return Command(name="update-poetry", callback=_update, help="Update poetry in pyproject.toml")


if __name__ == "__main__":
    create_cli().start()
