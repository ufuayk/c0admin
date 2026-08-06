import requests

from c0admin.config import DEFAULT_INSTRUCTION_URL


def fetch_instruction_text(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Warning: Failed to fetch system instruction from {url}. Error: {e}")
        print("Attempting to fetch default instruction...")
        try:
            resp = requests.get(DEFAULT_INSTRUCTION_URL, timeout=10)
            resp.raise_for_status()
            print("Default system instruction fetched successfully.")
            return resp.text
        except Exception as fallback_error:
            raise ValueError(f"Failed to fetch default instruction: {fallback_error}.")
