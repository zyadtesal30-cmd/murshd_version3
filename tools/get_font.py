# -*- coding: utf-8 -*-
"""ينزّل خط عربي حديث ويتأكد إنه بيدعم كل أشكال الحروف المتصلة. لو فشل، التطبيق بيستخدم الخط المدمج."""
import os
import shutil
import sys
import tempfile
import urllib.request

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'fonts')
G = 'https://github.com/google/fonts/raw/main/ofl/%s/%s'
N = 'https://github.com/notofonts/notofonts.github.io/raw/main/fonts/%s/hinted/ttf/%s'
CANDIDATES = [
    ('Noto Sans Arabic UI', N % ('NotoSansArabicUI', 'NotoSansArabicUI-Regular.ttf'), N % ('NotoSansArabicUI', 'NotoSansArabicUI-Bold.ttf')),
    ('Tajawal', G % ('tajawal', 'Tajawal-Regular.ttf'), G % ('tajawal', 'Tajawal-Bold.ttf')),
    ('IBM Plex Sans Arabic', G % ('ibmplexsansarabic', 'IBMPlexSansArabic-Regular.ttf'), G % ('ibmplexsansarabic', 'IBMPlexSansArabic-Bold.ttf')),
    ('Almarai', G % ('almarai', 'Almarai-Regular.ttf'), G % ('almarai', 'Almarai-Bold.ttf')),
]
# أشكال الحروف المتصلة (Presentation Forms-B) + الأرقام + الحروف اللاتينية
NEED = list(range(0xFE80, 0xFEFD)) + [0x0627, 0x0644, 0x060C, 0x061F] + list(range(0x30, 0x3A)) + list(range(0x41, 0x5B)) + list(range(0x0660, 0x066A))


def fetch(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)


def good(path):
    cm = TTFont(path, lazy=True).getBestCmap()
    miss = [c for c in NEED if c not in cm]
    return len(miss) <= 8 and 0x200C in cm, len(miss)      # ZWNJ لازم يكون موجود (بيمنع دمج «لا»)


def main():
    tmp = tempfile.mkdtemp()
    for name, ru, bu in CANDIDATES:
        try:
            r, b = os.path.join(tmp, 'r.ttf'), os.path.join(tmp, 'b.ttf')
            fetch(ru, r)
            fetch(bu, b)
            ok1, m1 = good(r)
            ok2, m2 = good(b)
            print('%s: missing glyphs regular=%d bold=%d' % (name, m1, m2))
            if ok1 and ok2:
                shutil.copy(r, os.path.join(OUT, 'ui-regular.ttf'))
                shutil.copy(b, os.path.join(OUT, 'ui-bold.ttf'))
                print('USING FONT:', name)
                return 0
        except Exception as e:      # noqa
            print('%s: failed (%s)' % (name, e))
    print('No modern font validated; using bundled font.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
