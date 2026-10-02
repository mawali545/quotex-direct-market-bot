from pathlib import Path
from shutil import copytree
import tarfile
import zipfile
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class PyquotexRecipe(Recipe):
    version = "1.1.0"
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


recipe = PyquotexRecipe()
