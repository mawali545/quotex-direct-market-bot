from pathlib import Path
from shutil import copytree
import tarfile
import zipfile
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class PyquotexRecipe(Recipe):
    version = "1.1.1"
    url = "https://github.com/cleitonleonel/pyquotex/archive/70fca1575b9c3e8f45aaaa08a54baf67adbdac68.tar.gz"
    depends = [
        "python3",
        "websockets",
        "httpx",
        "pyfiglet",
        "beautifulsoup4",
        "fake-useragent",
        "certifi",
        "rich",
    ]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            package = None
            matches = [p for p in Path(".").rglob("pyquotex") if p.is_dir() and (p / "__init__.py").is_file()]
            if len(matches) == 1:
                package = matches[0]

            if package is None:
                for archive in list(Path(".").glob("*.tar.gz")) + list(Path(".").glob("*.tgz")):
                    with tarfile.open(archive, "r:gz") as tf:
                        tf.extractall(".")
                    matches = [p for p in Path(".").rglob("pyquotex") if p.is_dir() and (p / "__init__.py").is_file()]
                    if len(matches) == 1:
                        package = matches[0]
                        break

            if package is None:
                for archive in list(Path(".").glob("*.whl")) + list(Path(".").glob("*.zip")):
                    with zipfile.ZipFile(archive) as zf:
                        zf.extractall(".")
                    matches = [p for p in Path(".").rglob("pyquotex") if p.is_dir() and (p / "__init__.py").is_file()]
                    if len(matches) == 1:
                        package = matches[0]
                        break

            if package is None:
                raise RuntimeError("pyquotex package directory was not found after archive extraction")

            copytree(package, target / "pyquotex", dirs_exist_ok=True)

            # Quotex can return the same cookie name on multiple domains/paths.
            # httpx raises CookieConflict when dict(response.cookies) or
            # client.cookies.items() sees those duplicates. Keep the cookie
            # jar intact but serialize it without collapsing through __getitem__.
            login_py = target / "pyquotex" / "network" / "login.py"
            if login_py.is_file():
                s = login_py.read_text(encoding="utf-8")
                old = '        cookies_dict = dict(response.cookies)\n        cookies_str = \'; \'.join([f"{key}={value}" for key, value in cookies_dict.items()])'
                new = '        cookies_dict = {}\n        for cookie in response.cookies.jar:\n            cookies_dict[cookie.name] = cookie.value\n        cookies_str = "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])'
                if old not in s:
                    raise RuntimeError("Expected pyquotex login cookie code was not found")
                login_py.write_text(s.replace(old, new), encoding="utf-8")

            api_py = target / "pyquotex" / "api.py"
            if api_py.is_file():
                s = api_py.read_text(encoding="utf-8")
                old = '                cookie_str = self.session_data["cookies"]\n'
                new = '                cookie_str = self.session_data.get("cookies") or ""\n'
                if old not in s:
                    raise RuntimeError("Expected pyquotex API cookie sync code was not found")
                s = s.replace(old, new)
                old_ws = '''        extra_headers = {
            "User-Agent": ua,
            "Origin": self.https_url,
            "Referer": f"{self.https_url}/{self.lang}/trade",
            "Cookie": self.session_data.get("cookies", ""),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        }'''
                new_ws = '''        try:
            browser_cookies = self.browser.get_cookies()
        except Exception:
            browser_cookies = self.session_data.get("cookies") or ""
        try:
            browser_ua = self.browser.headers.get("User-Agent") or ua
        except Exception:
            browser_ua = ua
        extra_headers = {
            "User-Agent": browser_ua,
            "Origin": self.https_url,
            "Referer": f"{self.https_url}/{self.lang}/trade",
            "Cookie": browser_cookies,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }'''
                if old_ws not in s:
                    raise RuntimeError("Expected pyquotex websocket header block was not found in API")
                s = s.replace(old_ws, new_ws)
                api_py.write_text(s, encoding="utf-8")

            stable_api_py = target / "pyquotex" / "stable_api.py"
            if stable_api_py.is_file():
                s = stable_api_py.read_text(encoding="utf-8")
                old = '            for ac in self.subscribe_candle:\n                sp = ac.split(",")\n'
                new = '            for ac in self.subscribe_candle:\n                if not ac:\n                    continue\n                sp = ac.split(",")\n'
                if old not in s:
                    raise RuntimeError("Expected pyquotex stable_api candle resubscribe code was not found")
                stable_api_py.write_text(s.replace(old, new), encoding="utf-8")

            # Cloudflare can reject the WebSocket handshake when it does not
            # look like the browser session that performed the HTTP login.
            # Reuse the same session/cookies and send browser-like origin,
            # referer and navigation headers on the Socket.IO upgrade.
            ws_py = target / "pyquotex" / "ws" / "client.py"
            if ws_py.is_file():
                s = ws_py.read_text(encoding="utf-8")
                old = '''        headers = extra_headers or {}'''
                new = '''        headers = dict(extra_headers or {})
        host = getattr(self.api, "host", "qxbroker.com")
        headers.setdefault("Origin", f"https://{host}")
        headers.setdefault("Referer", f"https://{host}/")
        headers.setdefault("Accept", "*/*")
        headers.setdefault("Accept-Language", "en-US,en;q=0.9")
        headers.setdefault("Cache-Control", "no-cache")
        headers.setdefault("Pragma", "no-cache")
        # Keep the WebSocket handshake browser-like while preserving the
        # authenticated Cookie and User-Agent already supplied by pyquotex.'''
                if old not in s:
                    raise RuntimeError("Expected pyquotex websocket header block was not found")
                ws_py.write_text(s.replace(old, new), encoding="utf-8")

            navigator_py = target / "pyquotex" / "network" / "navigator.py"
            if navigator_py.is_file():
                s = navigator_py.read_text(encoding="utf-8")
                old = '''        return '; '.join(
            f'{name}={value}'
            for name, value in self._client.cookies.items()
        )'''
                new = '''        return '; '.join(
            f'{cookie.name}={cookie.value}'
            for cookie in self._client.cookies.jar
        )'''
                if old not in s:
                    raise RuntimeError("Expected pyquotex navigator cookie code was not found")
                navigator_py.write_text(s.replace(old, new), encoding="utf-8")


recipe = PyquotexRecipe()
