class ConfigValidationError(Exception):
    pass


def validate_config(config: dict):
    required_root_keys = ["postgres", "defaults", "roles", "targets"]

    for key in required_root_keys:
        if key not in config:
            raise ConfigValidationError(f"Missing top-level key: '{key}'")

    validate_postgres(config["postgres"])
    validate_roles(config["roles"])
    validate_targets(config["targets"], config["roles"])


def validate_postgres(pg):
    for k in ("host", "port", "database", "user", "password"):
        if k not in pg:
            raise ConfigValidationError(f"Postgres config missing '{k}'")


def validate_roles(roles):
    if not roles:
        raise ConfigValidationError("At least one role must be defined")

    for r in roles:
        if "name" not in r:
            raise ConfigValidationError("Role missing 'name'")
        if "enabled" not in r:
            raise ConfigValidationError(f"Role '{r['name']}' missing 'enabled'")


def validate_targets(targets, roles):
    role_names = {r["name"] for r in roles}

    if not targets:
        raise ConfigValidationError("At least one target must be defined")

    for t in targets:
        for k in ("id", "client", "fdw_type", "connection", "databases"):
            if k not in t:
                raise ConfigValidationError(
                    f"Target missing '{k}': {t.get('id', 'unknown')}"
                )

        for db in t["databases"]:
            if "name" not in db:
                raise ConfigValidationError(
                    f"Database entry missing 'name' in target {t['id']}"
                )

            if "schemas" not in db:
                raise ConfigValidationError(
                    f"Database '{db['name']}' missing 'schemas'"
                )

            for s in db["schemas"]:
                if s not in role_names:
                    raise ConfigValidationError(
                        f"Schema '{s}' does not exist in roles list"
                    )
