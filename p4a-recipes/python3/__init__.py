from pythonforandroid.recipes.python3 import Python3Recipe as BasePython3Recipe
class Python3Recipe(BasePython3Recipe):
    version="3.12.10"
    url="https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env=super().get_recipe_env(arch,with_flags_in_cc)
        env["CFLAGS"]=env.get("CFLAGS","")+" -Wno-error=implicit-function-declaration -Dsetgrent(...)=((void)0) -Dendgrent(...)=((void)0) -Dgetgrent(...)=((struct group *)0) -Dgetgrouplist(...)=(-1) -Dinitgroups(...)=(-1)"
        return env
recipe=Python3Recipe()
