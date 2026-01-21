#!/usr/bin/env python3
"""Simple launcher for the bot.

Usage:
  python run_bot.py

This imports the existing `main()` entrypoint in `src.core.main` so you can
start the bot without using `-m`.
"""
import os
import sys

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.chdir(ROOT)

try:
  from src.core.main import main
except ModuleNotFoundError as e:
  missing = e.name
  print("Error: missing Python module:", missing)
  print()
  print("Suggested fix:")
  print("  1) Activate the Python environment you use for the project (if any).")
  print("  2) Install the missing package. Example (PowerShell):")
  print()
  print(r"     python -m pip install pyyaml")
  print()
  print("Or install all project requirements:")
  print()
  print(r"     python -m pip install -r requirements.txt")
  print()
  print("After installing, run this script again.")
  import sys
  sys.exit(1)


if __name__ == "__main__":
  main()
