import argparse
import json


def load_orders(filepath):
    with open(filepath) as f:
        return json.load(f)


def build_customers(orders):
    customers = {}
    for order in orders:
        phone = order["phone"]
        name = order["name"]
        customers[phone] = name
    return customers


def build_items(orders):
    items = {}
    for order in orders:
        for item in order["items"]:
            item_name = item["name"]
            price = item["price"]
            if item_name not in items:
                items[item_name] = {"price": price, "orders": 0}
            items[item_name]["orders"] += 1
    return items


def save_json(data, filepath):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def main():
    parser = argparse.ArgumentParser(description="Analyze Dosa restaurant orders.")
    parser.add_argument("orders_file", help="Path to the JSON orders file")
    args = parser.parse_args()

    orders = load_orders(args.orders_file)

    customers = build_customers(orders)
    save_json(customers, "customers.json")
    print(f"Saved {len(customers)} customers to customers.json")

    items = build_items(orders)
    save_json(items, "items.json")
    print(f"Saved {len(items)} items to items.json")


if __name__ == "__main__":
    main()
