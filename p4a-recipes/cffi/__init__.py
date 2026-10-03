from pathlib import Path
from shutil import copytree,copy2
from zipfile import ZipFile
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory
class CffiRecipe(Recipe):
    version="2.0.0"
    url="https://pypi.flet.dev/-/ver_19qZEZ/cffi-2.0.0-1-cp312-cp312-android_24_arm64_v8a.whl"
    depends=["python3","pycparser"]
    def build_arch(self,arch):
        target=Path(self.ctx.get_python_install_dir(arch.arch))
        with current_directory(self.get_build_dir(arch.arch)):
            wheels=list(Path(".").glob("*.whl"))
            if not wheels: raise RuntimeError("Android Cffi wheel was not downloaded")
            with ZipFile(wheels[0]) as zf: zf.extractall(".")
            copytree(Path("cffi"),target/"cffi",dirs_exist_ok=True)
            for p in Path(".").glob("_cffi_backend*.so"): copy2(p,target/p.name)
            for dist in Path(".").glob("cffi-*.dist-info"): copytree(dist,target/dist.name,dirs_exist_ok=True)
recipe=CffiRecipe()
