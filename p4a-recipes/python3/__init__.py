from pythonforandroid.recipes.python3 import Python3Recipe as BasePython3Recipe

class Python3Recipe(BasePython3Recipe):
    version = "3.12.10"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    # CPython 3.12.10 is not compatible with the old p4a CPython 3.11
    # patch set. Keep this recipe patch-free.
    patches = []

    def apply_patches(self, arch, build_dir=None):
        # python-for-android's base recipe repopulates its upstream patch list.
        # Explicitly bypass that for our CPython 3.12.10 source.
        return None

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        # NDK r25 uses compiler-rt/LLVM and does not ship the legacy GCC\n        # runtime library. Older p4a flags can inject -lgcc_s into libffi/CPython\n        # configure tests, causing Android linker failures. Remove that stale flag.\n        for key in ("LDFLAGS", "LIBS", "LDLIBS"):\n            env[key] = env.get(key, "").replace(" -lgcc_s", "").replace("-lgcc_s ", "").replace("-lgcc_s", "")\n\n        env["CFLAGS"] = env.get("CFLAGS", "") + (
            " -Wno-error=implicit-function-declaration"
            " -Dsetgrent(...)=((void)0)"
            " -Dendgrent(...)=((void)0)"
            " -Dgetgrent(...)=((struct group *)0)"
            " -Dgetgrouplist(...)=(-1)"
            " -Dinitgroups(...)=(-1)"
        )
        return env

recipe = Python3Recipe()
