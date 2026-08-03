import os
import subprocess


class Terminal:
    def run(self, step):
        command = step.get("action") or step.get("command") or step.get("description")

        if not command:
            return "No command provided."

        safe_commands = {
            "execute": "echo No executable command provided",
            "run": "echo No executable command provided",
            "check environment": "python --version",
            "verify environment": "python --version",
            "check dependencies": "python -m pip --version",
            "install dependencies": "python -m pip --version",
        }

        resolved_command = safe_commands.get(command.lower(), command)

        try:
            result = subprocess.run(
                resolved_command,
                shell=True,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (result.stdout or result.stderr).strip() or "Command completed without output."
            return {
                "command": resolved_command,
                "exit_code": result.returncode,
                "output": output,
            }
        except Exception as exc:
            return {"command": resolved_command, "error": str(exc)}
