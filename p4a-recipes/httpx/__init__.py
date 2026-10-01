from pathlib import Path
from shutil import copytree, copy2
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class HttpxRecipe(Recipe):
    version = "0.27.2"
    url = "https://files.pythonhosted.org/packages/56/95/9377bcb415797e44274b51d46e3249eba641711cf3348050f76ee7b15ffc/httpx-0.27.2-py3-none-any.whl"
    sha256sum = "7bb2708e112d8fdd7829cd4243970f0c223274051cb35ee80c03301ee29a3df0"
    depends = ["python3", "anyio", "certifi", "httpcore", "idna", "sniffio"]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            package = Path("httpx")
            dist = next(Path(".").glob("httpx-*.dist-info"), None)
            if not package.is_dir() or dist is None:
                raise RuntimeError("httpx wheel did not extract as expected")
            copytree(package, target / "httpx", dirs_exist_ok=True)
            copytree(dist, target / dist.name, dirs_exist_ok=True)


recipe = HttpxRecipe()
