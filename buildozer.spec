[app]
title = AMH110
package.name = amh110
package.domain = org.amh110
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,txt
source.exclude_dirs = tests,bin,.buildozer,__pycache__,.git
version = 3.0.3
icon.filename = icon.png
requirements = python3==3.12.10,hostpython3==3.12.10,kivy==2.3.1,pyjnius,android,curl_cffi==0.16.2,cffi==2.0.0,pycparser,typing_extensions,beautifulsoup4,certifi,charset-normalizer==3.4.3,fake-useragent==2.2.0,pyfiglet>=1.0.2,rich>=13.7.0,pyquotex
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,SYSTEM_ALERT_WINDOW,WAKE_LOCK
android.accept_sdk_license = True
p4a.branch = master
p4a.commit = e772ad93f20a61c0bbe1cf8955e073cfb41062e1
p4a.setup_py = false
p4a.local_recipes = p4a-recipes

[buildozer]
log_level = 2
warn_on_root = 1
