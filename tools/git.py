import os
import subprocess


class Git:
    def run(self, step):
        try:
            result = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=20,
            )
            output = (result.stdout or result.stderr).strip() or "No git output."
            return {"exit_code": result.returncode, "output": output}
        except Exception as exc:
            return {"error": str(exc)}
