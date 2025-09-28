import requests

paycheck = int(input("Enter your paycheck: "))

categories = {}

while True:
    print("\nCurrent categories:", categories)
    action = input("What do you want to do? [add/delete/change/done]: ").strip().lower()

    if action == "add":
        name = input("Enter category name: ").strip()
        cat_type = input(f"Is {name} a fixed amount or percentage? ").strip().lower().replace(" ", "")

        if cat_type in ["percentage", "percent"]:
            value = float(input(f"Enter % of paycheck for {name}: "))
        elif cat_type in ["fixed", "fixedamount"]:
            value = int(input(f"Enter fixed amount for {name}: "))
        else:
            print("Invalid type. Please choose 'percentage' or 'fixed'.")
            continue

        categories[name] = {"type": cat_type, "value": value}

    elif action == "delete":
        name = input("Enter category to delete: ").strip()
        if name in categories:
            categories.pop(name)
        else:
            print(f"Category '{name}' not found.")

    elif action == "change":
        name = input("Enter category to change: ").strip()
        if name in categories:
            cat_type = input(f"Is {name} a fixed amount or percentage? ").strip().lower().replace(" ", "")

            if cat_type in ["percentage", "percent"]:
                value = float(input(f"Enter % of paycheck for {name}: "))
            elif cat_type in ["fixed", "fixedamount"]:
                value = int(input(f"Enter fixed amount for {name}: "))
            else:
                print("Invalid type.")
                continue

            categories[name] = {"type": cat_type, "value": value}
        else:
            print("Category not found.")

    elif action == "done":
        break
    else:
        print("Invalid option.")

payload = {
    "paycheck": paycheck,
    "categories": categories
}

try:
    response = requests.post("http://127.0.0.1:5001/budget", json=payload)
    print("\nBudget result:", response.json())
except Exception as e:
    print(f"Error connecting to backend: {e}")

try:
    history = requests.get("http://127.0.0.1:5001/history")
    print("\nHistory:", history.json())
except Exception as e:
    print(f"Error fetching history: {e}")