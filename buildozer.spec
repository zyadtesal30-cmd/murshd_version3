[app]
# مهم: لازم يفضل هنا تحت [app] — بيثبّت نسخة python-for-android (من غيره البيلد بيفشل)
p4a.branch = v2024.01.21

title = Murshid Al-Talib
package.name = murshidtalib
package.domain = org.zyadtarek
version = 1.0.0

source.dir = .
source.include_exts = py,png,jpg,ttf
source.include_patterns = fonts/*
source.exclude_dirs = .github,bin,.buildozer,tools

# إصدارات مثبّتة: بايثون 3.11.5 للتطبيق وللبناء (لازم يتطابقوا)
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,python-bidi==0.4.2,six,setuptools,pyjnius,android

orientation = portrait
fullscreen = 0

android.archs = arm64-v8a
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True
android.permissions =
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
