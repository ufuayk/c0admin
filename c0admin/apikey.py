import os

from c0admin.config import ENV_PATH


def validate_api_key_format(api_key):
    return api_key is not None and len(api_key) > 10


def ensure_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        if os.path.exists(ENV_PATH):
            try:
                with open(ENV_PATH) as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1]
                            break
            except Exception as e:
                print(f"Warning: Could not read {ENV_PATH}.")
        if not api_key:
            while True:
                api_key = input("Enter your GEMINI_API_KEY: ").strip()
                if validate_api_key_format(api_key):
                    break
                print("Invalid API key format. Please try again.")
            try:
                with open(ENV_PATH, "a") as f:
                    f.write(f"GEMINI_API_KEY={api_key}\n")
                print("API key saved successfully.")
            except Exception as e:
                print(f"Warning: Could not save API key to {ENV_PATH}.")
                print("You may need to re-enter the API key next time.")
    elif not validate_api_key_format(api_key):
        print("Warning: Invalid API key format found in environment.")
    os.environ["GEMINI_API_KEY"] = api_key
    return api_key


def delete_api_key():
    try:
        if os.path.exists(ENV_PATH):
            os.remove(ENV_PATH)
            print("API key file deleted.")
        else:
            print("No API key file found.")
    except Exception as e:
        print("Error deleting API key file.")
    os.environ.pop("GEMINI_API_KEY", None)
    print("API key deleted from environment.")
