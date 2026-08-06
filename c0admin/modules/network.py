import platform
import socket
import subprocess


class NetworkModule:
    def __init__(self, ai, out, cfg, model=None):
        self.ai = ai
        self.out = out
        self.cfg = cfg
        self.model = model or cfg.get("report_model")

    def _run_cmd(self, cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except FileNotFoundError:
            return f"Command not found: {cmd[0]}"
        except Exception as e:
            return f"Error: {e}"

    def run(self, args=None):
        sub = args[0].lower() if args else "help"
        if sub == "ping":
            self._ping(args[1:])
        elif sub == "trace":
            self._trace(args[1:])
        elif sub == "dns":
            self._dns(args[1:])
        elif sub == "check":
            self._check(args[1:])
        else:
            self.out.warn("Usage: /net ping <host> | trace <host> | dns <host> | check <host> <port>")

    def _ping(self, args):
        if not args:
            self.out.warn("Usage: /net ping <host>")
            return
        host = args[0]
        count_flag = "-c" if platform.system() != "Windows" else "-n"
        output = self._run_cmd(["ping", count_flag, "4", host])

        def render_text():
            self.out.section(f"Ping {host}")
            print(output)

        self.out.emit({"action": "ping", "host": host, "output": output}, render_text)

    def _trace(self, args):
        if not args:
            self.out.warn("Usage: /net trace <host>")
            return
        host = args[0]
        output = self._run_cmd(["traceroute", host])

        def render_text():
            self.out.section(f"Traceroute {host}")
            print(output)

        self.out.emit({"action": "traceroute", "host": host, "output": output}, render_text)

    def _dns(self, args):
        if not args:
            self.out.warn("Usage: /net dns <host>")
            return
        host = args[0]
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            ip = "NXDOMAIN"
        nslookup = self._run_cmd(["nslookup", host])

        def render_text():
            self.out.section(f"DNS lookup {host}")
            self.out.info(f"Resolved: {ip}")
            print(nslookup)

        self.out.emit({"action": "dns", "host": host, "ip": ip, "nslookup": nslookup}, render_text)

    def _check(self, args):
        if len(args) < 2:
            self.out.warn("Usage: /net check <host> <port>")
            return
        host = args[0]
        port = args[1]
        result = {}
        try:
            s = socket.create_connection((host, int(port)), timeout=5)
            s.close()
            result["open"] = True
        except Exception:
            result["open"] = False

        def render_text():
            self.out.section(f"Port check {host}:{port}")
            if result["open"]:
                self.out.ok(f"Port {port} is OPEN.")
            else:
                self.out.warn(f"Port {port} is closed/filtered.")

        self.out.emit({"action": "portcheck", "host": host, "port": int(port), **result}, render_text)
