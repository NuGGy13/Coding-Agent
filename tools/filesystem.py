from pathlib import Path


class FileSystem:
    def run(self, step):
        action = (step.get("action") or "list").lower()
        root = Path.cwd()

        if action == "create_file":
            path = step.get("path")
            content = step.get("content", "")
            if not path:
                return {"success": False, "error": "No path provided"}

            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(target), "content": content}

        if action == "write_file":
            path = step.get("path")
            content = step.get("content", "")
            if not path:
                return {"success": False, "error": "No path provided"}

            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(target), "content": content}

        if action == "append_file":
            path = step.get("path")
            content = step.get("content", "")
            if not path:
                return {"success": False, "error": "No path provided"}

            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            existing = target.read_text(encoding="utf-8") if target.exists() else ""
            target.write_text(existing + content, encoding="utf-8")
            return {"success": True, "path": str(target), "content": existing + content}

        files = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                try:
                    files.append(str(path.relative_to(root)))
                except Exception:
                    files.append(str(path))

        return {"workspace": str(root), "files": files[:200]}

