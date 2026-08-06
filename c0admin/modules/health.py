import platform
import time


class HealthModule:
    def __init__(self, ai, out, cfg, model=None):
        self.ai = ai
        self.out = out
        self.cfg = cfg
        self.model = model or cfg.get("report_model")

    def collect(self):
        try:
            import psutil
        except ImportError:
            self.out.error("psutil is not installed. Run: pip install psutil")
            return None

        data = {}
        data["hostname"] = platform.node()
        data["os"] = f"{platform.system()} {platform.release()} {platform.machine()}"
        data["python"] = platform.python_version()
        data["boot_time"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())
        )
        data["uptime_seconds"] = int(time.time() - psutil.boot_time())

        data["cpu"] = {
            "percent": psutil.cpu_percent(interval=0.3),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "load_avg": [round(x, 2) for x in psutil.getloadavg()],
        }

        vm = psutil.virtual_memory()
        data["memory"] = {
            "total": vm.total,
            "used": vm.used,
            "available": vm.available,
            "percent": vm.percent,
        }

        data["swap"] = {"total": psutil.swap_memory().total, "used": psutil.swap_memory().used, "percent": psutil.swap_memory().percent}

        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mount": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "percent": usage.percent,
                    }
                )
            except Exception:
                continue
        data["disks"] = disks

        net = psutil.net_io_counters()
        data["network"] = {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }
        return data

    def analyze(self, data):
        sys_prompt = (
            "You are an expert GNU/Linux sysadmin. Analyze the following system "
            "health metrics (JSON) and produce a SHORT, plain-text health summary.\n"
            "RULES:\n"
            "- Use ONLY plain text. NO markdown: no '**', '#', '-', '*', backticks, or lists.\n"
            "- Max 5 lines. Write in single-line sentences.\n"
            "- First line: one-sentence overall verdict (OK / warning / critical).\n"
            "- Next lines: only real problems or risks, each one short.\n"
            "- If everything is fine, just say so in 2 lines.\n"
            f"Metrics:\n{data}"
        )
        try:
            return self.ai.quick(self.model, sys_prompt, "Analyze system health.")
        except Exception as e:
            return f"AI analysis failed: {e}"

    def run(self, args=None):
        data = self.collect()
        if not data:
            return

        def render_text():
            self.out.section("System Health")
            self.out.info(f"Host    : {data['hostname']}")
            self.out.info(f"OS      : {data['os']}")
            self.out.info(f"Uptime  : {data['uptime_seconds'] // 86400}d "
                          f"{(data['uptime_seconds'] % 86400) // 3600}h "
                          f"{(data['uptime_seconds'] % 3600) // 60}m")
            self.out.info(f"CPU     : {data['cpu']['percent']}% "
                          f"(load {data['cpu']['load_avg']})")
            mb = 1024 * 1024
            self.out.info(f"Memory  : {data['memory']['used'] // mb}MB / "
                          f"{data['memory']['total'] // mb}MB "
                          f"({data['memory']['percent']}%)")
            self.out.info(f"Swap    : {data['swap']['used'] // mb}MB / "
                          f"{data['swap']['total'] // mb}MB "
                          f"({data['swap']['percent']}%)")
            rows = []
            for d in data["disks"]:
                rows.append([d["mount"], f"{d['used'] // mb}MB", f"{d['total'] // mb}MB", f"%{d['percent']}"])
            self.out.table(["Mount", "Used", "Total", "Usage"], rows)
            self.out.info(f"Net TX  : {data['network']['bytes_sent'] // mb}MB")
            self.out.info(f"Net RX  : {data['network']['bytes_recv'] // mb}MB")
            self.out.section("AI Analysis")
            print(self.analyze(data))

        self.out.emit(data, render_text)
