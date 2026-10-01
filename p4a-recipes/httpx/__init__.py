from pathlib import Path
from shutil import copytree
import tarfile
import zipfile
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class HttpxRecipe(Recipe):
    version = "0.27.2"
    url = "https://files.pythonhosted.org/packages/78/82/08f8c936781f67d9e9b6e9b9eeb8a0c8b4e406136ea4c3d1f89a5db71d42e0e6/httpx-0.27.2.tar.gz"
    sha256sum = "f7c2be1d2f3c3c3160d441802406b206c2b76f5947b11115e6df10c6c65e66c2"
    depends = ["python3", "anyio", "certifi", "httpcore", "idna", "sniffio"]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            package = Path("httpx-0.27.2") / "httpx"
            if not package.is_dir():
                matches = [p for p in Path(".").rglob("httpx") if p.is_dir() and (p / "__init__.py").is_file()]
                if len(matches) == 1:
                    package = matches[0]
            if not package.is_dir():
                archives = list(Path(".").glob("*.tar.gz")) + list(Path(".").glob("*.tgz"))
                for archive in archives:
                    with tarfile.open(archive, "r:gz") as tf:
                        tf.extractall(".")
                    matches = list(Path(".").glob("*/httpx"))
                    if len(matches) == 1:
                        package = matches[0]
                        break
            if not package.is_dir():
                archives = list(Path(".").glob("*.whl")) + list(Path(".").glob("*.zip"))
                for archive in archives:
                    with zipfile.ZipFile(archive) as zf:
                        zf.extractall(".")
                    matches = list(Path(".").glob("*/httpx"))
                    if len(matches) == 1:
                        package = matches[0]
                        break
            if not package.is_dir():
                raise RuntimeError("httpx package directory was not found after archive extraction")
            copytree(package, target / "httpx", dirs_exist_ok=True)


recipe = HttpxRecipe()
