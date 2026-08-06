import signal
import time


class ProcessModule:
    def __init__(self, ai, out, cfg, model=None):
        self.ai = ai
        self.out = out
        self.cfg = cfg
        self.model = model or cfg.get("report_model")

    def _snapshot(self, limit=15):
        try:
            import psutil
        except ImportError:
            self.out.error("psutil is not installed. Run: pip install psutil")
            return []

        procs = []
        seen = set()
        for p in psutil.process_iter(["pid", "name", "username"]):
            try:
                info = p.info
                if info["pid"] in seen:
                    continue
                seen.add(info["pid"])
                procs.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"] or "?",
                        "user": info["username"] or "?",
                        "cpu": p.cpu_percent(interval=None),
                        "mem": p.memory_percent(),
                        "rss": p.memory_info().rss,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        procs.sort(key=lambda x: x["cpu"], reverse=True)
        return procs[:limit]

    def run(self, args=None):
        sub = args[0].lower() if args else "top"
        if sub == "top":
            self._top(args[1:])
        elif sub == "list":
            self._list(args[1:])
        elif sub == "kill":
            self._kill(args[1:])
        elif sub == "analyze":
            self._analyze()
        else:
            self.out.warn("Usage: /ps top [n] | list [name] | kill <pid> | analyze")

    def _top(self, args):
        limit = int(args[0]) if args and args[0].isdigit() else 15
        procs = self._snapshot(limit)
        if not procs:
            return

        def render_text():
            self.out.section(f"Top processes (by CPU)")
            rows = []
            for p in procs:
                rows.append([p["pid"], p["name"][:30], p["user"], f"{p['cpu']:.1f}%", f"{p['mem']:.1f}%", f"{p['rss'] // (1024*1024)}MB"])
            self.out.table(["PID", "Name", "User", "CPU%", "MEM%", "RSS"], rows)

        self.out.emit({"top": procs}, render_text)

    def _list(self, args):
        name = args[0].lower() if args else ""
        procs = self._snapshot(100)
        if name:
            procs = [p for p in procs if name in p["name"].lower()]

        def render_text():
            if not procs:
                self.out.warn("No matching processes.")
                return
            self.out.section(f"Processes {('matching ' + name) if name else ''}")
            rows = []
            for p in procs:
                rows.append([p["pid"], p["name"][:30], p["user"], f"{p['cpu']:.1f}%", f"{p['mem']:.1f}%"])
            self.out.table(["PID", "Name", "User", "CPU%", "MEM%"], rows)

        self.out.emit({"processes": procs}, render_text)

    def _kill(self, args):
        if not args or not args[0].isdigit():
            self.out.warn("Usage: /ps kill <pid>")
            return
        pid = int(args[0])
        try:
            import psutil

            p = psutil.Process(pid)
            self.out.warn(f"Kill process {pid} ({p.name()})? [y/N]")
            if input().strip().lower() not in ("y", "yes"):
                self.out.warn("Cancelled.")
                return
            os_kill = psutil.Process(pid)
            os_kill.kill()
            self.out.ok(f"Process {pid} killed.")
        except psutil.NoSuchProcess:
            self.out.error(f"No process with PID {pid}.")
        except psutil.AccessDenied:
            self.out.error("Permission denied. Try with sudo.")
        except Exception as e:
            self.out.error(f"Failed to kill process: {e}")

    def _analyze(self):
        procs = self._snapshot(15)
        if not procs:
            return
        summary = [
            {"pid": p["pid"], "name": p["name"], "cpu": round(p["cpu"], 1), "mem": round(p["mem"], 1)}
            for p in procs
        ]
        sys_prompt = (
            "You are an expert GNU/Linux sysadmin. The following is a snapshot of "
            "the most CPU-intensive processes on this machine (JSON). Identify any "
            "that look abnormal, suspicious, or resource-heavy, and suggest action.\n"
            "RULES: plain text only. No markdown ('**', '#', '-', '*', backticks). "
            "Max 5 lines, short sentences.\n\n"
            f"Processes:\n{summary}"
        )
        self.out.section("AI Process Analysis")

        def render_text():
            try:
                print(self.ai.quick(self.model, sys_prompt, "Analyze these processes."))
            except Exception as e:
                self.out.error(f"AI analysis failed: {e}")

        self.out.emit({"analysis": summary}, render_text)
