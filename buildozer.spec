[app]
title = Direct Market Signal Bot
package.name = directmarketsignal
package.domain = org.directmarketsignal
source.dir = .
source.include_exts = py,kv,png,jpg,txt
version = 0.4.0
requirements = python3,kivy,git+https://github.com/cleitonleonel/pyquotex.git
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.accept_sdk_license = True
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
