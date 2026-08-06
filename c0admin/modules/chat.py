import itertools
import os
import sys
import threading
import time

import pyperclip

from c0admin import instructions
from c0admin.config import CUSTOM_INSTRUCTION_PATH
from c0admin.history import log_history

MAX_SESSION_TURNS = 12


def spinner(stop_event):
    for c in itertools.cycle(["|", "/", "-", "\\"]):
        if stop_event.is_set():
            break
        sys.stdout.write("\rLoading... " + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 20 + "\r")


class ChatModule:
    def __init__(self, ai, out, cfg, model=None, on_suggested_command=None):
        self.ai = ai
        self.out = out
        self.cfg = cfg
        self.model = model or cfg.get("main_model")
        self.on_suggested_command = on_suggested_command
        self.session = []

    def clear_session(self):
        self.session = []
        self.out.ok("Session history cleared.")

    def _get_instruction_url(self):
        if os.path.exists(CUSTOM_INSTRUCTION_PATH):
            with open(CUSTOM_INSTRUCTION_PATH, "r") as f:
                return f.read().strip()
        return instructions.DEFAULT_INSTRUCTION_URL

    def ask(self, question):
        system_instruction = instructions.fetch_instruction_text(self._get_instruction_url())
        self.session.append({"role": "user", "text": question})
        session = self.session[-(MAX_SESSION_TURNS * 2):]

        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=(stop_event,))
        t.start()

        answer_text = ""
        try:
            for text in self.ai.stream(
                self.model, question, system_instruction, history=session[:-1]
            ):
                stop_event.set()
                t.join()
                print(text, end="")
                answer_text += text
                try:
                    pyperclip.copy(answer_text)
                except pyperclip.PyperclipException:
                    pass
        except Exception as e:
            stop_event.set()
            t.join()
            self.out.error_box("AI request failed", e)
            self.out.warn("You can retry with the same question, or type /debug for details.")
            return
        finally:
            log_history(answer_text)

        if answer_text.strip():
            self.session.append({"role": "assistant", "text": answer_text})
        print()

        if self.on_suggested_command and answer_text.strip():
            self.on_suggested_command(answer_text)
