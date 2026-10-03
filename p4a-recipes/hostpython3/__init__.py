from pythonforandroid.recipes.hostpython3 import HostPython3Recipe as BaseHostPython3Recipe

class HostPython3Recipe(BaseHostPython3Recipe):
    version = "3.12.10"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"

recipe = HostPython3Recipe()
