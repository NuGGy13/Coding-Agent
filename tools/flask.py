import glob
import os
import re


class FlaskTool:
    def run(self, step):
        python_files = sorted(glob.glob("**/*.py", recursive=True))
        routes = []

        for file_path in python_files:
            if os.path.isdir(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    content = handle.read()
            except Exception:
                continue

            for route in re.findall(r'@(?:\w+\.)?route\([\'\"]([^\'\"]+)[\'\"]', content):
                routes.append({"file": file_path, "route": route})

        return {"files_scanned": len(python_files), "routes": routes[:20]}
