# main.py
import os
import sys

PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from telegramwordcloud.ui import run_app

if __name__ == "__main__":
    run_app()
