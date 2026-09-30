[app]
title = OC管理器
package.name = ocmanager
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,json
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.arch = arm64-v8a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1