import time
from datetime import datetime

from c0admin.config import HISTORY_PATH


def log_history(answer):
    try:
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {answer}\n")
    except Exception as e:
        print(f"Warning: Could not write history: {e}")


def show_history():
    import os

    if not os.path.exists(HISTORY_PATH):
        print("History not found.")
        return
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        print(f.read())
