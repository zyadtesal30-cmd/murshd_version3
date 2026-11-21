# -*- coding: utf-8 -*-
"""
مرشد الطالب الأكاديمي — هندسة الميكاترونيات (نسخة أندرويد)
تطوير: Zyad Tarek
المصدر: لائحة قسم الميكاترونيات — كلية الهندسة — جامعة المنيا (2012)
"""
import copy
import json
import os
import sys
import threading
import traceback

try:
    from android.storage import app_storage_path   # noqa
    DATA_DIR = app_storage_path()
    ANDROID = True
except Exception:
    DATA_DIR = os.path.expanduser('~')
    ANDROID = False
os.environ['ADVISOR_HOME'] = DATA_DIR
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App                                   # noqa: E402
from kivy.clock import Clock                               # noqa: E402
from kivy.core.clipboard import Clipboard                  # noqa: E402
from kivy.core.window import Window                        # noqa: E402
from kivy.metrics import dp                                # noqa: E402
from kivy.uix.behaviors import ButtonBehavior              # noqa: E402
from kivy.graphics import Color, RoundedRectangle          # noqa: E402
from kivy.uix.boxlayout import BoxLayout                   # noqa: E402

import engine as E                                         # noqa: E402
from engine import C, term_label, term_offers, recommended_codes  # noqa: E402
from tabs_a import TabsA                                   # noqa: E402
from tabs_b import TabsB                                   # noqa: E402
from ui import (BG, BLUE_BG, CARD2, GOLD, MUTED, ON_PRIMARY, PRIMARY, SURFACE, TEXT, ALabel, Btn, Card,  # noqa: E402
                close_top_popup,
                info_popup, open_popup, page)

TABS = [('⚙', 'بياناتي'), ('☑', 'موادي'), ('◔', 'حالتي'), ('⌂', 'القسم'), ('✎', 'تسجيل'), ('➤', 'خطتي')]


class NavBtn(ButtonBehavior, BoxLayout):
    def __init__(self, icon, name, on, **kw):
        super().__init__(orientation='vertical', padding=(0, dp(8), 0, dp(4)), spacing=dp(1), **kw)
        self._on = on
        with self.canvas.before:
            Color(*_PILL)
            self._pill = RoundedRectangle(pos=self.pos, size=(0, 0), radius=[dp(14)])
        self.bind(pos=self._u, size=self._u)
        col = PRIMARY if on else MUTED
        self.add_widget(ALabel(icon, size=18, halign='center', color=col, size_hint_y=None, height=dp(24)))
        self.add_widget(ALabel(name, size=10.5, halign='center', color=TEXT if on else MUTED, bold=on,
                               size_hint_y=None, height=dp(16)))

    def _u(self, *a):
        if self._on:
            self._pill.size = (dp(54), dp(26))
            self._pill.pos = (self.center_x - dp(27), self.top - dp(8) - dp(26))


_PILL = (0.16, 0.22, 0.42, 1)


class Advisor(TabsA, TabsB, App):
    # ───────────── البداية ─────────────
    def build(self):
        self.title = 'مرشد الطالب'
        Window.clearcolor = BG
        Window.softinput_mode = 'below_target'
        if not ANDROID:
            Window.size = (420, 800)
        Window.bind(on_keyboard=self.on_key)

        self.rec = {}
        self.set = copy.deepcopy(E.DEFAULT_SET)
        self.cache = None
        self.crit_cache = None
        self.plans = []
        self.tracks = []
        self._ver = 0
        self._save_ev = None
        self._plans_tried = False
        self._sv = None
        self._reg_ok, self._reg_recs = set(), []
        self.limits = {}
        # حالة الواجهة
        self.tab = 0
        self.guide_on = False      # الدليل مقفول عند الفتح (يفتح بزر «؟ الدليل»)
        self.view, self.f_q, self.f_kind, self.f_left = 'univ', '', 'ALL', False
        self._rows, self._chips_box, self._info_lbl = {}, None, None
        self.dept_key, self.dept_sel, self.dept_mode, self.dept_q, self.dept_filter = None, set(), 'auto', '', 'all'
        self.dept_view, self._dchips, self.crit_open, self._deb = 'ALL', None, False, None
        self.plan_sub, self.plan_sel, self.track_sel = 'plans', None, None
        self.proj_path = os.path.join(DATA_DIR, 'student' + E.PROJ_EXT)

        root = BoxLayout(orientation='vertical')
        # الترويسة
        head = Card(bg=SURFACE, radius=0, pad=10, spacing=0, auto=False, orient='horizontal')
        head.height = dp(60)
        row = head
        gb = Btn('؟ الدليل', bg=CARD2, fg=PRIMARY, size=12, h=34, size_hint_x=None, width=dp(76), pos_hint={'center_y': .5}, bold=True)
        gb.bind(on_release=lambda *a: self.toggle_guide())
        tbox = BoxLayout(orientation='vertical', spacing=0)
        t1 = ALabel('مرشد الطالب الأكاديمي', size=17, bold=True, color=TEXT)
        t2 = ALabel('هندسة الميكاترونيات • Zyad Tarek', size=10.5, color=MUTED)
        tbox.add_widget(t1)
        tbox.add_widget(t2)
        row.add_widget(gb)
        row.add_widget(tbox)
        root.add_widget(head)

        self.content = BoxLayout(orientation='vertical')
        root.add_widget(self.content)

        self.nav = Card(bg=SURFACE, radius=0, pad=0, spacing=0, auto=False, orient='horizontal')
        self.nav.height = dp(60)
        root.add_widget(self.nav)

        self.startup_load()
        self.show_tab(0, top=True)
        return root

    def debounce(self, fn, delay=0.45):
        """تأخير بسيط عشان البحث الحي ما يتنفذش مع كل حرف."""
        if self._deb is not None:
            self._deb.cancel()
        self._deb = Clock.schedule_once(lambda dt: fn(), delay)

    def on_pause(self):
        self.save_now()
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.save_now()

    def on_key(self, win, key, *a):
        if key == 27:
            if close_top_popup():
                return True
            if self.tab != 0:
                self.show_tab(0, top=True)
                return True
        return False

    # ───────────── التنقل ─────────────
    def build_nav(self):
        self.nav.clear_widgets()
        for i in reversed(range(len(TABS))):
            ic, nm = TABS[i]
            b = NavBtn(ic, nm, i == self.tab)
            b.bind(on_release=lambda w, i=i: self.show_tab(i, top=True))
            self.nav.add_widget(b)

    def show_tab(self, i, top=False):
        if top:
            self.limits = {}
        old_y = None
        if i == self.tab and self._sv is not None and not top:
            old_y = self._sv.scroll_y
        self.tab = i
        self.content.clear_widgets()
        self.build_nav()
        sv, box = page()
        self._sv = sv
        self.content.add_widget(sv)
        gc = self.guide_card(i)
        if gc is not None:
            box.add_widget(gc)

        def restore(*a):
            if old_y is not None:
                sv.scroll_y = old_y
        try:
            if i == 0:
                self.t_info(box)
            elif i == 1:
                self.t_courses(box)
            elif i == 3:
                self.t_dept(box)
            elif i == 5:
                self.t_plan(box)
            else:
                self.with_pack(lambda p: self._fill(i, sv, box, p, old_y))
        except Exception:
            box.add_widget(ALabel('حصل خطأ:\n' + traceback.format_exc()[-700:], size=11, color=(1, .4, .4, 1)))
        Clock.schedule_once(restore, .08)

    def _fill(self, i, sv, box, p, old_y):
        if self.tab != i or sv is not self._sv:
            return
        try:
            if i == 2:
                self.t_dash(box, p)
            else:
                self.t_reg(box, p)
        except Exception:
            box.add_widget(ALabel('حصل خطأ:\n' + traceback.format_exc()[-700:], size=11, color=(1, .4, .4, 1)))
        if old_y is not None:
            Clock.schedule_once(lambda dt: setattr(sv, 'scroll_y', old_y), .08)

    # ───────────── الدليل الإرشادي ─────────────
    def toggle_guide(self):
        self.guide_on = not self.guide_on
        self.show_tab(self.tab)

    def guide_hint(self, i):
        s = self.set
        if i == 0:
            m = s['months']
            if not (m['S'] < m['U'] < m['F']):
                return '⚠ ترتيب الشهور غريب: المفروض الربيع قبل الصيفي قبل الخريف في نفس السنة.'
            return 'الفصل القادم: %s — لو تمام اضغط «التالي».' % term_label(s['start_type'], s['start_year'], m)
        if i == 1:
            n = sum(1 for c in E.COURSES if self.is_passed(c.code))
            if not n:
                return 'لسه ما علّمتش أي مقرر — ابدأ بمتطلبات الجامعة، أو استخدم «وصلت لحد فصل…» للتعليم السريع.'
            hrs = sum(c.cr for c in E.COURSES if self.is_passed(c.code))
            return '✔ علّمت %d مقرر (%d ساعة). كمّل لحد آخر فصل خلّصته ثم اضغط «التالي».' % (n, hrs)
        p = self.cache
        if p is None:
            return ''
        an, my, cfg = p['an'], p['my'], p['cfg']
        if i == 2:
            if my and my['terms']:
                return 'باقي %d ساعة معتمدة — التخرج المتوقع: %s.' % (an['remaining'], my['finish_label'])
            return 'مفيش مقررات متبقية — راجع شروط التخرج.'
        if i == 3:
            off = term_offers(cfg, cfg['start_type'], cfg['start_year'])
            if off is None:
                return 'القسم لسه ما أعلنش؟ اضغط «اعرف إيه اللازم يتفتح» تعرف تطلب إيه.'
            return '✔ علّمت %d مادة مفتوحة — هتختار منهم بس.' % len(off)
        if i == 4:
            rec, _t = recommended_codes(p)
            if rec:
                return 'الموصى بيه: %d مادة (%d ساعة). اضغط «اختار الموصى بيه» أو اختار بنفسك.' % (len(rec), sum(C[c].cr for c in rec))
            return '⚠ مفيش مواد موصى بيها للفصل ده — شوف تبويب «القسم» و«خطتي».'
        return ''

    def guide_card(self, i):
        if not self.guide_on:
            return None
        t, msg = E.GUIDE[i]
        c = Card(bg=BLUE_BG, accent=PRIMARY, pad=14, spacing=6)
        c.add_widget(ALabel('الدليل — خطوة %d من %d: %s' % (i + 1, len(E.GUIDE), t), size=14, bold=True, color=PRIMARY))
        c.add_widget(ALabel(msg, size=13, color=TEXT))
        try:
            h = self.guide_hint(i)
        except Exception:
            h = ''
        if h:
            c.add_widget(ALabel(h, size=12.5, bold=True, color=(0.24, 0.79, 0.71, 1)))
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        nx = Btn('التالي ◀', bg=PRIMARY, fg=ON_PRIMARY, h=38, size=13)
        pv = Btn('▶ السابق', bg=CARD2, fg=TEXT, h=38, size=13)
        nx.bind(on_release=lambda *a: self.show_tab(min(i + 1, len(E.GUIDE) - 1), top=True))
        pv.bind(on_release=lambda *a: self.show_tab(max(i - 1, 0), top=True))
        if i < len(E.GUIDE) - 1:
            row.add_widget(nx)
        if i > 0:
            row.add_widget(pv)
        c.add_widget(row)
        return c

    # ───────────── الحسابات (في خيط منفصل) ─────────────
    def changed(self):
        self._ver += 1
        self.cache = None
        self.crit_cache = None
        self.plans = []
        self.tracks = []
        self._plans_tried = False
        self.schedule_save()

    def run_async(self, fn, done):
        holder = {'pop': None, 'done': False}

        def show(dt):
            if holder['done']:
                return
            root = BoxLayout(orientation='vertical', padding=dp(10))
            root.add_widget(ALabel('جاري الحساب… لحظة', size=16, bold=True, color=GOLD, halign='center'))
            holder['pop'] = open_popup('من فضلك استنى', root, (0.72, 0.2))
            holder['pop'].auto_dismiss = False
        ev = Clock.schedule_once(show, 0.35)     # الحسابات السريعة ما بتظهرش نافذة

        def finish(res, err):
            holder['done'] = True
            ev.cancel()
            if holder['pop'] is not None:
                holder['pop'].dismiss()
            if err is not None:
                info_popup('خطأ', str(err), size=(0.9, 0.5))
                return
            done(res)

        def work():
            try:
                res, err = fn(), None
            except Exception as e:      # noqa
                res, err = None, e
            Clock.schedule_once(lambda dt: finish(res, err))
        threading.Thread(target=work, daemon=True).start()

    def with_pack(self, cb):
        if self.cache is not None:
            cb(self.cache)
            return
        ver = self._ver
        rec, setg = copy.deepcopy(self.rec), copy.deepcopy(self.set)

        def done(p):
            if ver != self._ver:        # اتغيّرت البيانات أثناء الحساب
                self.with_pack(cb)
                return
            self.cache = p
            cb(p)
        self.run_async(lambda: E.compute_all(rec, setg), done)

    # ───────────── الحفظ والفتح ─────────────
    def schedule_save(self):
        if self._save_ev is not None:
            self._save_ev.cancel()
        self._save_ev = Clock.schedule_once(lambda dt: self.save_now(), 1.0)

    def project_data(self):
        return {'version': 2, 'app': 'student_advisor', 'rec': self.rec, 'set': self.set}

    def save_now(self):
        try:
            E.write_project(self.proj_path, self.project_data())
        except Exception:
            pass

    def load_data(self, d):
        self.rec = {k: v for k, v in d.get('rec', {}).items() if k in C}
        self.set = copy.deepcopy(E.DEFAULT_SET)
        self.set.update(d.get('set', {}))
        m = dict(E.DEFAULT_MONTHS)
        for k, v in (self.set.get('months') or {}).items():
            try:
                if k in m and 1 <= int(v) <= 12:
                    m[k] = int(v)
            except (TypeError, ValueError):
                pass
        self.set['months'] = m
        self.set['offers'] = {k: [c for c in v if c in C] for k, v in (self.set.get('offers') or {}).items()}
        if self.set.get('summer_codes') is not None:
            self.set['summer_codes'] = [c for c in self.set['summer_codes'] if c in C]
        if not isinstance(self.set.get('picks'), dict):
            self.set['picks'] = {}
        self.dept_key = None
        self.changed()

    def startup_load(self):
        if os.path.exists(self.proj_path):
            try:
                self.load_data(E.read_project(self.proj_path))
            except Exception:
                pass

    # ───────────── نسخ ومشاركة ─────────────
    def copy_text(self, text):
        try:
            Clipboard.copy(text)
            info_popup('تم', 'تم النسخ — الصقه في أي مكان.', size=(0.8, 0.25))
        except Exception as e:      # noqa
            info_popup('تعذّر النسخ', str(e), size=(0.8, 0.3))

    def share_text(self, text):
        if ANDROID:
            try:
                from jnius import autoclass
                PA = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                it = Intent()
                it.setAction(Intent.ACTION_SEND)
                it.putExtra(Intent.EXTRA_TEXT, String(text))
                it.setType('text/plain')
                PA.mActivity.startActivity(Intent.createChooser(it, String('مشاركة')))
                return
            except Exception:
                pass
        self.copy_text(text)

    def export_data(self):
        self.share_text(json.dumps(self.project_data(), ensure_ascii=False))

    def import_data(self):
        try:
            d = json.loads(Clipboard.paste())
            if not isinstance(d, dict) or 'rec' not in d:
                raise ValueError('البيانات اللي في الحافظة مش نسخة من بياناتك.')
            self.load_data(d)
            self.save_now()
            self.show_tab(0, top=True)
            info_popup('تم', 'تم استيراد بياناتك.', size=(0.8, 0.25))
        except Exception as e:      # noqa
            info_popup('تعذّر الاستيراد', 'انسخ نص بياناتك (JSON) الأول ثم اضغط استيراد.\n' + str(e), size=(0.9, 0.4))


if __name__ == '__main__':
    Advisor().run()
