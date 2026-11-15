#!/usr/bin/env python3
"""
Unit tests for ocita tools, Hackatime tracker, AuthManager, and core engine.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from ocita_core import ToolExecutor, render_markdown, TOOLS_SCHEMA
from auth import AuthManager
from hackatime import HackatimeTracker
from prompts import build_enterprise_system_prompt

class TestOcitaCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.tracker = HackatimeTracker(project_dir=self.temp_dir.name)
        self.executor = ToolExecutor(auto_approve=True, tracker=self.tracker)

    def tearDown(self):
        os.chdir(self.old_cwd)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_write_and_view_file(self):
        content = "Line 1: Hello\nLine 2: World\nLine 3: Test"
        write_res = self.executor.execute("write_file", {"path": "test.txt", "content": content})
        self.assertIn("written successfully", write_res)

        view_res = self.executor.execute("view_file", {"path": "test.txt"})
        self.assertIn("Line 1: Hello", view_res)
        self.assertIn("Line 3: Test", view_res)

        range_res = self.executor.execute("view_file", {"path": "test.txt", "start_line": 2, "end_line": 2})
        self.assertNotIn("Line 1", range_res)
        self.assertIn("Line 2: World", range_res)
        self.assertNotIn("Line 3", range_res)

    def test_edit_file(self):
        self.executor.execute("write_file", {"path": "code.py", "content": "def greet():\n    return 'hello'\n"})
        
        edit_res = self.executor.execute("edit_file", {
            "path": "code.py",
            "old_string": "return 'hello'",
            "new_string": "return 'world'"
        })
        self.assertIn("Successfully updated", edit_res)

        content = Path("code.py").read_text()
        self.assertEqual(content, "def greet():\n    return 'world'\n")

    def test_edit_file_not_found(self):
        self.executor.execute("write_file", {"path": "file.txt", "content": "foo bar"})
        res = self.executor.execute("edit_file", {
            "path": "file.txt",
            "old_string": "non_existent_text",
            "new_string": "replacement"
        })
        self.assertIn("Error: old_string not found", res)

    def test_bash_execution(self):
        res = self.executor.execute("bash", {"command": "echo 'ocita-test-bash'"})
        self.assertIn("Exit code: 0", res)
        self.assertIn("ocita-test-bash", res)

    def test_search_files_glob(self):
        self.executor.execute("write_file", {"path": "src/app.py", "content": "# app"})
        self.executor.execute("write_file", {"path": "src/utils.py", "content": "# utils"})
        self.executor.execute("write_file", {"path": "README.md", "content": "# readme"})

        res = self.executor.execute("search_files", {"pattern": "*.py", "path": "src"})
        self.assertIn("app.py", res)
        self.assertIn("utils.py", res)
        self.assertNotIn("README.md", res)

    def test_search_text_grep(self):
        self.executor.execute("write_file", {"path": "sample.js", "content": "const SECRET_KEY = 'supersecret';"})
        res = self.executor.execute("search_text", {"query": "SECRET_KEY"})
        self.assertIn("SECRET_KEY", res)
        self.assertIn("sample.js", res)

    def test_code_outline(self):
        code = "class AuthService:\n    def login(self, user):\n        pass\n"
        self.executor.execute("write_file", {"path": "service.py", "content": code})
        res = self.executor.execute("code_outline", {"path": "service.py"})
        self.assertIn("AuthService", res)
        self.assertIn("login", res)

    def test_wakatime_tracker(self):
        conn = self.tracker.check_connection()
        self.assertIn("configured", conn)
        self.assertIn("api_url", conn)
        # Should not raise exception
        self.tracker.send_heartbeat("test.py", is_write=True)

    def test_auth_manager(self):
        auth = AuthManager()
        # Test setting and removing temporary test key
        auth.set_key("test_provider", "secret_123")
        self.assertEqual(auth.get_key("test_provider"), "secret_123")
        auth.remove_key("test_provider")
        self.assertEqual(auth.get_key("test_provider"), "")

    def test_enterprise_prompt_builder(self):
        prompt = build_enterprise_system_prompt(
            workspace_dir="/tmp/repo",
            instructions_text="Follow PEP8.",
            instructions_file="OCITA.md",
            git_info="On branch main",
            dir_listing="main.py",
            shell_name="PowerShell"
        )
        self.assertIn("ENTERPRISE ENGINEERING PRINCIPLES", prompt)
        self.assertIn("Clean Architecture", prompt)
        self.assertIn("OWASP TOP 10", prompt)
        self.assertIn("MANDATORY CODE COMMENTING", prompt)
        self.assertIn("DELIBERATE PACING", prompt)

    def test_gemini_and_chatgpt_providers(self):
        auth = AuthManager()
        # Verify provider keys mapping
        auth.set_key("gemini", "gemini_secret_key")
        auth.set_key("chatgpt", "chatgpt_secret_key")
        self.assertEqual(auth.get_key("gemini"), "gemini_secret_key")
        self.assertEqual(auth.get_key("chatgpt"), "chatgpt_secret_key")
        auth.remove_key("gemini")
        auth.remove_key("chatgpt")

    def test_slash_commands_and_argon(self):
        from ocita_core import AgentSession, handle_slash_command
        session = AgentSession(provider="anthropic", model="claude-3-7-sonnet")
        
        # Test /argon
        handle_slash_command("/argon", session)
        self.assertEqual(session.provider, "gemini")
        self.assertEqual(session.model, "gemini-4-argon")

        # Test /claude
        handle_slash_command("/claude", session)
        self.assertEqual(session.provider, "anthropic")
        self.assertEqual(session.model, "claude-3-7-sonnet")

        # Test /slow
        handle_slash_command("/slow off", session)
        self.assertFalse(session.slow_mode)
        handle_slash_command("/slow on", session)
        self.assertTrue(session.slow_mode)

        # Test /models
        res = handle_slash_command("/models", session)
        self.assertTrue(res)

    def test_tools_schema_count(self):
        tool_names = [t["name"] for t in TOOLS_SCHEMA]
        self.assertIn("bash", tool_names)
        self.assertIn("view_file", tool_names)
        self.assertIn("edit_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("git_commit", tool_names)
        self.assertIn("run_tests", tool_names)
        self.assertIn("code_outline", tool_names)
        self.assertIn("wakatime_heartbeat", tool_names)

if __name__ == "__main__":
    unittest.main()
