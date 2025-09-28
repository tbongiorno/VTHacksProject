#!/usr/bin/env python3
import runpy
import os

# Make sure current working directory is the script folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Path to the main script
script_to_run = os.path.join(os.path.dirname(__file__), "gemini_financial_advisor.py")

# Run the main script
if __name__ == "__main__":
    try:
        runpy.run_path(script_to_run, run_name="__main__")
    except FileNotFoundError:
        print("Error: gemini_financial_advisor.py not found!")
    except Exception as e:
        print(f"Error running gemini_financial_advisor.py: {e}")
