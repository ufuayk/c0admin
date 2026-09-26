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

# Current Gemini model options (September 2026).
# Order matters: it is the preferred fallback chain in AIClient.
MODEL_OPTIONS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
]

DEPRECATED_MODELS = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-preview-05-2025",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-3.1-flash-lite-preview",
}

DEFAULTS = {
    "theme": "default",
    "json_output": False,
    "main_model": "gemini-3.8-flash",
    "report_model": "gemini-3.5-flash-lite",
    "thinking": "medium",
    "config_version": 4,
    "model_fallbacks": list(MODEL_OPTIONS),
}


def _migrate(data):
    if not isinstance(data, dict):
        return {}
    old_version = data.get("config_version", 0)
    for key in ("main_model", "report_model"):
        if data.get(key) in DEPRECATED_MODELS:
            data[key] = DEFAULTS[key]
    if "model_fallbacks" in data and not isinstance(data["model_fallbacks"], list):
        data.pop("model_fallbacks", None)
    # gemini-3.8-flash / gemini-3.7-flash reject a "minimal" thinking level,
    # so upgrade stale "minimal" configs to the new default "medium".
    if old_version < 4 and data.get("thinking") == "minimal":
        data["thinking"] = "medium"
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
