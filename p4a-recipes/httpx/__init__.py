from pathlib import Path
from shutil import copytree
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class HttpxRecipe(Recipe):
    version = "0.27.2"
    url = "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.27.2.tar.gz"
    sha256sum = "f7c2be1d2f3c3c3160d441802406b206c2b76f5947b11115e6df10c6c65e66c2"
    depends = ["python3", "anyio", "certifi", "httpcore", "idna", "sniffio"]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            package = Path("httpx-0.27.2") / "httpx"
            if not package.is_dir():
                matches = list(Path(".").glob("*/httpx"))
                if len(matches) == 1:
                    package = matches[0]
            if not package.is_dir():
                raise RuntimeError("httpx source did not extract as expected")
            copytree(package, target / "httpx", dirs_exist_ok=True)


recipe = HttpxRecipe()
