#!/usr/bin/env python3
"""
hackatime.py - Direct Hackatime & WakaTime Integration for ocita
Bypasses local CLI sqlite deadlocks by communicating directly with the Hackatime REST API.
"""

import os
import sys
import time
import json
import shutil
import base64
import configparser
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path

class HackatimeTracker:
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir or os.getcwd()).resolve()
        self.project_name = self.project_dir.name
        self.config_path = Path.home() / ".wakatime.cfg"
        self.waka_dir = Path.home() / ".wakatime"
        self.api_url = "https://hackatime.hackclub.com/api/hackatime/v1"
        self.api_key = ""
        self.cli_path = None
        self.last_heartbeats = {}  # (entity, is_write) -> timestamp
        self.rate_limit_seconds = 60  # 1 minute default for reads

        self._load_config()
        self._find_or_setup_cli()

    def _load_config(self):
        """Reads configuration from ~/.wakatime.cfg if present."""
        if self.config_path.is_file():
            try:
                cp = configparser.ConfigParser()
                cp.read(self.config_path)
                if cp.has_section("settings"):
                    self.api_url = cp.get("settings", "api_url", fallback=self.api_url)
                    self.api_key = cp.get("settings", "api_key", fallback="")
                    self.rate_limit_seconds = cp.getint("settings", "heartbeat_rate_limit_seconds", fallback=60)
            except Exception:
                pass

        # Environment variable overrides
        self.api_key = os.getenv("WAKATIME_API_KEY", os.getenv("HACKATIME_API_KEY", self.api_key))
        self.api_url = os.getenv("WAKATIME_API_URL", os.getenv("HACKATIME_API_URL", self.api_url))

    def _find_or_setup_cli(self):
        """Locates wakatime-cli binary or fallback in ~/.wakatime."""
        which_cli = shutil.which("wakatime-cli")
        if which_cli:
            self.cli_path = which_cli
            return

        if self.waka_dir.is_dir():
            candidates = [
                self.waka_dir / "wakatime-cli.exe",
                self.waka_dir / "wakatime-cli",
                self.waka_dir / "wakatime-cli-windows-amd64.exe",
                self.waka_dir / "wakatime-cli-linux-amd64",
                self.waka_dir / "wakatime-cli-darwin-arm64",
                self.waka_dir / "wakatime-cli-darwin-amd64",
            ]
            for c in candidates:
                if c.is_file() and os.access(c, os.X_OK if sys.platform != "win32" else os.F_OK):
                    self.cli_path = str(c)
                    return

    def send_heartbeat(self, entity, is_write=False, language=None, category="coding"):
        """Sends a heartbeat asynchronously to avoid blocking the user turn."""
        if not entity:
            return

        now = time.time()
        key = (str(entity), is_write)
        last_time = self.last_heartbeats.get(key, 0)
        if not is_write and (now - last_time < self.rate_limit_seconds):
            return

        self.last_heartbeats[key] = now

        # Launch in background thread
        t = threading.Thread(
            target=self._dispatch_heartbeat,
            args=(entity, is_write, language, category, now),
            daemon=True
        )
        t.start()

    def _get_git_branch(self):
        try:
            return subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_dir),
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
        except Exception:
            return ""

    def _detect_language(self, entity):
        ext_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".tsx": "TypeScript", ".jsx": "JavaScript", ".md": "Markdown",
            ".json": "JSON", ".html": "HTML", ".css": "CSS", ".sh": "Bash",
            ".ps1": "PowerShell", ".rs": "Rust", ".go": "Go", ".c": "C", ".cpp": "C++"
        }
        ext = Path(entity).suffix.lower()
        return ext_map.get(ext, "Text")

    def _dispatch_heartbeat(self, entity, is_write, language, category, timestamp):
        branch = self._get_git_branch()
        full_path = str(Path(entity).resolve()) if os.path.exists(entity) else str(entity)
        lang = language or self._detect_language(full_path)

        # Primary Method: Direct HTTPS REST API to Hackatime
        if self.api_key and self.api_url:
            success = self._send_direct_api_heartbeat(full_path, is_write, lang, category, branch, timestamp)
            if success:
                return

        # Secondary Method: Use wakatime-cli as backup if API key was missing or direct call failed
        if self.cli_path:
            cmd = [
                self.cli_path,
                "--entity", full_path,
                "--project", self.project_name,
                "--plugin", "ocita/1.2.0 ocita-wakatime/1.2.0"
            ]
            if is_write:
                cmd.append("--write")
            if lang:
                cmd.extend(["--language", lang])
            if branch:
                cmd.extend(["--alternate-branch", branch])

            try:
                subprocess.run(
                    cmd,
                    cwd=str(self.project_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
            except Exception:
                pass

    def _send_direct_api_heartbeat(self, entity, is_write, language, category, branch, timestamp):
        """Sends heartbeats directly to Hackatime REST API."""
        url = f"{self.api_url.rstrip('/')}/users/current/heartbeats"
        auth_header = "Basic " + base64.b64encode(self.api_key.encode("utf-8")).decode("utf-8")

        payload = {
            "entity": entity,
            "type": "file" if os.path.exists(entity) else "app",
            "time": timestamp,
            "project": self.project_name,
            "branch": branch or "main",
            "language": language or "Text",
            "is_write": bool(is_write),
            "category": category or "coding",
            "user_agent": "wakatime/1.0.0 (ocita-cli 1.2.0)"
        }

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "wakatime/1.0.0 (ocita-cli 1.2.0)"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status in (200, 201, 202)
        except Exception:
            return False

    def get_today_stats(self):
        """Directly queries Hackatime REST API for verified today count."""
        if self.api_key and self.api_url:
            url = f"{self.api_url.rstrip('/')}/users/current/statusbar/today"
            auth_header = "Basic " + base64.b64encode(self.api_key.encode("utf-8")).decode("utf-8")
            headers = {
                "Authorization": auth_header,
                "User-Agent": "ocita-cli/1.2.0"
            }
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("data", {}).get("grand_total", {}).get("text")
                    if text:
                        return text
            except Exception:
                pass

        # Fallback to wakatime-cli if direct API fails
        if self.cli_path:
            try:
                res = subprocess.run(
                    [self.cli_path, "--today"],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass

        return "Active (tracking heartbeats to Hackatime)"

    def check_connection(self):
        """Checks if Hackatime / WakaTime is configured and accessible."""
        status = {
            "configured": bool(self.api_key),
            "api_url": self.api_url,
            "user_name": None,
            "cli_installed": bool(self.cli_path),
            "cli_path": self.cli_path,
            "config_file": str(self.config_path) if self.config_path.exists() else None
        }

        if self.api_key and self.api_url:
            url = f"{self.api_url.rstrip('/')}/users/current"
            auth_header = "Basic " + base64.b64encode(self.api_key.encode("utf-8")).decode("utf-8")
            headers = {"Authorization": auth_header, "User-Agent": "ocita-cli/1.2.0"}
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    u = data.get("data", {})
                    status["user_name"] = u.get("display_name") or u.get("full_name") or u.get("username")
            except Exception:
                pass

        return status
