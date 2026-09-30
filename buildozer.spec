[app]
title = Direct Market Signal Bot
package.name = directmarketsignal
package.domain = org.directmarketsignal
source.dir = .
source.include_exts = py,kv,png,jpg,txt
version = 0.5.5
requirements = python3,kivy,pyjnius,beautifulsoup4,certifi,curl_cffi,fake-useragent,pyfiglet,rich,typing_extensions,git+https://github.com/cleitonleonel/pyquotex.git
orientation = all
fullscreen = 0
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.permissions = SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,POST_NOTIFICATIONS,INTERNET,ACCESS_NETWORK_STATE
android.accept_sdk_license = True
p4a.branch = develop

android.add_src = src

[buildozer]
log_level = 2
warn_on_root = 1
