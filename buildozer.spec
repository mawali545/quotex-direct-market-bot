[app]
title = AMH110
package.name = amh110
package.domain = org.amh110
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,txt
source.exclude_dirs = tests,bin,.buildozer,__pycache__,.git
version = 3.0.0
requirements = python3==3.12.10,hostpython3==3.12.10,kivy==2.3.1,pyjnius,android,websockets==14.2.0,httpx,httpcore,anyio,h11,sniffio,idna,typing_extensions,beautifulsoup4,certifi,fake-useragent==2.2.0,pyfiglet>=1.0.2,<2.0.0,rich>=13.7.0,<14.0.0,git+https://github.com/cleitonleonel/pyquotex.git@70fca1575b9c3e8f45aaaa08a54baf67adbdac68
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,SYSTEM_ALERT_WINDOW,WAKE_LOCK
android.accept_sdk_license = True
p4a.branch = master
p4a.commit = 54cf321676712893786d4ccbbefbad3ff2e5930d
p4a.setup_py = false

[buildozer]
log_level = 2
warn_on_root = 1
