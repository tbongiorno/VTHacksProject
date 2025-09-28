from flask import Flask, request, jsonify
import json

app = Flask(__name__)
SETTINGS_FILE = 'data.json'

history = []

def read_settings():
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def write_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4);

@app.route("/settings", methods=["GET"])
def get_settings():
    data = read_settings()
    return jsonify(data)

@app.route("/settings", methods=["POST"])
def update_settings():
    new_data = request.json
    write_settings(new_data)
    return jsonify({"message": "Settings updated successfully"})

@app.route('/')
def home():
    return "Payroll Budgeter Backend is running!"

@app.route('/budget', methods=['POST'])
def budget():
    data = request.get_json()
    paycheck = data.get("paycheck")
    categories = data.get("categories", {})  #{"Rent": {"type":"percentage", "value":40}, ...}

    result = {}
    total_spent = 0

    for name, cat in categories.items():
        cat_type = cat.get("type", "").lower()
        if cat_type in ["percent", "percentage"]:
            amount = int(paycheck * (cat["value"] / 100))
        elif cat_type == "fixed":
            amount = cat["value"]
        else:
            return jsonify({"error": f"Unknown type for category '{name}': {cat_type}"}), 400

        result[name] = amount
        total_spent += amount

    result["Remaining"] = paycheck - total_spent

    history.append({
        "paycheck": paycheck,
        "categories": categories,
        "result": result
    })

    return jsonify(result)


@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)


if __name__ == '__main__':
    app.run(debug=True)
