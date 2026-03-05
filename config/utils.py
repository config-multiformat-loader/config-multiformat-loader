def tree_extract(key: str, values: dict) -> dict | None:
    cfg = values

    for subsection in key.split("."):
        if not isinstance(cfg, dict) or subsection not in cfg:
            return None
        cfg = cfg[subsection]

    return cfg
