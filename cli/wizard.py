def choose_from_list(title, items, label_fn):
    print(f"\n{title}")
    for i, item in enumerate(items, 1):
        print(f"{i}) {label_fn(item)}")

    while True:
        choice = input("Select: ")
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("Invalid option")


def choose_multiple(title, items):
    print(f"\n{title}")
    for i, item in enumerate(items, 1):
        print(f"{i}) {item}")

    while True:
        raw = input("Select (space separated): ")
        try:
            idxs = [int(x) - 1 for x in raw.split()]
            return [items[i] for i in idxs if 0 <= i < len(items)]
        except Exception:
            print("Invalid input")
