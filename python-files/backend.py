#!/usr/bin/env python3
"""
Flask backend for FinancialPaycheckBudgeter:
 - Serves index.html (templates/index.html)
 - /budget (POST) expects {paycheck, categories} and returns allocations
 - /history (GET) returns stored history
 - /ai_chat (POST) expects {message, context} and returns {"reply": "..."}
Gemini integration is optional/controlled by GEMINI_API_KEY env var.
"""

from flask import Flask, request, jsonify, render_template
import os
import traceback

app = Flask(__name__, template_folder="templates")

# In-memory history (replace with DB for production)
history = []

# Optional Gemini initialization
GEMINI_API_KEY = os.getenv("AIzaSyAPuhVvLof6_2L7uLpBrhFpSQTibgKxXmE")
MODEL = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        MODEL = genai.GenerativeModel("gemini-1.5-turbo")
        print("Gemini model initialized.")
    except Exception as e:
        print("Warning: Gemini initialization failed:", e)
        MODEL = None
else:
    print("GEMINI_API_KEY not set — AI will use fallback responses.")

# Serve the SPA
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Budget allocation endpoint
@app.route("/budget", methods=["POST"])
def budget():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON payload."}), 400

        paycheck = data.get("paycheck")
        categories = data.get("categories", {})

        # Basic validation
        try:
            paycheck = float(paycheck)
            if paycheck < 0:
                raise ValueError()
        except Exception:
            return jsonify({"error": "Invalid 'paycheck' value; must be non-negative number."}), 400

        if not isinstance(categories, dict):
            return jsonify({"error": "'categories' must be an object/dictionary."}), 400

        result = {}
        total_spent = 0.0

        # Accept several synonyms for types
        for name, info in categories.items():
            if not isinstance(info, dict):
                return jsonify({"error": f"Invalid category format for '{name}'."}), 400

            ctype = str(info.get("type", "")).strip().lower()
            val = info.get("value", 0)

            if ctype in ("percent", "percentage", "pct"):
                try:
                    pct = float(val)
                except Exception:
                    return jsonify({"error": f"Invalid percentage for '{name}'."}), 400
                amount = round(paycheck * (pct / 100.0), 2)

            elif ctype in ("fixed", "fixedamount", "amount"):
                try:
                    amount = round(float(val), 2)
                except Exception:
                    return jsonify({"error": f"Invalid fixed amount for '{name}'."}), 400
            else:
                return jsonify({"error": f"Unknown type for category '{name}': {ctype}"}), 400

            result[name] = amount
            total_spent += amount

        remaining = round(paycheck - total_spent, 2)
        result["Remaining"] = remaining

        # store history (basic)
        history.append({
            "paycheck": round(paycheck, 2),
            "categories": categories,
            "result": result
        })

        return jsonify(result)

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": "Server error", "detail": str(exc)}), 500


# Simple history endpoint
@app.route("/history", methods=["GET"])
def get_history():
    return jsonify(history)


# AI chat endpoint (POST)
@app.route("/ai_chat", methods=["POST"])
def ai_chat():
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "Missing JSON body"}), 400

        message = payload.get("message", "").strip()
        context = payload.get("context", [])

        if not message:
            return jsonify({"error": "Empty message"}), 400

        # Build prompt from recent context (limit size)
        recent = []
        if isinstance(context, list):
            for turn in context[-8:]:
                role = turn.get("role", "user")
                txt = turn.get("text", "")
                recent.append(f"{role.title()}: {txt}")

        prompt = "\n".join(recent + [f"User: {message}", "Assistant:"])

        # If model available, call it; otherwise return a helpful fallback
        if MODEL:
            try:
                ai_resp = MODEL.generate_content(prompt)
                reply = getattr(ai_resp, "text", None) or str(ai_resp)
            except Exception as e:
                reply = f"AI error: {e}"
        else:
            # fallback: small friendly reply with budgeting tips (no external calls)
            reply = (
                "I can't access the AI engine right now. Quick guidance: pay essentials first (rent, utilities), "
                "save at least 10-20% if possible, and avoid allocating more than 100% of your paycheck to percentages. "
                "Ask me specifics like 'How much should I save if I earn $3000?'"
            )

        return jsonify({"reply": reply})

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": "Server error", "detail": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("BUDGETER_PORT", 5002))
    # Use debug=False in production
    app.run(debug=True, port=port, use_reloader=False)