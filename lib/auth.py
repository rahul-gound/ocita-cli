#!/usr/bin/env python3
"""
auth.py - Authentication and Credential Management for ocita
Supports:
  1. Direct Anthropic API Key (ANTHROPIC_API_KEY)
  2. Claude.ai Web Session Login (sessionKey cookie / OAuth token)
  3. Multi-provider API keys (OpenRouter, OpenAI, DeepSeek, Gemini, Groq)
  4. Persistent credential storage in ~/.config/ocita/auth.json
"""

import os
import sys
import json
import stat
from pathlib import Path

class AuthManager:
    def __init__(self):
        self.config_dir = Path(os.getenv("OCITA_CONFIG_DIR", Path.home() / ".config/ocita"))
        self.auth_file = self.config_dir / "auth.json"
        self.claude_credentials_file = Path.home() / ".claude/.credentials.json"
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        """Loads stored credentials, creating directory if needed."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        creds = {}

        if self.auth_file.is_file():
            try:
                with open(self.auth_file, "r", encoding="utf-8") as f:
                    creds = json.load(f)
            except Exception:
                creds = {}

        # Fallback inspection of ~/.claude/.credentials.json if present
        if "anthropic" not in creds and self.claude_credentials_file.is_file():
            try:
                with open(self.claude_credentials_file, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    if "sessionKey" in c_data:
                        creds["claude_session_key"] = c_data["sessionKey"]
                    if "apiKey" in c_data:
                        creds["anthropic"] = c_data["apiKey"]
            except Exception:
                pass

        return creds

    def save_credentials(self):
        """Saves credentials securely with restricted permissions."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.auth_file, "w", encoding="utf-8") as f:
                json.dump(self.credentials, f, indent=2)
            # Restrict permissions on Unix
            if sys.platform != "win32":
                os.chmod(self.auth_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            print(f"Warning: Failed to save credentials: {e}")

    def get_key(self, provider):
        """Resolves API key or token from environment, then stored auth.json."""
        provider = provider.lower()

        # Check standard environment variables
        env_map = {
            "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
            "claude": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "CLAUDE_SESSION_KEY"],
            "claude_session": ["CLAUDE_SESSION_KEY", "CLAUDE_SESSION_TOKEN", "CLAUDE_COOKIE"],
            "openrouter": ["OPENROUTER_API_KEY"],
            "openai": ["OPENAI_API_KEY", "CHATGPT_API_KEY"],
            "chatgpt": ["CHATGPT_API_KEY", "OPENAI_API_KEY"],
            "deepseek": ["DEEPSEEK_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_COOKIE", "GEMINI_COOKIES", "SECURE_1PSID", "__Secure-1PSID", "GOOGLE_OAUTH_TOKEN"],
            "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_COOKIE", "GEMINI_COOKIES", "SECURE_1PSID", "__Secure-1PSID", "GOOGLE_OAUTH_TOKEN"],
            "gemini_cookie": ["GEMINI_COOKIE", "GEMINI_COOKIES", "SECURE_1PSID", "__Secure-1PSID"],
            "mistral": ["MISTRAL_API_KEY"],
            "perplexity": ["PERPLEXITY_API_KEY"],
            "together": ["TOGETHER_API_KEY"],
            "groq": ["GROQ_API_KEY"]
        }

        for var in env_map.get(provider, [f"{provider.upper()}_API_KEY"]):
            val = os.getenv(var)
            if val:
                return val

        # Check persistent credentials
        if provider == "anthropic" or provider == "claude":
            return self.credentials.get("anthropic") or self.credentials.get("claude_session_key", "")
        elif provider in ("gemini", "google"):
            return (
                self.credentials.get("gemini")
                or self.credentials.get("gemini_cookies")
                or self.credentials.get("gemini_oauth_token")
                or self.credentials.get("google", "")
            )
        elif provider in ("gemini_cookie", "gemini-cookie", "cookie"):
            return self.credentials.get("gemini_cookies", "")
        return self.credentials.get(provider, "")

    def get_claude_auth_type(self):
        """Determines whether Anthropic/Claude is authenticated via API key or Claude.ai session."""
        key = self.get_key("anthropic")
        if not key:
            key = self.get_key("claude_session")

        if not key:
            return None, ""
        if key.startswith("sk-ant-sid"):
            return "claude_ai_session", key
        elif key.startswith("sk-ant-api"):
            return "anthropic_api_key", key
        else:
            return "generic_token", key

    def get_gemini_auth_type(self):
        """
        Determines whether Google Gemini is authenticated via:
          1. 'gemini_web_cookie': Web session cookies (__Secure-1PSID, __Secure-1PSIDTS)
          2. 'google_oauth_token': Google Account OAuth Access token (ya29... with cloud/account credits)
          3. 'gemini_api_key': Google AI Studio API key (AIzaSy...)
        """
        # 1. Check explicit web cookie environment variables
        cookie_env = (
            os.getenv("GEMINI_COOKIE")
            or os.getenv("GEMINI_COOKIES")
            or os.getenv("SECURE_1PSID")
            or os.getenv("__Secure-1PSID")
        )
        if cookie_env:
            return "gemini_web_cookie", cookie_env

        # 2. Check OAuth / Account Credit token
        oauth_env = os.getenv("GOOGLE_OAUTH_TOKEN") or os.getenv("GEMINI_OAUTH_TOKEN")
        if oauth_env:
            return "google_oauth_token", oauth_env

        # 3. Check persistent credentials
        auth_type_saved = self.credentials.get("gemini_auth_type")
        if auth_type_saved == "gemini_web_cookie" and self.credentials.get("gemini_cookies"):
            return "gemini_web_cookie", self.credentials.get("gemini_cookies")
        elif auth_type_saved == "google_oauth_token" and self.credentials.get("gemini_oauth_token"):
            return "google_oauth_token", self.credentials.get("gemini_oauth_token")
        elif auth_type_saved == "gemini_api_key" and self.credentials.get("gemini"):
            return "gemini_api_key", self.credentials.get("gemini")

        if self.credentials.get("gemini_cookies"):
            return "gemini_web_cookie", self.credentials.get("gemini_cookies")
        if self.credentials.get("gemini_oauth_token"):
            return "google_oauth_token", self.credentials.get("gemini_oauth_token")

        # 4. Check standard key (env or stored)
        key = self.get_key("gemini")
        if not key:
            return None, ""

        if key.startswith("ya29."):
            return "google_oauth_token", key
        elif "1PSID" in key or ";" in key or "=" in key:
            return "gemini_web_cookie", key
        elif key.startswith("AIza"):
            return "gemini_api_key", key
        else:
            return "gemini_api_key", key

    def set_key(self, provider, key):
        """Stores a credential for a provider."""
        provider = provider.lower()
        if provider in ("claude", "claude.ai", "claude_ai"):
            if key.startswith("sk-ant-sid"):
                self.credentials["claude_session_key"] = key
            else:
                self.credentials["anthropic"] = key
        elif provider in ("chatgpt", "openai"):
            self.credentials["chatgpt"] = key
            self.credentials["openai"] = key
        elif provider in ("gemini", "google", "gemini-cookie", "gemini_cookie", "cookie"):
            # Clear previous Gemini credential variants
            self.credentials.pop("gemini_cookies", None)
            self.credentials.pop("gemini_oauth_token", None)
            self.credentials.pop("gemini", None)
            self.credentials.pop("google", None)
            self.credentials.pop("gemini_auth_type", None)

            if key.startswith("ya29."):
                self.credentials["gemini_oauth_token"] = key
                self.credentials["gemini_auth_type"] = "google_oauth_token"
            elif "1PSID" in key or ";" in key or "=" in key or provider in ("gemini-cookie", "gemini_cookie", "cookie"):
                self.credentials["gemini_cookies"] = key
                self.credentials["gemini_auth_type"] = "gemini_web_cookie"
            else:
                self.credentials["gemini"] = key
                self.credentials["google"] = key
                self.credentials["gemini_auth_type"] = "gemini_api_key"
        else:
            self.credentials[provider] = key
        self.save_credentials()

    def validate_key(self, provider, key):
        """Attempts a quick metadata call or format inspection to verify if the key is valid."""
        import urllib.request
        p = provider.lower()

        # Special handling for Gemini cookies & Google OAuth tokens
        if p in ("gemini", "google", "gemini-cookie", "gemini_cookie", "cookie"):
            if key.startswith("ya29."):
                try:
                    tok_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={key}"
                    tok_req = urllib.request.Request(tok_url, headers={"User-Agent": "ocita/1.2.0"})
                    with urllib.request.urlopen(tok_req, timeout=6) as resp:
                        if resp.status == 200:
                            return True, "Google Account token verified (account credits active)."
                except Exception:
                    return True, "Google Account OAuth token saved."
            elif "1PSID" in key or ";" in key or "=" in key or p in ("gemini-cookie", "gemini_cookie", "cookie"):
                if len(key) >= 12:
                    return True, "Gemini web session cookies formatted and saved successfully."
                return False, "Gemini cookie appears too short (expected __Secure-1PSID cookie)."

        endpoints = {
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/models",
            "google": "https://generativelanguage.googleapis.com/v1beta/openai/models",
            "openai": "https://api.openai.com/v1/models",
            "chatgpt": "https://api.openai.com/v1/models",
            "openrouter": "https://openrouter.ai/api/v1/models",
            "mistral": "https://api.mistral.ai/v1/models",
            "together": "https://api.together.xyz/v1/models"
        }
        url = endpoints.get(p)
        if not url:
            return True, "Key saved."

        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": "ocita/1.2.0"})
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    return True, "Verified with server (HTTP 200 OK)."
                return True, f"Server responded with status {resp.status}."
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Authentication failed: Invalid API key (HTTP 401 Unauthorized)."
            elif e.code == 403:
                return False, "Access denied: Key lacks required permissions (HTTP 403 Forbidden)."
            return True, f"Key saved (server HTTP {e.code})."
        except Exception as e:
            return True, f"Key saved."

    def remove_key(self, provider):
        provider = provider.lower()
        if provider in ("claude", "claude.ai", "claude_ai"):
            self.credentials.pop("claude_session_key", None)
            self.credentials.pop("anthropic", None)
        elif provider in ("gemini", "google", "gemini-cookie", "gemini_cookie", "cookie"):
            self.credentials.pop("gemini", None)
            self.credentials.pop("google", None)
            self.credentials.pop("gemini_cookies", None)
            self.credentials.pop("gemini_oauth_token", None)
            self.credentials.pop("gemini_auth_type", None)
        else:
            self.credentials.pop(provider, None)
        self.save_credentials()

    def list_status(self):
        """Returns non-sensitive status of configured auth."""
        providers = ["openrouter", "anthropic", "chatgpt", "gemini", "deepseek", "groq", "ollama"]
        status = {}
        for p in providers:
            if p == "ollama":
                status[p] = {"authenticated": True, "type": "local (no auth required)"}
            elif p == "anthropic":
                atype, key = self.get_claude_auth_type()
                if atype:
                    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                    status[p] = {"authenticated": True, "type": atype, "preview": masked}
                else:
                    status[p] = {"authenticated": False, "type": None}
            elif p in ("gemini", "google"):
                atype, key = self.get_gemini_auth_type()
                if atype:
                    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                    status[p] = {"authenticated": True, "type": atype, "preview": masked}
                else:
                    status[p] = {"authenticated": False, "type": None}
            else:
                k = self.get_key(p)
                if k:
                    masked = k[:6] + "..." + k[-4:] if len(k) > 10 else "***"
                    status[p] = {"authenticated": True, "type": "api_key", "preview": masked}
                else:
                    status[p] = {"authenticated": False, "type": None}
        return status
