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
