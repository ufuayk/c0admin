import base64
import os
from google import genai
from google.genai import types
import threading
import itertools
import sys
import time
import requests
from colorama import init, Fore, Style
import time

init()

CUSTOM_INSTRUCTION_PATH = "custom_instruction.txt"
DEFAULT_INSTRUCTION_URL = "https://raw.githubusercontent.com/ufuayk/c0admin-system-instructions/refs/heads/main/instructions/default.txt"

def ensure_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    env_path = ".env"
    if not api_key:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
        if not api_key:
            api_key = input("Enter your GEMINI_API_KEY: ").strip()
            with open(env_path, "a") as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
    os.environ["GEMINI_API_KEY"] = api_key
    return api_key

def delete_api_key():
    env_path = ".env"
    if os.path.exists(env_path):
        os.remove(env_path)
    os.environ.pop("GEMINI_API_KEY", None)
    print("API key deleted.")

def spinner(stop_event):
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if stop_event.is_set():
            break
        sys.stdout.write('\rLoading... ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 20 + '\r')

def print_ascii():
    print(Fore.CYAN + r"""
  ▄▖   ▌   ▘  
▛▘▛▌▀▌▛▌▛▛▌▌▛▌
▙▖█▌█▌▙▌▌▌▌▌▌▌                              
    """ + Style.RESET_ALL)

def log_history(answer):
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"{answer}\n")

def fetch_instruction_text(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Warning: Failed to fetch system instruction from {url}. Using default..")
        try:
            resp = requests.get(DEFAULT_INSTRUCTION_URL, timeout=5)
            resp.raise_for_status()
            return resp.text
        except Exception as fallback_error:
            raise ValueError(f"Failed to fetch default instruction: {fallback_error} [ERROR_CODE:43]")

def generate():
    print_ascii()
    api_key = ensure_api_key()
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")
    client = genai.Client(
        api_key=api_key,
    )
    try:
        while True:
            question = input("> ")
            if question.strip() == "/del":
                delete_api_key()
                return
            elif question.strip() == "--help":
                print("""/del — Delete the GEMINI API KEY.
/setinst <url> — Set a custom system instruction from a given URL.
/resetinst — Reset system instruction to the default one.""")
                continue
            elif question.strip().startswith("/setinst "):
                custom_link = question.strip().split(" ", 1)[1]
                with open(CUSTOM_INSTRUCTION_PATH, "w") as f:
                    f.write(custom_link)
                print("Custom instruction URL saved.")
                continue
            elif question.strip() == "/resetinst":
                if os.path.exists(CUSTOM_INSTRUCTION_PATH):
                    os.remove(CUSTOM_INSTRUCTION_PATH)
                    print("Custom instruction reset to default.")
                else:
                    print("No custom instruction set.")
                continue

            if os.path.exists(CUSTOM_INSTRUCTION_PATH):
                with open(CUSTOM_INSTRUCTION_PATH, "r") as f:
                    system_instruction_url = f.read().strip()
            else:
                system_instruction_url = DEFAULT_INSTRUCTION_URL

            system_instruction_text = fetch_instruction_text(system_instruction_url)

            model = "gemini-2.0-flash-lite"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=question),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                system_instruction=[
                    types.Part.from_text(text=system_instruction_text),
                ],
            )

            stop_event = threading.Event()
            t = threading.Thread(target=spinner, args=(stop_event,))
            t.start()

            answer_text = ""
            try:
                for chunk in client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=generate_content_config,
                ):
                    stop_event.set()
                    t.join()
                    print(chunk.text, end="")
                    answer_text += chunk.text
            except Exception as e:
                if "API key not valid" in str(e):
                    print("\nAPI key not valid. Please check your GEMINI_API_KEY or type /del to reset.")
                else:
                    print("An error occurred:", str(e))
            finally:
                log_history(answer_text)
                stop_event.set()
                t.join()
    except KeyboardInterrupt:
        print("\nExiting..")

if __name__ == "__main__":
    generate()
