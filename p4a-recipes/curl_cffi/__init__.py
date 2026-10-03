from pathlib import Path
from shutil import copytree
from zipfile import ZipFile

from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class CurlCffiRecipe(Recipe):
    version = "0.16.2"
    url = "https://pypi.flet.dev/-/ver_1V9muK/curl_cffi-0.16.2-1-cp312-cp312-android_24_arm64_v8a.whl"
    depends = ["python3", "cffi", "certifi"]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            wheels = list(Path(".").glob("*.whl"))
            if not wheels:
                raise RuntimeError("Android curl_cffi wheel was not downloaded")
            with ZipFile(wheels[0]) as zf:
                zf.extractall(".")
            package = Path("curl_cffi")
            if not package.is_dir():
                raise RuntimeError("Android curl_cffi wheel did not unpack correctly")
            copytree(package, target / "curl_cffi", dirs_exist_ok=True)
            for dist in Path(".").glob("curl_cffi-*.dist-info"):
                copytree(dist, target / dist.name, dirs_exist_ok=True)


recipe = CurlCffiRecipe()
