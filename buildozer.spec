[app]
title = OC管理器
package.name = ocmanager
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json
version = 1.4
android.numeric_version = 5
requirements = hostpython3==3.11.9,python3==3.11.9,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.accept_sdk_license = True
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1