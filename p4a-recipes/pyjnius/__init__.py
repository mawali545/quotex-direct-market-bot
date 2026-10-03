from pathlib import Path
from shutil import copytree
from zipfile import ZipFile

from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class PyjniusRecipe(Recipe):
    version = "1.7.0"
    url = "https://pypi.flet.dev/-/ver_1vxEAp/pyjnius-1.7.0-1-cp312-cp312-android_24_arm64_v8a.whl"
    # pyjnius' Android bridge is provided by the Android recipe itself;
    # declaring android here creates an android -> pyjnius -> android cycle.
    depends = ["python3"]

    def build_arch(self, arch):
        target = Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            wheels = list(Path(".").glob("*.whl"))
            if not wheels:
                raise RuntimeError("Android pyjnius wheel was not downloaded")
            with ZipFile(wheels[0]) as zf:
                zf.extractall(".")
            package = Path("jnius")
            if not package.is_dir():
                raise RuntimeError("Android pyjnius wheel did not unpack correctly")
            copytree(package, target / "jnius", dirs_exist_ok=True)
            for dist in Path(".").glob("pyjnius-*.dist-info"):
                copytree(dist, target / dist.name, dirs_exist_ok=True)


recipe = PyjniusRecipe()
