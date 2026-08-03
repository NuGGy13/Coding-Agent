import json
import os
from pathlib import Path


class Memory:
    FILE = "memory.json"
    LOG_FILE = Path(__file__).resolve().parent / "app.logs"

    def load_project(self):
        if os.path.exists(self.FILE):
            with open(self.FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        return {}

    def save_project(self, project):
        with open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=4)

    def log(self, step, result):
        description = step.get("description", "task")
        with open(self.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{description} -> {result}\n")

        print(f"LOGGED: {description}")
        if isinstance(result, dict):
            print(result)
        else:
            print(result)
