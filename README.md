# Config Multiformat Loader

A Python library for loading application configuration from multiple file formats (JSON5 and YAML) with a unified, attribute-based API and a factory that selects the backend automatically via an environment variable.

**PyPI:** <https://pypi.org/project/config-multiformat-loader/>  
**Repository:** <https://github.com/config-multiformat-loader/config-multiformat-loader>  
**Current version:** 1.0.0  
**Requires:** Python ≥ 3.12

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)  
   2.1 [Module map](#module-map)  
   2.2 [Class hierarchy](#class-hierarchy)  
   2.3 [Metaclass machinery](#metaclass-machinery)  
   2.4 [Factory and backend selection](#factory-and-backend-selection)
3. [Features](#features)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage examples](#usage-examples)  
   6.1 [Factory (recommended)](#61-factory-recommended)  
   6.2 [Direct backend instantiation](#62-direct-backend-instantiation)  
   6.3 [Section extraction](#63-section-extraction)  
   6.4 [Dot-notation deep sections](#64-dot-notation-deep-sections)  
   6.5 [Uppercase key normalization](#65-uppercase-key-normalization)  
   6.6 [In-memory config (tests)](#66-in-memory-config-tests)  
   6.7 [Stub config (safe no-op)](#67-stub-config-safe-no-op)
7. [Deployment](#deployment)  
   7.1 [Environment variables reference](#environment-variables-reference)  
   7.2 [File discovery rules](#file-discovery-rules)
8. [Testing](#testing)
9. [Design decisions](#design-decisions)
10. [Changelog](#changelog)

---

## Overview

`config-multiformat-loader` provides a single import point — `config.Config` — that transparently returns the right config backend depending on the `APP_CONFIG_SOURCE` environment variable. All backends share the same interface: config values are exposed as plain instance attributes.

```python
from config import Config

cfg = Config()        # reads APP_CONFIG_SOURCE to decide what to load
print(cfg.database_host)        # attribute access
print(cfg.get("timeout", 30))   # safe access with a default
db = cfg.extract("database")    # sub-config scoped to the "database" section
```

---

## Architecture

### Module map

```shell
config/
├── __init__.py       # Public entry point — factory class Config
├── baseclasses.py    # ConfigInterface (abstract) + BaseConfig (shared logic)
├── interfaces.py     # FileType metaclass + EmptyType metaclass
├── constants.py      # SOURCE enum, RESERVED_CLASS_NAMES, default constants
├── utils.py          # tree_extract() — dot-notation key navigation
├── json.py           # JSON5 backend  (metaclass = JSONType → FileType)
├── yaml.py           # YAML backend   (metaclass = YAMLType → FileType)
├── stub.py           # Silent no-op   (metaclass = EmptyType)
└── memory.py         # In-memory dict (metaclass = EmptyType)
```

### Class hierarchy

```schema
ConfigInterface          ← abstract interface (reload, extract, get, to_dict)
    └── BaseConfig       ← shared file-backed logic (_apply_dict, convert_case, …)
            ├── json.Config   (metaclass=JSONType  → FileType)
            └── yaml.Config   (metaclass=YAMLType  → FileType)

ConfigInterface
    ├── stub.Config   (metaclass=EmptyType)
    └── memory.Config (metaclass=EmptyType)

config.Config            ← factory: __new__ returns one of the four backends
```

### Metaclass machinery

Two metaclasses drive the backend system.

**`FileType`** (used by JSON and YAML backends)

At class-creation time `FileType.__new__` intercepts two special class-body attributes and moves them out of the class namespace:

| Attribute   | Env variable it reads                               | Purpose                               |
| ----------- | --------------------------------------------------- | ------------------------------------- |
| `container` | value of the env var whose *name* is specified here | absolute path to the config file      |
| `filename`  | *(literal, not an env var)*                         | fallback filename used by scan rules  |

The `container` *property* (on the metaclass, so it's a class-level descriptor) scans a set of path patterns (`scan_rules`) at access time and returns the first file whose extension matches the backend. This means **no environment variable needs to be set in advance** — the library will try several well-known locations automatically.

**`EmptyType`** (used by `stub.Config` and `memory.Config`)

A minimal metaclass whose `container` property always returns `None`. These backends do not need a file on disk.

### Factory and backend selection

`config.Config.__new__` reads `APP_CONFIG_SOURCE` and uses Python 3.10+ structural pattern matching to return the right concrete instance:

| `APP_CONFIG_SOURCE`   | Returned type                     |
| --------------------- | --------------------------------- |
| `json`                | `json.Config`                     |
| `yaml`                | `yaml.Config`                     |
| `stub`                | `stub.Config`                     |
| `memory`              | `memory.Config`                   |
| *(unset)*             | `json.Config` (silent default)    |
| *(unknown value)*     | `json.Config` + `UserWarning`     |

---

## Features

- **Single import, multiple backends** — swap `json` ↔ `yaml` ↔ `stub` ↔ `memory` by changing one env variable; no code changes required.
- **Attribute-based access** — `cfg.my_key` instead of `cfg["my_key"]`; keeps consumer code clean.
- **Safe fallback access** — `cfg.get("key", default)` never raises.
- **Section scoping** — `cfg.extract("database")` returns a new config object containing only the keys inside that nested section.
- **Deep dot-notation sections** — `cfg.extract("nested.level1.level2")` traverses arbitrarily deep trees.
- **Uppercase normalization** — set `uppercase=True` to have all keys converted to `UPPER_CASE` at load time; useful when bridging config files and `os.environ`-style code.
- **JSON5 support** — comments and trailing commas are allowed in JSON config files (via `pyjson5`).
- **YAML support** — via `PyYAML` with `safe_load` to prevent arbitrary object deserialization.
- **Reserved-name protection** — config keys that would shadow built-in methods (`get`, `reload`, `extract`, …) are silently dropped with a `UserWarning`.
- **Stub backend** — every attribute access returns `None`, every `get()` returns the supplied default; safe to use in environments where no config file exists.
- **Memory backend** — accepts a plain `dict`; designed for unit tests. Eliminates the need for mocking file I/O.
- **Hot reload** — `cfg.reload()` re-reads the file from disk and updates all attributes in place (file-backed backends only).
- **`to_dict()` export** — returns a plain `{key: value}` dict containing only config data; internal attributes (`configfile`, `section`, etc.) are excluded automatically.
- **Prefix filtering in `to_dict`** — `cfg.to_dict(prefix="db_")` returns only keys that start with `db_`.

---

## Installation

### With Poetry (recommended)

```bash
poetry add config-multiformat-loader
```

### With pip

```bash
pip install config-multiformat-loader
```

### From source (development)

```bash
git clone https://github.com/config-multiformat-loader/config-multiformat-loader.git
cd config
poetry install --with tests,linter
```

---

## Configuration

### Environment variables reference

| Variable              | Required  | Default               | Description                                                                                   |
| --------------------- | --------- | --------------------- | --------------------------------------------------------------------------------------------- |
| `APP_CONFIG_SOURCE`   | No        | `json`                | Backend to use: `json`, `yaml`, `stub`, `memory`.                                             |
| `APP_CONFIG_FILE`     | No*       | *(auto-discovered)*   | Absolute or relative path to the config file. Read by both `json.Config` and `yaml.Config`.   |

\* If `APP_CONFIG_FILE` is not set the library applies the [file discovery rules](#file-discovery-rules) to locate the file.

### File discovery rules

When `APP_CONFIG_FILE` is set to a path (e.g. `/etc/myapp/settings`), the backend tries the following patterns in order, stopping at the first existing file whose extension matches the backend:

| Pattern                       | Example (json backend)                                |
| ----------------------------- | ----------------------------------------------------- |
| `{path}`                      | `/etc/myapp/settings`                                 |
| `{path}.{ext}`                | `/etc/myapp/settings.json`                            |
| `{filename}.{ext}`            | `configuration.json` *(relative, default filename)*   |
| `../data/{path}`              | `../data/settings`                                    |
| `../data/{path}.{ext}`        | `../data/settings.json`                               |
| `../data/{filename}.{ext}`    | `../data/configuration.json`                          |

The default filename (`configuration`) is defined in `constants.DEFAULT_CONFIG_FILENAME` and can be overridden per-backend by setting `filename = "myapp"` in the class body.

---

## Usage examples

### 6.1 Factory (recommended)

```python
import os
from config import Config

os.environ["APP_CONFIG_SOURCE"] = "json"
os.environ["APP_CONFIG_FILE"] = "/etc/myapp/config.json"

cfg = Config()
print(cfg.host)         # "localhost"
print(cfg.port)         # 8080
print(cfg.debug)        # True
```

### 6.2 Direct backend instantiation

```python
from config.json import Config as JsonConfig
from config.yaml import Config as YamlConfig

# Use the JSON backend directly (ignores APP_CONFIG_SOURCE)
cfg = JsonConfig()

# YAML backend
cfg = YamlConfig()
```

### 6.3 Section extraction

Given a config file:

```json
{
    "host": "localhost",
    "database": {
        "name": "mydb",
        "user": "admin",
        "password": "secret"
    }
}
```

```python
cfg = Config()

db = cfg.extract("database")
print(db.name)      # "mydb"
print(db.user)      # "admin"

# The original cfg is unchanged
print(cfg.host)     # "localhost"
```

### 6.4 Dot-notation deep sections

```python
# Config file contains: {"nested": {"level1": {"level2": {"value": "deep"}}}}

cfg = Config()
deep = cfg.extract("nested.level1.level2")
print(deep.value)   # "deep"
```

### 6.5 Uppercase key normalization

Useful when your config keys should match `os.environ`-style names:

```python
cfg = Config(uppercase=True)
print(cfg.DATABASE_HOST)    # keys from file are uppercased at load time

# Works with extract too
db = cfg.extract("DATABASE", uppercase=True)
print(db.NAME)
```

### 6.6 In-memory config (tests)

`memory.Config` takes a dict directly — no file needed. It is the recommended approach for unit tests.

```python
from config.memory import Config as MemoryConfig

cfg = MemoryConfig(data={"host": "127.0.0.1", "port": 5432})

print(cfg.host)                 # "127.0.0.1"
print(cfg.get("timeout", 30))   # 30  (default, key absent)
print(cfg.to_dict())            # {"host": "127.0.0.1", "port": 5432}

# extract works the same way
db = MemoryConfig(data={"database": {"name": "testdb"}})
section = db.extract("database")
print(section.name)             # "testdb"
```

Using the `APP_CONFIG_SOURCE=memory` env variable in a test suite:

```python
import pytest
from config import Config

@pytest.fixture(autouse=True)
def memory_config(monkeypatch):
    monkeypatch.setenv("APP_CONFIG_SOURCE", "memory")

def test_something():
    cfg = Config(data={"timeout": 10})
    assert cfg.timeout == 10
```

### 6.7 Stub config (safe no-op)

`stub.Config` never raises; every attribute returns `None`, every `get()` returns the default.  
Use it in environments where configuration is optional or not yet available.

```python
from config.stub import Config as StubConfig

cfg = StubConfig()
print(cfg.anything)               # None — no AttributeError
print(cfg.get("key", "default"))  # "default"

sub = cfg.extract("section")
print(sub.value)                  # None — still silent
```

### Reloading from disk

```python
cfg = Config()
# ... some time passes, the file changes ...
cfg.reload()
print(cfg.new_key)  # reflects the updated file
```

### Exporting to dict

```python
cfg = Config()
data = cfg.to_dict()          # all keys
subset = cfg.to_dict("db_")   # only keys starting with "db_"
```

---

## Deployment

### Docker / container environments

Set the two environment variables at runtime:

```dockerfile
ENV APP_CONFIG_SOURCE=json
ENV APP_CONFIG_FILE=/app/config/settings.json
```

Or pass them through `docker run`:

```bash
docker run \
  -e APP_CONFIG_SOURCE=yaml \
  -e APP_CONFIG_FILE=/etc/myapp/config.yml \
  myapp:latest
```

### Kubernetes

```yaml
env:
  - name: APP_CONFIG_SOURCE
    value: "yaml"
  - name: APP_CONFIG_FILE
    valueFrom:
      configMapKeyRef:
        name: myapp-config
        key: config_path
```

## Testing

### Running the test suite

```bash
# Install test dependencies
poetry install --with tests

# Run all tests with coverage
task test

# Or invoke pytest directly
pytest -vx --cov=config --cov-report=term-missing tests/
```

### Running linters

```bash
task lint          # runs all linters in sequence

task lint-ruff     # ruff (fast linter + formatter)
task lint-flake    # flake8 + wemake-python-styleguide
task lint-mypy     # mypy (strict static typing)
task lint-vulture  # vulture (dead code detection)
```

### Test structure

```shell
tests/
├── conftest.py           # re-exports all shared fixtures
├── fixtures.py           # pytest fixtures (env, json_ctx, yaml_ctx, memory_cfg, concrete_cfg)
├── constants.py          # shared test data (JSON_CONFIG_DATA, YAML_CONFIG_DATA, …)
├── utils.py              # ConcreteConfig — a minimal concrete subclass of BaseConfig
├── data/
│   ├── configuration.json
│   └── configuration.yml
├── reducers/
│   └── memory.py         # helper factory functions for memory.Config variants
├── test_factory.py       # config.Config factory (backend selection, fallback, warnings)
├── test_baseclasses.py   # BaseConfig shared logic
├── test_interfaces.py    # FileType / EmptyType metaclass behaviour
├── test_json.py          # JSON backend
├── test_yaml.py          # YAML backend
├── test_memory.py        # memory.Config
├── test_stub.py          # stub.Config
├── test_source.py        # SOURCE enum
└── test_utils.py         # tree_extract()
```

### Key testing patterns

**Isolating env variables** — the `env` fixture captures and restores `os.environ` after each test:

```python
def test_factory_json(env):
    env["APP_CONFIG_SOURCE"] = "json"
    cfg = Config()
    assert isinstance(cfg, JsonConfig)
```

**Isolating file paths** — `json_ctx` / `yaml_ctx` fixtures temporarily redirect the metaclass's path context to the `tests/data/` directory, so tests never touch production files:

```python
@pytest.mark.usefixtures("json_ctx")
def test_reads_host(env):
    env["APP_CONFIG_SOURCE"] = "json"
    cfg = Config()
    assert cfg.host == "localhost"
```

**In-memory config in tests** — use `memory_cfg` fixture to avoid all file I/O in unit tests:

```python
def test_something(memory_cfg):
    cfg = memory_cfg({"timeout": 5})
    assert cfg.timeout == 5
```

---

## Design decisions

### 1. `__new__` instead of `__init__` in the factory

`config.Config.__new__` returns an instance of a *different* class (one of the four backends). Python's `__init__` on the factory class would then be called on that foreign instance, which is wrong. Using `__new__` for the factory and letting each backend's own `__new__` / `__init__` handle construction avoids this pitfall cleanly. `BaseConfig` itself also uses `__new__` for the same reason — `FileType` metaclass descriptors interact with class construction, and separating allocation from population keeps the logic explicit.

### 2. Metaclass-based file resolution (`FileType`)

The class body of `json.Config` declares `container = "APP_CONFIG_FILE"` and `filename = "configuration"`. These are *not* regular class attributes — `FileType.__new__` removes them from the class namespace and stores them in `cls.context` during class definition. At instantiation time, `cls.container` (a metaclass property) reads the env variable and runs the scan rules to find an actual file path. This design means:

- The concrete class declaration is declarative and readable.
- File resolution is lazy — it only runs when an instance is created.
- The metaclass can be reused for any future file-based backend without duplicating the scanning logic.

### 3. Scan rules with multiple path patterns

Rather than requiring an exact path, the backend tries six path patterns. This makes the library usable out of the box in common project layouts (`./configuration.json`, `./configuration.yml`, `../data/configuration.json`, etc.) without any configuration, while still respecting an explicit `APP_CONFIG_FILE` override when provided. Note: the `container` property performs filesystem I/O on each access; the result is captured once during `__new__` and stored as `configfile` on the instance.

### 4. `pyjson5` instead of the standard `json` module

JSON5 is a superset of JSON that allows comments (`// …`, `/* … */`) and trailing commas. Configuration files often benefit from inline documentation; using `pyjson5` lets developers annotate their config without breaking the parser. Standard-format JSON files are fully compatible with `pyjson5`.

### 5. `yaml.safe_load` instead of `yaml.load`

`PyYAML`'s `yaml.load` can deserialize arbitrary Python objects, which is a code-execution vector when the config file is not fully trusted. `safe_load` restricts the parser to standard YAML scalars, lists, and mappings, which is all a configuration file ever needs.

### 6. Dynamic attributes rather than a fixed schema

Config values are set as instance attributes via `setattr` in `_apply_dict`. There is no predefined schema class. This means:

- The library is format-agnostic — any valid key in the file becomes accessible.
- `to_dict()` returns only `vars(self)` entries that are not internal attributes, so the public API is clean.
- The tradeoff is that typos in key names are silent at runtime; users who need schema validation can layer Pydantic or similar on top of `to_dict()`.

### 7. Reserved-name protection with `RESERVED_CLASS_NAMES`

The `BaseConfig` instance exposes methods like `get`, `reload`, `extract`, and `to_dict`. If a config file contained a key with the same name, `setattr` would silently shadow the method, causing confusing behaviour. Instead, `_apply_dict` checks every key against `RESERVED_CLASS_NAMES` and emits a `UserWarning` while skipping the key. This surfaces the conflict at startup rather than causing a hard-to-debug runtime failure later.

### 8. `object.__setattr__` for internal properties

During `__new__`, internal fields (`uppercase`, `section`, `configfile`, `_properties`) are written via `object.__setattr__` rather than a plain `self.x = …` assignment. This bypasses any potential `__setattr__` override in subclasses, guaranteeing that the framework's own bookkeeping attributes are always set correctly.

### 9. `warnings.warn` for unknown `APP_CONFIG_SOURCE`

When an unrecognised value is set for `APP_CONFIG_SOURCE` the library issues a `UserWarning` and falls back to `json.Config`. Raising an exception at import time or during application startup would crash the service for a simple typo in an env variable. A warning surfaces the problem in logs while keeping the application operational.

### 10. `deepcopy` in `memory.Config`

The `data` dict passed to `memory.Config(data=…)` is deep-copied at construction time. This prevents mutation of the caller's dict from affecting the config object (and vice versa), which is important in test suites where the same fixture dict is reused across multiple tests.

### 11. `EmptyType` for stub and memory backends

Neither `stub.Config` nor `memory.Config` reads files; they do not need the path-scanning logic of `FileType`. Using a separate lightweight metaclass (`EmptyType`) that always returns `None` for `container` keeps both backends self-contained and free of any filesystem coupling.

### 12. `memory.Config.reload()` warns instead of being a no-op

Calling `reload()` on an in-memory config silently doing nothing would be confusing — the developer might expect data to refresh. Instead, the method emits a `UserWarning` that clearly explains the behaviour ("the in-memory store is not backed by an external source"). This makes the contract explicit without raising an error.

---

## Changelog

### 1.0.0

Initial public release. Requires Python ≥ 3.12.

Factory

- `config.Config` factory class — `__new__` reads `APP_CONFIG_SOURCE` and returns the matching backend instance without requiring any code changes in consumer code.
- Backend selection uses Python 3.10+ structural pattern matching (`match`/`case`).
- Unknown `APP_CONFIG_SOURCE` values fall back to `json.Config` and emit a `UserWarning` instead of raising, keeping the application operational on a misconfigured env variable.

Backends

- `json.Config` — JSON5 backend via `pyjson5`; supports comments (`// …`, `/* … */`) and trailing commas in config files; all standard JSON files are fully compatible.
- `yaml.Config` — YAML backend via `PyYAML`; uses `safe_load` to prevent arbitrary Python-object deserialization.
- `stub.Config` — silent no-op backend; every attribute access returns `None`, every `get()` call returns the supplied default; `extract()` returns a new stub instance, consistent with other backends.
- `memory.Config` — in-memory dict backend designed for unit tests; eliminates mock-based file I/O; the supplied `data` dict is deep-copied at construction time to prevent cross-test mutation.

Metaclass machinery

- `FileType` metaclass for file-backed backends (`json.Config`, `yaml.Config`): intercepts `container` and `filename` class-body attributes at class-creation time, stores them in `cls.context`, and exposes `cls.container` as a lazy class-level property that runs scan rules against the filesystem.
- Six-pattern file scan rules — when `APP_CONFIG_FILE` is set, each backend tries the bare path, the path with extension, the default filename, and three `../data/`-prefixed variants, stopping at the first match.
- `EmptyType` metaclass for `stub.Config` and `memory.Config`: always returns `None` for `container`; keeps non-file backends free of any filesystem coupling.

Shared interface (`ConfigInterface` / `BaseConfig`)

- Attribute-based access — config keys are set as plain instance attributes via `setattr` in `_apply_dict`; `cfg.my_key` works without `cfg["my_key"]`.
- `get(key, default=None)` — safe key lookup that never raises `AttributeError`.
- `extract(section)` — returns a new config object scoped to a nested section; supports dot-notation paths (`"nested.level1.level2"`) for arbitrarily deep traversal via `utils.tree_extract()`.
- `uppercase` parameter — pass `uppercase=True` at construction time to have all keys uppercased at load; also accepted by `extract()`.
- `reload()` — re-reads the file from disk and refreshes all attributes in place (file-backed backends); `memory.Config.reload()` emits `UserWarning` rather than silently doing nothing.
- `to_dict()` — returns a plain `{key: value}` dict of config data, excluding internal attributes (`configfile`, `section`, `_properties`, etc.); accepts an optional `prefix` argument to filter keys by prefix.

Safety and correctness

- Reserved-name protection — `_apply_dict` checks every incoming key against `RESERVED_CLASS_NAMES` and emits a `UserWarning` while skipping any key that would shadow a method (`get`, `reload`, `extract`, `to_dict`, …); also skips keys that start with `_`.
- Internal properties (`uppercase`, `section`, `configfile`, `_properties`) are written via `object.__setattr__` to bypass any subclass `__setattr__` override.
- `APP_CONFIG_FILE` environment variable — explicit path override accepted by both file-backed backends; path resolution and scan rules still apply when the value lacks a file extension.
