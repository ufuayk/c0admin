import os
import readline
import sys
import traceback

from colorama import Style

from c0admin.ai import AIClient
from c0admin.apikey import ensure_api_key, delete_api_key
from c0admin.config import (
    CUSTOM_INSTRUCTION_PATH,
    DEBUG_LOG_PATH,
    INPUT_HISTORY_PATH,
    load_config,
    save_config,
)
from c0admin.history import show_history
from c0admin.output import Output
from c0admin.theme import list_themes
from c0admin.modules.chat import ChatModule
from c0admin.modules.exec import ExecModule, extract_commands
from c0admin.modules.health import HealthModule
from c0admin.modules.network import NetworkModule
from c0admin.modules.processes import ProcessModule

HELP_ROWS = [
    ("/help", "Show this help"),
    ("/exit", "Exit the app safely"),
    ("/del", "Delete the GEMINI API KEY"),
    ("/history", "Display the command history"),
    ("/clear", "Clear the current session conversation history"),
    ("/setinst <url>", "Set a custom system instruction URL"),
    ("/resetinst", "Reset system instruction to default"),
    ("/theme [name|list]", "Show/set theme"),
    ("/json [on|off]", "Toggle JSON output mode"),
    ("/debug [on|off]", "Toggle verbose debug output"),
    ("/health", "System health report (AI analyzed)"),
    ("/ps top|list|kill|analyze", "Process manager"),
    ("/net ping|trace|dns|check", "Network diagnostics"),
    ("/run <command>", "Run a command after AI safety check"),
]


def print_help(out):
    out.section("c0admin commands")
    rows = [[out.color("accent", cmd), desc] for cmd, desc in HELP_ROWS]
    out.table(["Command", "Description"], rows)
    print()
    print(out.color("dim", "Anything else is asked to the AI as a command suggestion."))


def print_banner(out):
    print(out.color("title", r"""
  ▄▖   ▌   ▘
▛▘▛▌▀▌▛▌▛▛▌▌▛▌
▙▖█▌█▌▙▌▌▌▌▌▌▌
    """))


def log_error(out, e, debug):
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            traceback.print_exc(file=f)
    except Exception:
        pass
    if debug:
        traceback.print_exc()
    else:
        out.error_box("Unexpected error", e)


def setup_readline():
    readline.set_history_length(500)
    try:
        readline.read_history_file(INPUT_HISTORY_PATH)
    except FileNotFoundError:
        pass
    except Exception:
        pass


def clear_screen():
    print("\033[2J\033[H", end="", flush=True)


def save_readline():
    try:
        readline.write_history_file(INPUT_HISTORY_PATH)
    except Exception:
        pass


def main():
    debug = "--debug" in sys.argv
    cfg = load_config()
    cfg["debug"] = debug
    out = Output(cfg)

    print_banner(out)

    api_key = ensure_api_key()
    if not api_key:
        print("Missing GEMINI_API_KEY.")
        return

    ai = AIClient(api_key, cfg)

    chat = ChatModule(ai, out, cfg, model=cfg["main_model"])
    exec_mod = ExecModule(ai, out, cfg)
    health = HealthModule(ai, out, cfg)
    procs = ProcessModule(ai, out, cfg)
    network = NetworkModule(ai, out, cfg)

    def handle_run_prompt(answer_text):
        commands = extract_commands(answer_text)
        if commands:
            choice = input(f"\nRun suggested command '{commands[0]}'? [y/N] ").strip().lower()
            if choice in ("y", "yes"):
                exec_mod.run(commands[0])

    chat.on_suggested_command = handle_run_prompt
    setup_readline()

    try:
        while True:
            try:
                question = input(out.prompt_line())
            except EOFError:
                print()
                break
            q = question.strip()
            if not q:
                continue

            if q in ("/exit", "exit"):
                print("Exiting...")
                break
            elif q == "/help":
                print_help(out)
            elif q == "/del":
                delete_api_key()
                break
            elif q == "/history":
                show_history()
            elif q == "/clear":
                clear_screen()
                chat.clear_session()
            elif q.startswith("/setinst "):
                custom_link = q.split(" ", 1)[1]
                with open(CUSTOM_INSTRUCTION_PATH, "w") as f:
                    f.write(custom_link)
                print("Custom instruction URL saved.")
            elif q == "/resetinst":
                if os.path.exists(CUSTOM_INSTRUCTION_PATH):
                    os.remove(CUSTOM_INSTRUCTION_PATH)
                    print("Custom instruction reset to default.")
                else:
                    print("No custom instruction set.")
            elif q.startswith("/theme"):
                parts = q.split()
                if len(parts) == 1:
                    out.info(f"Current theme: {cfg.get('theme')}")
                    out.info("Available: " + ", ".join(list_themes()))
                elif parts[1] == "list":
                    out.info("Available themes: " + ", ".join(list_themes()))
                elif parts[1] in list_themes():
                    cfg["theme"] = parts[1]
                    save_config(cfg)
                    out.set_theme(parts[1])
                    print("Theme set to " + parts[1])
                else:
                    out.error("Unknown theme. Available: " + ", ".join(list_themes()))
            elif q.startswith("/json"):
                parts = q.split()
                if len(parts) == 1:
                    out.info(f"JSON output: {'on' if cfg.get('json_output') else 'off'}")
                elif parts[1] in ("on", "off"):
                    cfg["json_output"] = parts[1] == "on"
                    save_config(cfg)
                    print("JSON output: " + parts[1])
                else:
                    out.warn("Usage: /json on|off")
            elif q.startswith("/debug"):
                parts = q.split()
                if len(parts) == 1:
                    out.info(f"Debug: {'on' if debug else 'off'}")
                elif parts[1] in ("on", "off"):
                    debug = parts[1] == "on"
                    cfg["debug"] = debug
                    print("Debug: " + parts[1])
                else:
                    out.warn("Usage: /debug on|off")
            elif q.startswith("/health"):
                health.run()
            elif q.startswith("/ps"):
                procs.run(q.split()[1:])
            elif q.startswith("/net"):
                network.run(q.split()[1:])
            elif q.startswith("/run "):
                exec_mod.run(q[5:].strip())
            elif q == "clear":
                clear_screen()
            else:
                chat.ask(q)
    except KeyboardInterrupt:
        print("\nExiting..")
    except Exception as e:
        log_error(out, e, debug)
    finally:
        save_readline()


if __name__ == "__main__":
    main()
