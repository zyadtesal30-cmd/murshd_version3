# -*- coding: utf-8 -*-
"""أدوات الواجهة: عربي سليم (تشكيل + RTL + التفاف)، تصميم عصري هادئ، عناصر خفيفة."""
import os
import re
from functools import lru_cache

from arshape import reshape as _reshape
from bidi.algorithm import get_display
from kivy.clock import Clock
from kivy.core.text import LabelBase, Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, 'fonts')


def _f(*names):
    for n in names:
        p = os.path.join(FD, n)
        if os.path.exists(p):
            return p
    return os.path.join(FD, names[-1])


# الخط الأساسي: خط حديث لو اتنزّل وقت البناء، وإلا الخط المدمج. خط الرموز: دايما المدمج.
LabelBase.register(name='AR', fn_regular=_f('ui-regular.ttf', 'DejaVuSansCondensed.ttf'),
                   fn_bold=_f('ui-bold.ttf', 'DejaVuSansCondensed-Bold.ttf'))
LabelBase.register(name='IC', fn_regular=_f('DejaVuSansCondensed.ttf'), fn_bold=_f('DejaVuSansCondensed-Bold.ttf'))


def _c(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (1,)


# ── لوحة ألوان هادئة (مريحة للعين) ──
BG = _c('0E1320')          # خلفية التطبيق
SURFACE = _c('161D2E')     # الكروت
CARD = SURFACE
CARD2 = _c('212B42')       # أزرار وحقول
PRIMARY = _c('5B7FF0')     # اللون الأساسي (أزرق هادئ)
GOLD = PRIMARY             # (اسم قديم)
ON_PRIMARY = _c('FFFFFF')
DARK = ON_PRIMARY          # (اسم قديم: لون النص فوق الأساسي)
INK = _c('0B1020')         # نص غامق فوق ألوان فاتحة
TEAL = _c('3DC9B5')
TEXT = _c('E8ECF4')
MUTED = _c('8E99B0')
GREEN = _c('52C98A')
AMBER = _c('F0B35A')
RED = _c('F0707A')
BLUE = _c('6FA8FF')
GREEN_BG = _c('142822')
RED_BG = _c('2D1A22')
AMBER_BG = _c('2B2414')
BLUE_BG = _c('172544')
PICK_BG = _c('1D2B55')
CREAM = BLUE_BG


def hexc(c):
    return '%02x%02x%02x' % tuple(int(round(x * 255)) for x in c[:3])


_EMOJI = re.compile('[\U0001F000-\U0001FFFF\uFE0F\u200d]')
# رموز مش موجودة في الخطوط العربية — بنرسمها بخط الرموز المدمج
_SYM = re.compile('([\u2010-\u2027\u2190-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2212\u00d7])')
_SPACE = 0.30


# النص بيتعرض معكوس (ترتيب بصري)، فـ «ا» + «ل» بتبقى «ل» + «ا» جنب بعض والخط بيدمجهم في رمز «لا» واحد
# (فـ «التالي» تظهر «التلاي»). فاصل غير مرئي (ZWNJ) بينهم بيمنع الدمج.
_LAM_ALEF = re.compile('([\uFEDD-\uFEE0])([\uFE81-\uFE84\uFE87\uFE88\uFE8D\uFE8E])')


@lru_cache(maxsize=8192)
def shape(s):
    s = _EMOJI.sub('', str(s)).strip()
    if not s:
        return ''
    return _LAM_ALEF.sub('\\1\u200c\\2', get_display(_reshape(s), base_dir='R'))


def mk(s):
    """نص جاهز للعرض -> نص ماركب آمن (مع تبديل خط الرموز)."""
    s = s.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')
    return _SYM.sub(r'[font=IC]\1[/font]', s)


@lru_cache(maxsize=64)
def _meter(px, bold):
    return CoreLabel(font_name='AR', font_size=px, bold=bold)


@lru_cache(maxsize=32768)
def _cw(ch, px, bold):
    return _meter(px, bold).get_extents(ch)[0]


def _wid(word, px, bold):
    return sum(_cw(c, px, bold) for c in shape(word))


def text_width(raw, px, bold=False):
    return _wid(raw, px, bold)


def wrap_text(text, width, px, bold=False):
    """يلفّ النص المنطقي على أسطر ثم يشكّل كل سطر على حدة."""
    text = _EMOJI.sub('', str(text))
    lines = []
    space = px * _SPACE
    limit = width * 0.90
    for para in text.split('\n'):
        words = para.split()
        if not words:
            lines.append('')
            continue
        cur, cw = [], 0.0
        for w in words:
            ww = _wid(w, px, bold)
            add = ww + (space if cur else 0)
            if cur and cw + add > limit:
                lines.append(' '.join(cur))
                cur, cw = [w], ww
            else:
                cur.append(w)
                cw += add
        lines.append(' '.join(cur))
    return '\n'.join(shape(l) if l else '' for l in lines)


class _Fit:
    """منطق مشترك: ما نرسمش النص قبل ما المقاس يتحدد."""

    def _force(self, *a):
        self._laid = True
        self._upd()

    def _on_w(self, *a):
        if abs(self.width - self._w) > 2:
            self._upd()

    def _on_ts(self, w, ts):
        self.height = max(ts[1] + dp(4), dp(18))

    def _ready(self):
        w = self.width
        return not (w < 30 or (w == 100 and not self._laid))


class ALabel(_Fit, Label):
    """نص عربي متعدد الأسطر بارتفاع تلقائي (بدون خروج عن المربع)."""

    def __init__(self, text='', size=14, color=TEXT, bold=False, halign='right', **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('line_height', 1.15)
        super().__init__(font_name='AR', font_size=dp(size), bold=bold, color=color, markup=True,
                         halign=halign, valign='top', **kw)
        self.raw = text
        self._bold = bold
        self._w = 0
        self._laid = False
        self.bind(width=self._on_w, texture_size=self._on_ts)
        Clock.schedule_once(self._force, 0)

    def set(self, t):
        if t != self.raw:
            self.raw = t
            self._w = 0
            self._upd()

    def _upd(self):
        if not self._ready():
            return
        w = self.width
        self._w = w
        self.text = mk(wrap_text(self.raw, w, self.font_size, self._bold))
        self.text_size = (w, None)


class RLabel(_Fit, Label):
    """عدة أسطر بألوان وأحجام مختلفة في عنصر واحد (أخف بكتير).
    lines = [(نص, لون, حجم, عريض)]"""

    def __init__(self, lines, halign='right', **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('line_height', 1.2)
        super().__init__(font_name='AR', markup=True, halign=halign, valign='top', color=TEXT, **kw)
        self.lines = lines
        self._w = 0
        self._laid = False
        self.bind(width=self._on_w, texture_size=self._on_ts)
        Clock.schedule_once(self._force, 0)

    def set_lines(self, lines):
        self.lines = lines
        self._w = 0
        self._upd()

    def _upd(self):
        if not self._ready():
            return
        w = self.width
        self._w = w
        out = []
        for ln in self.lines:
            text, col, size, bold = (tuple(ln) + (None, None, None, None))[:4]
            px = int(round(dp(size or 13)))
            wrapped = wrap_text(text, w, px, bool(bold))
            for sub in wrapped.split('\n'):
                s = '[size=%d][color=%s]%s[/color][/size]' % (px, hexc(col or TEXT), mk(sub))
                out.append('[b]' + s + '[/b]' if bold else s)
        self.text = '\n'.join(out)
        self.text_size = (w, None)


class Card(BoxLayout):
    def __init__(self, bg=SURFACE, radius=16, pad=14, spacing=6, auto=True, accent=None, orient='vertical', **kw):
        kw.setdefault('size_hint_y', None)
        rpad = dp(pad) + (dp(6) if accent else 0)
        super().__init__(orientation=orient, padding=[dp(pad), dp(pad), rpad, dp(pad)], spacing=dp(spacing), **kw)
        with self.canvas.before:
            self._col = Color(*bg)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
            self._acol = Color(*(accent or bg))
            self._ar = RoundedRectangle(pos=self.pos, size=(0, 0), radius=[dp(2)])
        self._has_accent = bool(accent)
        self.bind(pos=self._u, size=self._u)
        if auto:
            self.bind(minimum_height=self.setter('height'))

    def _u(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size
        if self._has_accent:
            self._ar.pos = (self.right - dp(5), self.y + dp(12))
            self._ar.size = (dp(3), max(0, self.height - dp(24)))

    def set_bg(self, c):
        self._col.rgba = c

    def set_accent(self, c):
        if self._has_accent:
            self._acol.rgba = c


class TapCard(ButtonBehavior, Card):
    pass


class Btn(Button):
    """زر بنص عربي يصغّر خطه تلقائياً ليبقى جوه الزر."""

    def __init__(self, text='', bg=CARD2, fg=TEXT, size=14, h=44, radius=12, bold=None, **kw):
        kw.setdefault('size_hint_y', None)
        if bold is None:
            bold = bg == PRIMARY
        super().__init__(text=mk(shape(text)), font_name='AR', font_size=dp(size), bold=bold, color=fg, markup=True,
                         background_normal='', background_down='', background_color=(0, 0, 0, 0),
                         height=dp(h), **kw)
        self.bg = bg
        self._raw = text
        self._base = dp(size)
        self._bold = bold
        with self.canvas.before:
            self._col = Color(*bg)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._u, size=self._u, state=self._st, width=self._fit)
        self._fit()

    def _fit(self, *a):
        w = self.width - dp(14)
        if w <= 10 or not self._raw:
            return
        tw = text_width(self._raw, int(self._base), self._bold)
        self.font_size = self._base if tw <= w else max(self._base * 0.55, self._base * w / float(tw))

    def set_text(self, t):
        self._raw = t
        self.text = mk(shape(t))
        self._fit()

    def set_bg(self, c, fg=None):
        self.bg = c
        self._col.rgba = c
        if fg:
            self.color = fg

    def _u(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size

    def _st(self, *a):
        self._col.rgba = tuple(min(1, x * 1.25) for x in self.bg[:3]) + (1,) if self.state == 'down' else self.bg


class Sw(ButtonBehavior, Widget):
    """مفتاح تشغيل/إيقاف عصري."""

    def __init__(self, on=False, on_change=None, **kw):
        super().__init__(size_hint=(None, None), size=(dp(46), dp(26)), **kw)
        self.on = bool(on)
        self._cb = on_change
        with self.canvas:
            self._tc = Color(*(GREEN if self.on else CARD2))
            self._tr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
            Color(1, 1, 1, 1)
            self._kn = Ellipse(pos=self.pos, size=(dp(20), dp(20)))
        self.bind(pos=self._u, size=self._u, on_release=self._flip)
        self._u()

    def _flip(self, *a):
        self.on = not self.on
        self._u()
        if self._cb:
            self._cb(self.on)

    def _u(self, *a):
        self._tc.rgba = GREEN if self.on else CARD2
        self._tr.pos = self.pos
        self._tr.size = self.size
        self._kn.size = (dp(20), dp(20))
        self._kn.pos = (self.right - dp(23) if self.on else self.x + dp(3), self.center_y - dp(10))


class Bar(Widget):
    def __init__(self, value=0.0, color=PRIMARY, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(8))
        super().__init__(**kw)
        self.value = value
        with self.canvas:
            Color(*CARD2)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(*color)
            self._fg = RoundedRectangle(pos=self.pos, size=(0, self.height), radius=[dp(4)])
        self.bind(pos=self._u, size=self._u)
        self._u()

    def _u(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._fg.pos = self.pos
        self._fg.size = (max(0, min(1, self.value)) * self.width, self.height)


_AR_DIG = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫،,', '01234567890123456789...')


def _num_filter(sub, from_undo):
    """يقبل الأرقام العربي والإنجليزي والنقطة العشرية."""
    return ''.join(ch for ch in sub.translate(_AR_DIG) if ch.isdigit() or ch == '.')


class ArInput(FloatLayout):
    """حقل إدخال بيعرض العربي متصل وصح. بنكتب في حقل شفاف ونعرض النص المشكّل فوقه.
    لوحة المفاتيح على أندرويد بتبعت الكلمة «تحت الكتابة» (composition) قبل ما تتثبّت،
    فبنعرضها هي كمان عشان الحرف يظهر لحظة الكتابة."""

    def __init__(self, text='', hint='', on_text=None, numeric=False, h=46, **kw):
        kw.setdefault('size_hint_y', None)
        super().__init__(height=dp(h), **kw)
        self._on_text = on_text
        self._hint = hint
        self._comp = ''
        self._poll = None
        self._last = None
        self._fb = False
        self._chk = None
        with self.canvas.before:
            self._col = Color(*CARD2)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        clear = (0, 0, 0, 0)
        self.ti = TextInput(text=text, multiline=False, size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                            font_name='AR', input_filter=_num_filter if numeric else None, write_tab=False,
                            background_normal='', background_active='', background_color=clear,
                            foreground_color=clear, cursor_color=clear, selection_color=clear,
                            hint_text_color=clear)
        try:
            self.ti.keyboard_suggestions = False     # من غير شريط اقتراحات = الحروف بتتثبّت فوراً
        except Exception:      # noqa
            pass
        # نفس أسلوب ALabel المضمون: markup + text_size بدون ارتفاع، والتوسيط بنعمله يدوي
        self.disp = Label(font_name='AR', font_size=dp(15), color=TEXT, markup=True, halign='right', valign='top',
                          size_hint=(None, None), size=(dp(100), dp(20)))
        self.add_widget(self.ti)
        self.add_widget(self.disp)
        self.bind(pos=self._u, size=self._u)
        self.disp.bind(texture_size=self._u)
        self.ti.bind(text=self._chg, focus=self._foc)
        self.ti.bind(on_text_validate=lambda *a: setattr(self.ti, 'focus', False))
        self._u()
        self._render()

    @property
    def text(self):
        return self.ti.text

    def _u(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size
        d = self.disp
        w = max(10, self.width - dp(24))
        d.width = w
        d.text_size = (w, None)
        d.height = max(d.texture_size[1], dp(20))
        d.x = self.x + dp(12)
        d.y = self.center_y - d.height / 2.0

    def _check(self, dt):
        # شبكة أمان: لو فيه نص (أو تلميح) والطبقة المشكّلة ما اترسمتش، نظهر الحقل العادي بدلها
        self._chk = None
        if self._fb:
            return
        want = self.ti.text or self._hint
        if want and self.disp.texture_size[0] < 2:
            self._fb = True
            self.disp.opacity = 0
            ti = self.ti
            ti.foreground_color = TEXT
            ti.cursor_color = TEXT
            ti.hint_text = self._hint
            ti.hint_text_color = MUTED
            ti.padding = [dp(12), dp(12), dp(12), dp(8)]
            ti.halign = 'right'

    def _chg(self, w, v):
        self._comp = ''
        self._render()
        if self._on_text:
            try:
                self._on_text(v)
            except Exception:      # noqa
                pass

    def _ime(self, win, txt):
        self._comp = txt or ''
        self._render()

    def _foc(self, w, f):
        self._col.rgba = _c('2A3652') if f else CARD2
        self._comp = ''
        if f:
            Window.bind(on_textedit=self._ime)
            if self._poll is None:
                self._poll = Clock.schedule_interval(self._tick, 0.12)
        else:
            Window.unbind(on_textedit=self._ime)
            if self._poll is not None:
                self._poll.cancel()
                self._poll = None
        self._render()

    def _tick(self, dt):
        # شبكة أمان: لو لوحة المفاتيح غيّرت النص من غير ما حدث يوصل، نحدّث العرض
        if self._last != (self.ti.text, self._comp_now(), self.ti.focus):
            self._render()

    def _comp_now(self):
        if self._comp:
            return self._comp
        ic = getattr(self.ti, '_ime_composition', '') or ''
        return '' if (not ic or self.ti.text.endswith(ic)) else ic

    def _render(self):
        v = self.ti.text
        comp = self._comp_now() if self.ti.focus else ''
        self._last = (v, comp, self.ti.focus)
        full = v + comp
        cur = '|' if self.ti.focus else ''
        try:
            if full or cur:
                self.disp.color = TEXT
                avail = max(10, self.width - dp(50))
                px = int(self.disp.font_size)
                k = 0
                # لو النص أطول من الحقل نخفي أول الحروف (اللي على اليمين) ونسيب الأحدث ظاهر
                while k < len(full) and _wid(full[k:] + cur, px, False) > avail:
                    k += 1
                self.disp.text = mk(shape(full[k:] + cur))
            else:
                self.disp.color = MUTED
                self.disp.text = mk(shape(self._hint))
        except Exception:      # noqa
            self.disp.color = TEXT
            self.disp.text = mk((full + cur) or self._hint)
        if not self._fb and self._chk is None:
            self._chk = Clock.schedule_once(self._check, 0.6)


def page(pad=14, spacing=12):
    sv = ScrollView(do_scroll_x=False, bar_width=dp(2), bar_color=(*PRIMARY[:3], 0.5), scroll_type=['content', 'bars'])
    box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(pad), spacing=dp(spacing))
    box.bind(minimum_height=box.setter('height'))
    sv.add_widget(box)
    return sv, box


def hrow(*widgets, h=44, spacing=8):
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(spacing))
    for w in widgets:
        r.add_widget(w)
    return r


def chips(items, selected, on_pick, h=38):
    """شريط أزرار أفقي قابل للتمرير. الأول يظهر يمين."""
    sv = ScrollView(do_scroll_y=False, size_hint_y=None, height=dp(h + 4), bar_width=0)
    inner = BoxLayout(orientation='horizontal', size_hint=(None, None), height=dp(h), spacing=dp(6))
    inner.bind(minimum_width=inner.setter('width'))
    for key, label in reversed(items):
        on = key == selected
        b = Btn(label, bg=PRIMARY if on else CARD2, fg=ON_PRIMARY if on else MUTED, size=13, h=h, radius=h / 2.0,
                size_hint_x=None, width=dp(max(60, 8.5 * len(label) + 28)))
        b.bind(on_release=lambda w, k=key: on_pick(k))
        inner.add_widget(b)
    sv.add_widget(inner)
    sv.scroll_x = 1
    return sv


def seg(options, value, on_change, h=40):
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(6))
    for key, label in reversed(options):
        on = key == value
        b = Btn(label, bg=PRIMARY if on else CARD2, fg=ON_PRIMARY if on else MUTED, size=13, h=h)
        b.bind(on_release=lambda w, k=key: on_change(k))
        r.add_widget(b)
    return r


def stepper(value, lo, hi, on_change, fmt=str, h=40):
    cur = [value]
    val = Btn(fmt(value), bg=SURFACE, fg=TEXT, size=15, h=h, bold=True)

    def bump(d):
        v = max(lo, min(hi, cur[0] + d))
        cur[0] = v
        val.set_text(fmt(v))
        on_change(v)
    minus = Btn('−', size=20, h=h, size_hint_x=None, width=dp(44), fg=PRIMARY, bold=True)
    plus = Btn('+', size=20, h=h, size_hint_x=None, width=dp(44), fg=PRIMARY, bold=True)
    minus.bind(on_release=lambda *a: bump(-1))
    plus.bind(on_release=lambda *a: bump(1))
    return hrow(plus, val, minus, h=h, spacing=4)


def toggle(text, value, on_change):
    sw = Sw(value, on_change, pos_hint={'center_y': .5})
    lb = ALabel(text, size=13, pos_hint={'center_y': .5})
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(12))
    r.add_widget(sw)
    r.add_widget(lb)
    lb.bind(height=lambda w, hh: setattr(r, 'height', max(dp(44), hh + dp(8))))
    return r


# ── النوافذ ──
_popups = []


def open_popup(title, content, size=(0.92, 0.8)):
    p = Popup(title=shape(title), title_font='AR', title_size=dp(15), title_align='right',
              content=content, size_hint=size, auto_dismiss=True,
              background='', background_color=SURFACE, separator_color=PRIMARY, title_color=TEXT)
    _popups.append(p)
    p.bind(on_dismiss=lambda *a: _popups.remove(p) if p in _popups else None)
    p.open()
    return p


def close_top_popup():
    if _popups:
        _popups[-1].dismiss()
        return True
    return False


def info_popup(title, text, buttons=None, size=(0.92, 0.7)):
    root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(6))
    sv = ScrollView(do_scroll_x=False)
    box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(4))
    box.bind(minimum_height=box.setter('height'))
    box.add_widget(ALabel(text, size=14))
    sv.add_widget(box)
    root.add_widget(sv)
    p = open_popup(title, root, size)
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
    for lb, cb in (buttons or []):
        b = Btn(lb, bg=PRIMARY, fg=ON_PRIMARY, h=44)
        b.bind(on_release=lambda w, cb=cb: cb())
        row.add_widget(b)
    c = Btn('إغلاق', h=44)
    c.bind(on_release=lambda *a: p.dismiss())
    row.add_widget(c)
    root.add_widget(row)
    return p


def confirm_popup(title, text, on_yes):
    root = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(6))
    root.add_widget(ALabel(text, size=14))
    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
    p = open_popup(title, root, (0.88, 0.4))
    no = Btn('إلغاء', h=44)
    yes = Btn('تأكيد', bg=RED, fg=INK, h=44, bold=True)
    no.bind(on_release=lambda *a: p.dismiss())

    def go(*a):
        p.dismiss()
        on_yes()
    yes.bind(on_release=go)
    row.add_widget(no)
    row.add_widget(yes)
    root.add_widget(row)
    return p


def choice_popup(title, options, on_pick, size=(0.88, 0.7)):
    sv, box = page(8, 8)
    p = open_popup(title, sv, size)
    for key, label in options:
        b = Btn(label, size=14, h=44)

        def pick(w, k=key):
            p.dismiss()
            on_pick(k)
        b.bind(on_release=pick)
        box.add_widget(b)
    return p
