#!/usr/bin/env python3
"""
Main program:
 - collects paycheck + categories,
 - optionally calls Gemini (if configured/installed),
 - posts the budget to the backend and prints result & history.

This script is robust in the presence of a local 'requests.py' file:
it temporarily removes the project directory from sys.path to import
the real external `requests` package, then restores sys.path.
"""

import os
import sys
import importlib
import importlib.util

_this_dir = os.path.dirname(os.path.abspath(__file__))


def import_real_requests():
    """
    Import the system-installed 'requests' package even if there's a local requests.py.
    Returns the module or raises an ImportError.
    """
    removed = False
    if _this_dir in sys.path:
        sys.path.remove(_this_dir)
        removed = True

    try:
        spec = importlib.util.find_spec("requests")
        if spec is None:
            # fallback to standard import (may still fail)
            return importlib.import_module("requests")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if removed:
            sys.path.insert(0, _this_dir)


# Attempt to get real requests
try:
    requests = import_real_requests()
except Exception as e:
    print("ERROR: Could not import the real 'requests' package. Install it with: pip install requests")
    raise

# Try loading Google Gemini SDK if available (optional)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

# If GEMINI_API_KEY is set, use it; otherwise we'll skip AI call gracefully
GEMINI_API_KEY = os.getenv("AIzaSyAPuhVvLof6_2L7uLpBrhFpSQTibgKxXmE", None)

# ---------- User input (budget categories) ----------
def collect_budget():
    while True:
        try:
            paycheck = float(input("Enter your paycheck: ").strip())
            break
        except Exception:
            print("Invalid paycheck. Enter a number (e.g., 3000).")

    categories = {}
    while True:
        print("\nCurrent categories:", categories)
        action = input("What do you want to do? [add/delete/change/done]: ").strip().lower()

        if action == "add":
            name = input("Enter category name: ").strip()
            cat_type = input(f"Is {name} a fixed amount or percentage? ").strip().lower().replace(" ", "")
            if cat_type in ["percentage", "percent"]:
                try:
                    value = float(input(f"Enter % of paycheck for {name}: ").strip())
                except Exception:
                    print("Invalid percentage — try again.")
                    continue
            elif cat_type in ["fixed", "fixedamount"]:
                try:
                    value = float(input(f"Enter fixed amount for {name}: ").strip())
                except Exception:
                    print("Invalid fixed amount — try again.")
                    continue
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
                    try:
                        value = float(input(f"Enter % of paycheck for {name}: ").strip())
                    except Exception:
                        print("Invalid percentage — try again.")
                        continue
                elif cat_type in ["fixed", "fixedamount"]:
                    try:
                        value = float(input(f"Enter fixed amount for {name}: ").strip())
                    except Exception:
                        print("Invalid fixed amount — try again.")
                        continue
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

    return paycheck, categories


def ask_investment_questions():
    risk = input("\nAI Question: How much risk are you willing to take? [low/medium/high]: ").strip().lower()
    amount_preference = input("Do you want to allocate money as a fixed amount or percentage? ").strip().lower()
    investment_duration = input("How long do you wish to invest? [months/years]: ").strip().lower()
    return risk, amount_preference, investment_duration


def get_ai_advice(paycheck, risk, amount_pref, duration):
    prompt = (
        f"I have a paycheck of ${paycheck}. "
        f"My risk tolerance is {risk}. "
        f"I prefer to allocate money as {amount_pref}. "
        f"I plan to invest for {duration}. "
        "Please give me simple, personalized financial advice on how to invest and allocate my paycheck."
    )

    if not GENAI_AVAILABLE or not GEMINI_API_KEY:
        return "Gemini AI not available or GEMINI_API_KEY not set — skipping AI advice."

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Try recommended GenerativeModel API first; if it fails, try chat API fallback.
        try:
            model = genai.GenerativeModel("gemini-1.5-turbo")
            ai_resp = model.generate_content(prompt)
            # Depending on SDK version, the response text might be in different fields
            text = getattr(ai_resp, "text", None)
            if text is None:
                # attempt to stringify
                text = str(ai_resp)
        except Exception:
            # fallback to chat API style (older/newer SDKs differ)
            chat_resp = genai.chat.create(model="gemini-1.5-turbo", messages=[{"role": "user", "content": prompt}])
            text = chat_resp.last.response.content[0].text
        return text
    except Exception as e:
        return f"Error calling Gemini API: {e}"


def send_to_backend(paycheck, categories):
    payload = {"paycheck": paycheck, "categories": categories}
    try:
        resp = requests.post("http://127.0.0.1:5001/budget", json=payload, timeout=5)
        print("\nBudget result:", resp.json())
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return

    try:
        hist = requests.get("http://127.0.0.1:5001/history", timeout=5)
        print("\nHistory:", hist.json())
    except Exception as e:
        print(f"Error fetching history: {e}")


def main():
    paycheck, categories = collect_budget()
    # Ask AI questions
    risk, amount_pref, duration = ask_investment_questions()

    ai_advice = get_ai_advice(paycheck, risk, amount_pref, duration)
    print("\nAI Financial Advice:")
    print(ai_advice)

    # Send to backend (uses the real `requests` package)
    send_to_backend(paycheck, categories)


if __name__ == "__main__":
    main()