from types import MappingProxyType

JSON_CONFIG_DATA = MappingProxyType({
    "host": "localhost",
    "port": 8080,
    "database": {
        "name": "testdb",
        "user": "admin",
        "password": "secret",
    },
    "debug": True,
    "nested": {
        "level1": {
            "level2": {
                "value": "deep",
            },
        },
    },
})

YAML_CONFIG_DATA = MappingProxyType({
    "service": "test-service",
    "port": 9090,
    "logging": {
        "level": "DEBUG",
        "file": "/var/log/test.log",
    },
})

MEMORY_CONFIG_DATA = MappingProxyType({
    "host": "127.0.0.1",
    "port": 5432,
    "name": "memdb",
    "timeout": 30,
})

SECTION_KEY = "database"
NESTED_SECTION_KEY = "nested.level1.level2"
MISSING_SECTION_KEY = "nonexistent"

HOST = "localhost"
PORT = 8080
DB_PORT = 5432
YAML_PORT = 9090
DB_NAME = "testdb"
TIMEOUT = 30
GET_DEFAULT = 42
NON_STRING_KEY = 123
