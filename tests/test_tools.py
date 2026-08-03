import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engineer import AISoftwareEngineer
from tools.filesystem import FileSystem
from tools.terminal import Terminal


class ToolExecutionTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix="agent-test-", dir=str(Path(__file__).resolve().parent))
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_filesystem_can_create_a_file(self):
        tool = FileSystem()
        result = tool.run({"action": "create_file", "path": "demo.txt", "content": "hello world"})

        self.assertTrue(result["success"])
        self.assertTrue(Path(self.temp_dir, "demo.txt").exists())
        self.assertEqual(Path(self.temp_dir, "demo.txt").read_text(encoding="utf-8"), "hello world")

    def test_terminal_can_run_a_simple_command(self):
        tool = Terminal()
        result = tool.run({"action": "check environment"})

        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Python", result["output"])

    def test_direct_execute_handles_execute_prompts(self):
        engineer = AISoftwareEngineer()
        results = engineer._direct_execute("execute python --version")

        self.assertTrue(results)
        self.assertEqual(results[0]["tool"], "terminal")
        self.assertEqual(results[0]["result"]["exit_code"], 0)
        self.assertIn("Python", results[0]["result"]["output"])

    def test_create_flask_app_prompt_creates_app_file(self):
        engineer = AISoftwareEngineer()
        result = engineer._handle_code_request("create a basic Flask app")

        self.assertTrue(result["success"])
        self.assertTrue(Path(os.getcwd(), "app.py").exists())
        self.assertIn("Flask", Path(os.getcwd(), "app.py").read_text(encoding="utf-8"))

    def test_create_prompt_overwrites_existing_file(self):
        engineer = AISoftwareEngineer()
        Path(os.getcwd(), "app.py").write_text("old content", encoding="utf-8")

        result = engineer._handle_code_request("create a basic Flask app")

        self.assertTrue(result["success"])
        content = Path(os.getcwd(), "app.py").read_text(encoding="utf-8")
        self.assertIn("from flask import Flask", content)
        self.assertNotIn("old content", content)

    def test_extracts_multiple_targets_from_one_request(self):
        engineer = AISoftwareEngineer()
        targets = engineer._extract_code_targets("Create modules src/foo.py and src/bar.py")

        self.assertEqual(targets, ["src/foo.py", "src/bar.py"])

    def test_patch_existing_file_preserves_imports_and_inserts_snippet(self):
        engineer = AISoftwareEngineer()
        existing = "import os\n\ndef existing():\n    return True\n"
        snippet = "from pathlib import Path\n\ndef added():\n    return Path('x').exists()\n"

        updated = engineer._apply_patch(existing, snippet)

        self.assertIn("import os", updated)
        self.assertIn("from pathlib import Path", updated)
        self.assertIn("def added()", updated)
        self.assertIn("def existing()", updated)

    def test_merge_imports_keeps_existing_imports(self):
        engineer = AISoftwareEngineer()
        existing = "import os\nimport sys\n\ndef existing():\n    return True\n"
        generated = "def new_feature():\n    return False\n"

        merged = engineer._merge_imports(existing, generated)

        self.assertIn("import os", merged)
        self.assertIn("import sys", merged)
        self.assertIn("def new_feature()", merged)

    def test_apply_unified_diff_adds_new_content(self):
        engineer = AISoftwareEngineer()
        existing = "import os\n\ndef existing():\n    return True\n"
        diff = "@@\n+from pathlib import Path\n+\n+def added():\n+    return Path('x').exists()\n"

        updated = engineer._apply_patch(existing, diff)

        self.assertIn("from pathlib import Path", updated)
        self.assertIn("def added()", updated)

    def test_execute_plan_creates_and_edits_files(self):
        engineer = AISoftwareEngineer()
        plan = {
            "goal": "Create a sample module",
            "files": [
                {"path": "demo.py", "action": "create", "content": "print('hello')\n"},
                {"path": "demo.py", "action": "edit", "patch": {"replace": "print('hello')", "with": "print('hello from patch')"}},
            ],
        }

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                result = engineer.execute_plan(plan)
            finally:
                os.chdir(original_cwd)

            self.assertTrue(result["success"])
            self.assertTrue(Path(temp_dir, "demo.py").exists())
            self.assertIn("hello from patch", Path(temp_dir, "demo.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
