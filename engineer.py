import argparse
import json
import logging
import re
import sys
from pathlib import Path

from typing import Optional

from planner import Planner
from llm import LLM
from memory import Memory

from tools.filesystem import FileSystem
from tools.flask import FlaskTool
from tools.terminal import Terminal
from tools.git import Git
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

LOG_FILE = Path(__file__).resolve().parent / "app.logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ai_engineer")

TOOLS = {
    "filesystem": FileSystem(),
    "flask": FlaskTool(),
    "terminal": Terminal(),
    "git": Git(),
}


class AISoftwareEngineer:
    def __init__(self):
        self.memory = Memory()
        self.llm = LLM()
        self.planner = Planner(self.llm)

    def _infer_target_path(self, request: str) -> Optional[str]:
        lowered = request.lower().strip()
        root = Path.cwd()

        if re.search(r"(?:in|under|inside)\s+([a-z0-9_./\\-]+)", lowered):
            folder = re.search(r"(?:in|under|inside)\s+([a-z0-9_./\\-]+)", lowered).group(1)
            if folder and (root / folder).exists():
                base_dir = folder
            else:
                base_dir = folder
        else:
            base_dir = ""

        module_match = re.search(r"(?:create|make|generate)\s+(?:a\s+)?(?:python\s+)?module(?:\s+named)?\s+([a-z0-9_./\\-]+)", lowered)
        if module_match:
            candidate = module_match.group(1)
            if not candidate.endswith(".py"):
                candidate = f"{candidate}.py"
            return str(Path(base_dir) / candidate) if base_dir else candidate

        file_match = re.search(r"(?:create|make|write)\s+(?:a\s+)?file(?:\s+named)?\s+([a-z0-9_./\\-]+)", lowered)
        if file_match:
            return str(Path(base_dir) / file_match.group(1)) if base_dir else file_match.group(1)

        edit_match = re.search(r"(?:edit|update|modify)\s+(?:file\s+)?([a-z0-9_./\\-]+)", lowered)
        if edit_match:
            return str(Path(base_dir) / edit_match.group(1)) if base_dir else edit_match.group(1)

        if "flask" in lowered and "app" in lowered:
            default_name = "app.py"
            return str(Path(base_dir) / default_name) if base_dir else default_name

        if "app" in lowered:
            default_name = "app.py"
            return str(Path(base_dir) / default_name) if base_dir else default_name

        if "module" in lowered or "file" in lowered:
            default_name = "generated_module.py"
            return str(Path(base_dir) / default_name) if base_dir else default_name

        if re.search(r"\b(create|make|generate|write|build)\b", lowered):
            default_name = "generated_module.py"
            return str(Path(base_dir) / default_name) if base_dir else default_name

        return None

    def _generate_code_content(self, request: str, target_path: str, existing_content: Optional[str] = None) -> str:
        lowered_request = request.lower()
        if "flask" in lowered_request and "app" in lowered_request:
            return '''from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "Hello, Flask!"

if __name__ == "__main__":
    app.run(debug=True)
'''

        module_name = Path(target_path).stem.replace("-", "_")
        if existing_content:
            prompt = f"""You are an expert Python engineer. Update the existing file content to satisfy this request.

Request: {request}

Existing file content:
{existing_content}

Return ONLY the updated file content. Keep the module name and structure consistent. Do not include markdown fences."""
        else:
            prompt = f"""You are an expert Python engineer. Create a complete Python module for this request.

Request: {request}

Module name: {module_name}

Return ONLY the file content. Do not include markdown fences."""

        try:
            response = self.llm.ask(prompt)
        except Exception:
            response = ""

        if response:
            text = response.strip()
            if "```python" in text:
                text = text.split("```python", 1)[1].split("```", 1)[0].strip()
            elif "```" in text:
                text = text.split("```", 1)[1].split("```", 1)[0].strip()
            return text.strip()

        if existing_content:
            return existing_content

        return f'''"""{module_name} module."""


def main() -> None:
    """Placeholder implementation for: {request}"""
    pass


if __name__ == "__main__":
    main()
'''

    def _extract_code_targets(self, request: str):
        lowered = request.lower()
        matches = re.findall(r"([a-z0-9_./\\-]+\.py)", lowered)
        if matches:
            return [m for m in matches]

        if "module" in lowered or "file" in lowered:
            return ["generated_module.py"]

        return []

    def _parse_plan(self, request: str):
        text = request.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        if isinstance(parsed, dict) and "files" in parsed:
            return parsed
        return None

    def _merge_imports(self, existing_content: str, generated_content: str) -> str:
        if not existing_content:
            return generated_content

        existing_lines = [line for line in existing_content.splitlines() if line.strip()]
        generated_lines = [line for line in generated_content.splitlines() if line.strip()]

        existing_imports = [line for line in existing_lines if line.startswith("import ") or line.startswith("from ")]
        generated_imports = [line for line in generated_lines if line.startswith("import ") or line.startswith("from ")]

        merged_imports = []
        for line in existing_imports + generated_imports:
            if line not in merged_imports:
                merged_imports.append(line)

        non_import_lines = [line for line in generated_lines if not (line.startswith("import ") or line.startswith("from "))]

        if not non_import_lines:
            return "\n".join(merged_imports + [""]) + "\n"

        body = "\n".join(non_import_lines)
        if merged_imports:
            return "\n".join(merged_imports + [""] + [body])
        return body

    def _apply_patch(self, existing_content: str, snippet: str) -> str:
        if not existing_content:
            return snippet

        if snippet.strip() in existing_content:
            return existing_content

        if "diff" in snippet.lower():
            return self._apply_unified_diff(existing_content, snippet)

        if "def " in snippet and "def " in existing_content:
            return existing_content.rstrip() + "\n\n" + snippet.strip() + "\n"

        if "class " in snippet and "class " in existing_content:
            return existing_content.rstrip() + "\n\n" + snippet.strip() + "\n"

        return existing_content.rstrip() + "\n\n" + snippet.strip() + "\n"

    def _apply_unified_diff(self, existing_content: str, diff_text: str) -> str:
        lines = existing_content.splitlines()
        new_lines = list(lines)
        current_index = 0

        for line in diff_text.splitlines():
            if line.startswith("@@"):
                current_index = 0
                continue
            if line.startswith("+") and not line.startswith("+++"):
                new_lines.insert(len(new_lines), line[1:])
            elif line.startswith("-") and not line.startswith("---") and not line.startswith("+++ "):
                if new_lines:
                    new_lines.pop()

        if not new_lines:
            return existing_content
        return "\n".join(new_lines) + "\n"

    def _generate_patch(self, request: str, target_path: str, existing_content: Optional[str] = None) -> str:
        module_name = Path(target_path).stem.replace("-", "_")
        if existing_content:
            prompt = f"""You are an expert Python engineer. Produce a unified diff patch for the existing file to satisfy this request.

Request: {request}

Existing file content:
{existing_content}

Return ONLY a unified diff block. Do not include markdown fences."""
        else:
            prompt = f"""You are an expert Python engineer. Create a complete Python module for this request.

Request: {request}

Module name: {module_name}

Return ONLY the file content. Do not include markdown fences."""

        try:
            response = self.llm.ask(prompt)
        except Exception:
            response = ""

        if response:
            text = response.strip()
            if "```diff" in text:
                text = text.split("```diff", 1)[1].split("```", 1)[0].strip()
            elif "```" in text:
                text = text.split("```", 1)[1].split("```", 1)[0].strip()
            return text.strip()

        return ""

    def execute_plan(self, plan):
        root = Path.cwd()
        written_files = []

        for entry in plan.get("files", []):
            path = entry.get("path")
            action = entry.get("action", "create").lower()
            if not path:
                continue

            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)

            if action == "create":
                content = entry.get("content", "")
                target.write_text(content, encoding="utf-8")
                written_files.append({"path": str(target), "content": content})
                continue

            if action == "edit":
                existing_content = target.read_text(encoding="utf-8") if target.exists() else ""
                patch = entry.get("patch", {})
                replacement = patch.get("replace", "")
                new_value = patch.get("with", "")
                if replacement:
                    updated_content = existing_content.replace(replacement, new_value)
                else:
                    updated_content = existing_content
                target.write_text(updated_content, encoding="utf-8")
                written_files.append({"path": str(target), "content": updated_content})
                continue

        return {"success": True, "files": written_files}

    def _handle_code_request(self, request: str):
        lowered = request.lower().strip()
        is_code_request = any(token in lowered for token in ["create module", "create a module", "generate module", "create file", "write file", "edit file", "update file", "modify file", "make file", "create a basic", "create an app", "create a flask", "create app", "create a simple", "create a python", "create a new", "create"])
        if not is_code_request:
            return None

        targets = self._extract_code_targets(request)
        if not targets:
            target_path = self._infer_target_path(request)
            if not target_path:
                return None
            targets = [target_path]

        root = Path.cwd()
        written_files = []

        for target_path in targets:
            target = root / target_path
            target.parent.mkdir(parents=True, exist_ok=True)

            existing_content = target.read_text(encoding="utf-8") if target.exists() else None
            patch_text = self._generate_patch(request, target_path, existing_content)
            generated_content = self._generate_code_content(request, target_path, existing_content)

            if existing_content and re.search(r"\b(create|make|generate|write|build)\b", request.lower()):
                merged_content = generated_content
            else:
                merged_content = generated_content

                if existing_content:
                    if patch_text:
                        merged_content = self._apply_patch(existing_content, patch_text)
                    else:
                        merged_content = self._merge_imports(existing_content, generated_content)
                        if generated_content.strip() not in existing_content:
                            merged_content = self._apply_patch(existing_content, generated_content)

            target.write_text(merged_content, encoding="utf-8")
            written_files.append({"path": str(target), "content": merged_content})

        return {
            "success": True,
            "files": written_files,
        }

    def _direct_execute(self, request):
        lowered = request.lower().strip()

        if re.search(r"create(?: a)? file(?: named)?\s+([\w\\/.:-]+)", lowered):
            match = re.search(r"create(?: a)? file(?: named)?\s+([\w\\/.:-]+)", lowered)
            path = match.group(1)
            tool = TOOLS["filesystem"]
            return [{"tool": "filesystem", "result": tool.run({"action": "create_file", "path": path, "content": ""})}]

        if re.search(r"write (?:file )?([\w\\/.:-]+)", lowered):
            match = re.search(r"write (?:file )?([\w\\/.:-]+)", lowered)
            path = match.group(1)
            tool = TOOLS["filesystem"]
            return [{"tool": "filesystem", "result": tool.run({"action": "write_file", "path": path, "content": ""})}]

        if re.search(r"append (?:to )?(?:file )?([\w\\/.:-]+)", lowered):
            match = re.search(r"append (?:to )?(?:file )?([\w\\/.:-]+)", lowered)
            path = match.group(1)
            tool = TOOLS["filesystem"]
            return [{"tool": "filesystem", "result": tool.run({"action": "append_file", "path": path, "content": ""})}]

        if re.search(r"list files|show files|inspect files", lowered):
            tool = TOOLS["filesystem"]
            return [{"tool": "filesystem", "result": tool.run({"action": "list"})}]

        if re.search(r"git status|check git", lowered):
            tool = TOOLS["git"]
            return [{"tool": "git", "result": tool.run({"action": "status"})}]

        terminal_match = re.search(r"^(?:execute|run|do)\s+(.+)$", lowered)
        if terminal_match:
            command = terminal_match.group(1).strip()
            tool = TOOLS["terminal"]
            return [{"tool": "terminal", "result": tool.run({"action": command})}]

        return []

    def execute(self, request):
        logger.info("User request: %s", request)

        parsed_plan = self._parse_plan(request)
        if parsed_plan:
            result = self.execute_plan(parsed_plan)
            self.memory.log({"description": request}, result)
            logger.info("Executed JSON plan: %s", result)
            return [{"tool": "filesystem", "result": result}]

        direct_results = self._direct_execute(request)
        if direct_results:
            results = []
            for item in direct_results:
                self.memory.log({"description": request}, item["result"])
                results.append(item)
                logger.info("Direct execution result: %s", item["result"])
            return results

        code_result = self._handle_code_request(request)
        if code_result:
            self.memory.log({"description": request}, code_result)
            logger.info("Code edit result: %s", code_result)
            return [{"tool": "filesystem", "result": code_result}]

        project = self.memory.load_project()
        plan = self.planner.create_plan(request, project)

        logger.info("Goal: %s", plan.get("goal", "No goal"))

        results = []

        for step in plan.get("tasks", []):
            description = step.get("description", "No description")
            tool_name = step.get("tool", "unknown")

            logger.info("Executing task: %s", description)

            tool = TOOLS.get(tool_name)
            if tool:
                try:
                    result = tool.run(step)
                    self.memory.log(step, result)
                    results.append({"tool": tool_name, "result": result})
                    logger.info("Tool %s completed: %s", tool_name, result)
                except Exception as exc:
                    logger.exception("Tool %s failed: %s", tool_name, exc)
            else:
                logger.warning("Unknown tool: %s", tool_name)

        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI software engineering assistant")
    parser.add_argument("--prompt", help="Natural-language prompt for the engineer")
    parser.add_argument("--plan", help="JSON plan with files and patch instructions")
    args = parser.parse_args()

    engineer = AISoftwareEngineer()
    logger.info("AI Software Engineer started")

    if args.plan:
        try:
            plan = json.loads(args.plan)
            result = engineer.execute_plan(plan)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON plan: {exc}")
    elif args.prompt:
        results = engineer.execute(args.prompt)
        print(json.dumps(results, indent=2))
    else:
        while True:
            request = input("Engineer> ")

            if request.lower() == "exit":
                logger.info("Session ended")
                break

            engineer.execute(request)
