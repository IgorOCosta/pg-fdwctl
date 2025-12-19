from cli.wizard import choose_from_list, choose_multiple
from engine.fdw_manager import FDWManager
from engine.postgres import PostgresConnection
import json

def load_config():
    with open("config/fdwctl.config.json") as f:
        return json.load(f)

def validate_user_selection(database, selected_schemas):
    available = set(database["schemas"])
    for s in selected_schemas:
        if s not in available:
            raise ValueError(
                f"Schema '{s}' does not exist in this database target"
            )

def main():
    config = load_config()

    target = choose_from_list(
        "🔎 Available targets:",
        config["targets"],
        lambda t: f"{t['client']} - {t['fdw_type']} - {t['connection']['jdbc']}"
    )

    database = choose_from_list(
        f"📦 Databases for {target['client']}:",
        target["databases"],
        lambda d: d["name"]
    )

    schemas = choose_multiple(
        "🗂 Schemas available:",
        database["schemas"]
    )

    try:
        validate_user_selection(database, schemas)
    except ValueError as e:
        print(f"❌ {e}")
        return

    print("\n⚙️ Action:")
    print("1) Install")
    print("2) Update (recreate)")
    print("3) Remove")

    action = input("Select action: ")

    action_map = {
        "1": "install",
        "2": "update",
        "3": "remove"
    }

    if action not in action_map:
        print("Invalid action")
        return

    pg = PostgresConnection(config["postgres"])
    manager = FDWManager(pg, config)

    manager.execute(
        target=target,
        database=database["name"],
        schemas=schemas,
        action=action_map[action]
    )

if __name__ == "__main__":
    main()
