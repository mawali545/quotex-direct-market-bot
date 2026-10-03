from pythonforandroid.recipes.python3 import Python3Recipe as BasePython3Recipe

class Python3Recipe(BasePython3Recipe):
    version = "3.12.10"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    patches = []
    configure_args = BasePython3Recipe.configure_args + (
        "--with-build-python={python_host_bin}",
        "ac_cv_func_getgrent=no",
    )

recipe = Python3Recipe()
