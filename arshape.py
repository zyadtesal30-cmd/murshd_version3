# -*- coding: utf-8 -*-
"""مشكّل عربي خفيف: بيحوّل الحروف لأشكالها المتصلة (Presentation Forms-B فقط).
أخف من مكتبة arabic-reshaper، ومفيهوش رموز ربط نادرة ممكن تكون ناقصة في الخط."""
import re
import unicodedata

_HARAKAT = re.compile('[\u064B-\u065F\u0670\u06D6-\u06ED]')
_ALEFS = '\u0622\u0623\u0625\u0627'

_FORMS = {}
_LAMALEF = {}
for _cp in range(0xFE70, 0xFEFD):
    _d = unicodedata.decomposition(chr(_cp))
    if not _d.startswith('<'):
        continue
    _tag, _rest = _d.split(' ', 1)
    _parts = _rest.split()
    _tag = _tag.strip('<>')
    if len(_parts) == 1:
        _FORMS.setdefault(chr(int(_parts[0], 16)), {})[_tag] = chr(_cp)
    elif len(_parts) == 2 and _parts[0] == '0644':
        _LAMALEF.setdefault(chr(int(_parts[1], 16)), {})[_tag] = chr(_cp)

_CLASS = {}
for _b, _f in _FORMS.items():
    _CLASS[_b] = 'D' if 'initial' in _f else ('R' if 'final' in _f else 'N')
_CLASS['\u0640'] = 'D'       # التطويل


def reshape(text):
    text = _HARAKAT.sub('', text).replace('\u0671', '\u0627')
    toks = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '\u0644' and i + 1 < n and text[i + 1] in _ALEFS:
            toks.append(('LA', text[i + 1]))
            i += 2
            continue
        toks.append((_CLASS.get(c, 'O'), c))
        i += 1
    out = []
    last = len(toks) - 1
    for k, (cls, c) in enumerate(toks):
        pj = k > 0 and toks[k - 1][0] == 'D'
        nj = k < last and toks[k + 1][0] in ('D', 'R', 'LA')
        if cls == 'D':
            f = _FORMS.get(c)
            if not f:
                out.append(c)
            else:
                form = 'medial' if (pj and nj) else 'final' if pj else 'initial' if nj else 'isolated'
                out.append(f.get(form) or f.get('isolated') or c)
        elif cls == 'R':
            f = _FORMS[c]
            out.append((f.get('final') if pj else f.get('isolated')) or c)
        elif cls == 'LA':
            f = _LAMALEF[c]
            out.append((f.get('final') if pj else f.get('isolated')) or '\u0644' + c)
        elif cls == 'N':
            out.append(_FORMS[c].get('isolated', c))
        else:
            out.append(c)
    return ''.join(out)
