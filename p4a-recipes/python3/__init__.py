from pythonforandroid.recipes.python3 import Python3Recipe as BasePython3Recipe

class Python3Recipe(BasePython3Recipe):
    version = "3.12.10"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    patches = []
    configure_args = list(BasePython3Recipe.configure_args) + [
        "--with-build-python={python_host_bin}",
        "ac_cv_func_getgrent=no",
        "ac_cv_func_setgrent=no",
        "ac_cv_func_endgrent=no",
        "ac_cv_func_getgrouplist=no",
        "ac_cv_func_initgroups=no",
        "ac_cv_module_grp=no",
    ]

    def apply_patches(self, arch, build_dir=None):
        self.patches = []

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        # Android bionic exposes some group APIs differently from glibc.
        # CPython 3.12 otherwise treats the missing declarations as fatal.
        env["CFLAGS"] = env.get("CFLAGS", "") + " -Wno-error=implicit-function-declaration"
        env["CPPFLAGS"] = env.get("CPPFLAGS", "") + " -D_GNU_SOURCE -UHAVE_GETGROUPLIST -UHAVE_INITGROUPS"
        return env

recipe = Python3Recipe()
