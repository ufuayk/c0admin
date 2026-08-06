import re
import subprocess


def extract_commands(text):
    commands = []
    for m in re.finditer(r"```(?:bash|sh)?\s*\n(.*?)\n```", text, re.DOTALL):
        for line in m.group(1).strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)
    if not commands:
        for line in text.splitlines():
            line = line.strip()
            m = re.match(r"^[$#]\s+(.*)$", line)
            if m:
                commands.append(m.group(1).strip())
    return commands


class ExecModule:
    def __init__(self, ai, out, cfg, model=None):
        self.ai = ai
        self.out = out
        self.cfg = cfg
        self.model = model or cfg.get("report_model")

    def assess_safety(self, command):
        sys_prompt = (
            "You are a security auditor for a GNU/Linux sysadmin assistant. "
            "A user wants to execute a command. Analyze ONLY this command: "
            f"{command!r}\n\n"
            "Reply in exactly this format:\n"
            "VERDICT: SAFE|CAUTION|DANGEROUS\n"
            "REASON: one-line explanation\n"
            "Do not add anything else. Do not use markdown."
        )
        try:
            text = self.ai.quick(self.model, sys_prompt, "Assess the safety of the command.")
            verdict = "CAUTION"
            reason = text
            for line in text.splitlines():
                if line.upper().startswith("VERDICT:"):
                    v = line.split(":", 1)[1].strip().upper()
                    if v in ("SAFE", "CAUTION", "DANGEROUS"):
                        verdict = v
                elif line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()
            return verdict, reason
        except Exception as e:
            return "CAUTION", f"AI safety check failed: {e}"

    def run(self, command):
        self.out.section("Safety check")
        verdict, reason = self.assess_safety(command)
        if verdict == "SAFE":
            self.out.ok(f"VERDICT: {verdict}")
        elif verdict == "DANGEROUS":
            self.out.error(f"VERDICT: {verdict}")
        else:
            self.out.warn(f"VERDICT: {verdict}")
        self.out.info(f"REASON: {reason}")

        if verdict == "DANGEROUS":
            self.out.error("Execution blocked by safety policy.")
            return

        self.out.info(f"$ {command}")
        choice = input("Run this command? [y/N] ").strip().lower()
        if choice not in ("y", "yes"):
            self.out.warn("Cancelled.")
            return

        self.out.section("Output")
        try:
            proc = subprocess.run(command, shell=True, text=True)
        except KeyboardInterrupt:
            self.out.warn("\nInterrupted.")
        except Exception as e:
            self.out.error(f"Failed to run command: {e}")
