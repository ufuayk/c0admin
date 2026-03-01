import base64
import os
from google import genai
from google.genai import types
import threading
import itertools
import sys
import time
import requests
import webbrowser
import pyperclip
from colorama import init, Fore, Style
import time

init()

CUSTOM_INSTRUCTION_PATH = "custom_instruction.txt"
DEFAULT_INSTRUCTION_URL = "https://raw.githubusercontent.com/ufuayk/c0admin-system-instructions/refs/heads/main/instructions/default.txt"

def validate_api_key_format(api_key):
    return api_key and len(api_key) > 10
def ensure_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    env_path = ".env"
    if not api_key:
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1]
                            break
            except Exception as e:
                print(f"Warning: Could not read {env_path}.")
        if not api_key:
            while True:
                api_key = input("Enter your GEMINI_API_KEY: ").strip()
                if validate_api_key_format(api_key):
                    break
                else:
                    print("Invalid API key format. Please try again.")
            try:
                with open(env_path, "a") as f:
                    f.write(f"GEMINI_API_KEY={api_key}\n")
                print("API key saved successfully.")
            except Exception as e:
                print(f"Warning: Could not save API key to {env_path}.")
                print("You may need to re-enter the API key next time.")
    elif not validate_api_key_format(api_key):
        print("Warning: Invalid API key format found in environment.")
    os.environ["GEMINI_API_KEY"] = api_key
    return api_key

def delete_api_key():
    env_path = ".env"
    try:
        if os.path.exists(env_path):
            os.remove(env_path)
            print("API key file deleted.")
        else:
            print("No API key file found.")
    except Exception as e:
        print(f"Error deleting API key file.")
    os.environ.pop("GEMINI_API_KEY", None)
    print("API key deleted from environment.")

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

current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 

def log_history(answer):
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"{current_time}: {answer}\n")

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
            print(f"Failed to fetch default instruction: {fallback_error}")
            raise ValueError(f"Failed to fetch default instruction: {fallback_error}.")

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
            elif question.strip() == "/":
                print("Type your question or command.")
                continue
            elif question.strip() == "/exit":
                print("Exiting...")
                return
            elif question.strip() == "/history":
                if not os.path.exists("history.txt"):
                    print("History not found.")
                    continue
                os.system("cat history.txt")
                continue
            elif question.strip() == "/help":
                print("""/del — Delete the GEMINI API KEY.
/exit — Exit the app safely.
/history — Displays the command history (history.txt).
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

            model = "gemini-3-flash-preview"
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
                    try:
                        pyperclip.copy(answer_text)
                    except pyperclip.PyperclipException:
                        pass
            except Exception as e:
                if "API key not valid" in str(e):
                    print("\nAPI key not valid. Please check your GEMINI_API_KEY or type /del to reset.")
                else:
                    print("An error occurred:", str(e))
            finally:
                log_history(answer_text)
                stop_event.set()
                t.join()
                print()
    except KeyboardInterrupt:
        print("\nExiting..")

if __name__ == "__main__":
    generate()
