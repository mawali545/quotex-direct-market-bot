[app]
title = Direct Market Signal Bot
package.name = directmarketsignal
package.domain = org.directmarketsignal
source.dir = .
source.include_exts = py,kv,png,jpg,txt
source.exclude_dirs = tests,bin,.git,.buildozer,__pycache__
version = 0.6.0
requirements = python3,kivy,websockets==12.0,httpx==0.27.2,httpcore==1.0.7,anyio==4.8.0,h11==0.14.0,sniffio==1.3.1,idna==3.10,typing_extensions==4.12.2,beautifulsoup4==4.13.4,certifi==2025.7.14,fake-useragent==2.2.0,pyfiglet==1.0.2,rich==13.9.4,git+https://github.com/cleitonleonel/pyquotex.git@70fca1575b9c3e8f45aaaa08a54baf67adbdac68
orientation = all
fullscreen = 0
android.api = 34
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.accept_sdk_license = True
p4a.branch = master
p4a.commit = 957a3e5
p4a.setup_py = false

[buildozer]
log_level = 2
warn_on_root = 1
