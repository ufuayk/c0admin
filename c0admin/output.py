import json
import re

from colorama import Style

from c0admin.theme import get_theme

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_width(text):
    return len(ANSI_RE.sub("", str(text)))


class Output:
    def __init__(self, cfg):
        self.cfg = cfg
        self.theme = get_theme(cfg.get("theme", "default"))

    def set_theme(self, name):
        self.theme = get_theme(name)

    def color(self, key, text=""):
        return self.theme[key] + text + self.theme["reset"]

    def section(self, text):
        print(self.color("title", f"== {text} =="))

    def info(self, text):
        print(self.color("info", text))

    def ok(self, text):
        print(self.color("ok", text))

    def warn(self, text):
        print(self.color("warn", text))

    def error(self, text):
        print(self.color("error", text))

    def _pad(self, text, width):
        pad = max(0, width - _visible_width(text))
        return str(text) + " " * pad

    def table(self, headers, rows, col_widths=None):
        if not headers:
            return
        if col_widths is None:
            col_widths = []
            for i, h in enumerate(headers):
                w = _visible_width(h)
                for r in rows:
                    if i < len(r):
                        w = max(w, _visible_width(r[i]))
                col_widths.append(w)
        header_line = "  ".join(self._pad(h, col_widths[i]) for i, h in enumerate(headers))
        print(self.color("title", header_line))
        print(self.color("dim", "-" * len(ANSI_RE.sub("", header_line))))
        for row in rows:
            line = "  ".join(self._pad(c, col_widths[i]) for i, c in enumerate(row))
            print(line)

    def emit(self, data, render_text=None):
        if self.cfg.get("json_output"):
            try:
                print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
            except Exception:
                print(json.dumps(str(data)))
        elif render_text:
            render_text()

    def prompt_line(self):
        return self.theme["prompt"] + "c0admin> " + Style.RESET_ALL

    def error_box(self, title, details):
        self.error(f"== {title} ==")
        for line in str(details).splitlines()[:6]:
            self.warn("  " + line)
        self.warn("  (run /debug to see the full traceback)")
