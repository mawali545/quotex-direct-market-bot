from pythonforandroid.recipes.python3 import Python3Recipe as BasePython3Recipe

class Python3Recipe(BasePython3Recipe):
    version = "3.12.10"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    patches = []
    configure_args = BasePython3Recipe.configure_args + (
        "--with-build-python={python_host_bin}",
        "ac_cv_header_grp_h=no",
        "ac_cv_func_getgrent=no",
        "ac_cv_func_setgrent=no",
        "ac_cv_func_endgrent=no",
    )

    def apply_patches(self, arch, build_dir=None):
        # Keep the clean CPython 3.12.10 source tree; the upstream p4a
        # patch set is version-specific and is not present in this local recipe.
        self.patches = []

recipe = Python3Recipe()
