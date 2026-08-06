import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")
ENV_PATH = os.path.join(PROJECT_DIR, ".env")
HISTORY_PATH = os.path.join(PROJECT_DIR, "history.txt")
CUSTOM_INSTRUCTION_PATH = os.path.join(PROJECT_DIR, "custom_instruction.txt")
INPUT_HISTORY_PATH = os.path.join(PROJECT_DIR, "input_history.txt")
DEBUG_LOG_PATH = os.path.join(PROJECT_DIR, "debug.log")

DEFAULT_INSTRUCTION_URL = (
    "https://raw.githubusercontent.com/ufuayk/c0admin-system-instructions/"
    "refs/heads/main/instructions/default.txt"
)

DEPRECATED_MODELS = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
}

DEFAULTS = {
    "theme": "default",
    "json_output": False,
    "main_model": "gemini-3.1-flash-lite",
    "report_model": "gemini-3.1-flash-lite",
    "thinking": "minimal",
    "config_version": 3,
    "model_fallbacks": [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
    ],
}


def _migrate(data):
    if not isinstance(data, dict):
        return {}
    for key in ("main_model", "report_model"):
        if data.get(key) in DEPRECATED_MODELS:
            data[key] = DEFAULTS[key]
    if "model_fallbacks" in data and not isinstance(data["model_fallbacks"], list):
        data.pop("model_fallbacks", None)
    return data


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = _migrate(data)
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
        except Exception as e:
            print(f"Warning: Could not read config file: {e}")
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")
