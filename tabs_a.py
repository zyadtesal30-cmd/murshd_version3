# -*- coding: utf-8 -*-
"""الشاشات: ١) بياناتي  ٢) موادي  ٣) حالتي"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import engine as E
from engine import (COURSES, C, ELEC_MIN, GRADE_LIST, GROUP_NAME, MONTH_AR, TOTAL_REQUIRED, pre_of, term_label)
from ui import (AMBER, AMBER_BG, BLUE, BLUE_BG, CARD2, DARK, GOLD, GREEN, GREEN_BG, MUTED, RED, RED_BG, SURFACE, TEAL,
                ALabel, ArInput, Bar, Btn, Card, RLabel, TapCard, chips, choice_popup, confirm_popup, hrow, info_popup,
                open_popup, seg, stepper, toggle)

KIND_TXT = {'univ': 'جامعة', 'college': 'كلية', 'major': 'تخصص رئيسي', 'sub': 'تخصص فرعي'}
TYPE_OPTS = [('F', 'خريف'), ('S', 'ربيع'), ('U', 'صيفي')]
PAGE = 14


def sec(text, color=GOLD):
    return ALabel(text, size=16, bold=True, color=color)


def lab_row(title, ctrl, h=44):
    lb = ALabel(title, size=13, color=MUTED, size_hint_x=.42, pos_hint={'center_y': .5})
    ctrl.size_hint_x = .58
    r = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h), spacing=dp(8))
    r.add_widget(ctrl)
    r.add_widget(lb)
    lb.bind(height=lambda w, hh: setattr(r, 'height', max(dp(h), hh + dp(8))))
    return r


def menu_btn():
    b = Btn('⋯', bg=CARD2, fg=GOLD, size=20, h=40, size_hint=(None, None), width=dp(42), pos_hint={'center_y': .5})
    b.size = (dp(42), dp(40))
    return b


class TabsA:
    # أداة عرض بالصفحات: بتبني أول دفعة بس عشان الشاشة تفتح بسرعة
    def paged(self, box, key, items, build, refill=None):
        n = self.limits.get(key, PAGE)
        for it in items[:n]:
            box.add_widget(build(it))
        rest = len(items) - n
        if not items:
            box.add_widget(ALabel('مفيش مواد مطابقة — جرّب نوع تاني أو امسح البحث.', size=13, color=MUTED, halign='center'))
        if rest > 0:
            more = Btn('عرض المزيد (%d متبقي)' % rest, bg=CARD2, fg=GOLD, h=46)

            def go(*a):
                self.limits[key] = n + PAGE
                if refill is not None:
                    refill()
                else:
                    self.show_tab(self.tab)
            more.bind(on_release=go)
            box.add_widget(more)

    def list_box(self):
        lst = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(12))
        lst.bind(minimum_height=lst.setter('height'))
        return lst

    # ───────────────── ١) بياناتي ─────────────────
    def t_info(self, box):
        s = self.set

        c = Card()
        c.add_widget(sec('أنا مين؟'))

        def on_name(v):
            s['name'] = v.strip()
            self.changed()
        c.add_widget(ArInput(text=s.get('name', ''), hint='اكتب اسمك (اختياري)', on_text=on_name))

        def on_gpa(v):
            try:
                s['gpa_manual'] = float(v.translate(E.AR_DIGITS).replace(',', '.')) if v.strip() else None
            except ValueError:
                s['gpa_manual'] = None
            self.changed()
        c.add_widget(ALabel('معدلي التراكمي (بيتحسب لوحده لو دخلت تقديرات):', size=12, color=MUTED))
        c.add_widget(ArInput(text='' if s.get('gpa_manual') is None else str(s['gpa_manual']), hint='مثال: 2.85',
                             numeric=True, on_text=on_gpa))
        c.add_widget(toggle('أنهيت التدريب الصيفي (٦ أسابيع على الأقل — شرط للتخرج)', s.get('training'),
                            lambda v: (s.__setitem__('training', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('الفصل القادم اللي هسجّل فيه'))
        nxt = ALabel('', size=16, bold=True, color=TEAL, halign='center')
        warn = ALabel('', size=12, color=RED)

        def refresh():
            m = s['months']
            nxt.set('الفصل القادم: ' + term_label(s['start_type'], s['start_year'], m))
            warn.set('' if m['S'] < m['U'] < m['F'] else
                     '⚠ المفروض الربيع قبل الصيفي قبل الخريف في نفس السنة — راجع الشهور.')

        def set_type(k):
            s['start_type'] = k
            self.changed()
            self.show_tab(0)
        c.add_widget(seg(TYPE_OPTS, s['start_type'], set_type))
        c.add_widget(lab_row('السنة', stepper(s['start_year'], 2020, 2060,
                                              lambda v: (s.__setitem__('start_year', v), self.changed(), refresh()))))
        c.add_widget(nxt)
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('ساعاتي في كل فصل'))
        c.add_widget(lab_row('أقصى عدد ساعات', stepper(s.get('cap', 21), 6, 21,
                                                       lambda v: (s.__setitem__('cap', v), self.changed()))))
        c.add_widget(lab_row('أقل عدد ساعات (0 = بدون)', stepper(s.get('min_load', 0), 0, 21,
                                                                 lambda v: (s.__setitem__('min_load', v), self.changed()))))
        c.add_widget(ALabel('لو المواد المطلوبة مش كفاية، البرنامج بيكمّل الفصل بمواد اختيارية إضافية.', size=12, color=MUTED))
        c.add_widget(toggle('استخدام الفصل الصيفي في الخطة', s.get('use_summer', True),
                            lambda v: (s.__setitem__('use_summer', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('شهر بداية كل فصل'))
        for typ, nm in (('F', 'خريف'), ('S', 'ربيع'), ('U', 'صيفي')):
            c.add_widget(lab_row(nm, stepper(int(s['months'][typ]), 1, 12,
                                             lambda v, t=typ: (s['months'].__setitem__(t, v), self.changed(), refresh()),
                                             fmt=lambda v: MONTH_AR[v - 1])))
        c.add_widget(warn)
        box.add_widget(c)
        refresh()

        c = Card()
        c.add_widget(sec('إعدادات متقدمة', MUTED))
        c.add_widget(toggle('كل مقرر بيتطرح في نوع الفصل المقترح له فقط (فردي = خريف / زوجي = ربيع)', s.get('parity', True),
                            lambda v: (s.__setitem__('parity', v), self.changed())))
        c.add_widget(toggle('مشروع التخرج (٢) لازم يكون بعد مشروع (١)', s.get('proj_order', True),
                            lambda v: (s.__setitem__('proj_order', v), self.changed())))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('نسخة احتياطية'))
        c.add_widget(ALabel('بياناتك بتتحفظ تلقائياً على الموبايل. تقدر تشارك نسخة أو تلصق نسخة من جهاز تاني.',
                            size=12, color=MUTED))
        e1 = Btn('مشاركة نسخة', h=44, size=13)
        e1.bind(on_release=lambda *a: self.export_data())
        e2 = Btn('استيراد من الحافظة', h=44, size=13)
        e2.bind(on_release=lambda *a: self.import_data())
        c.add_widget(hrow(e2, e1, h=44))
        box.add_widget(c)

        b = Btn('عن البرنامج وأهم قواعد اللائحة', bg=SURFACE, fg=GOLD, h=46)
        b.bind(on_release=lambda *a: info_popup('أهم قواعد اللائحة', E.RULES_TEXT + '\n\nتطوير: ' + E.DEVELOPER,
                                                size=(0.94, 0.85)))
        box.add_widget(b)

    # ───────────────── ٢) موادي (مقسّمة حسب نوع المتطلب) ─────────────────
    def is_passed(self, code):
        e = self.rec.get(code)
        return bool(e) and e.get('s') == 'done' and e.get('g') != 'F'

    def view_base(self, key):
        if key == 'ALL':
            return list(COURSES)
        return [c for c in COURSES if c.grp == key]

    def elective_hours(self):
        tot, per = 0, {}
        for g in ELEC_MIN:
            h = sum(c.cr for c in COURSES if c.grp == g and c.kind == 'E' and self.is_passed(c.code))
            per[g] = h
            tot += min(h, ELEC_MIN[g])
        return tot, per

    def visible_courses(self):
        q = self.f_q.strip().lower()
        out = []
        for c in self.view_base(self.view):
            if q and q not in c.name.lower() and q not in c.code.lower():
                continue
            if (self.f_kind == 'R' and c.kind != 'R') or (self.f_kind == 'E' and c.kind != 'E'):
                continue
            if self.f_left and self.is_passed(c.code):
                continue
            out.append(c)
        return sorted(out, key=lambda c: (0 if c.kind == 'R' else 1, c.sem if c.sem else 99, c.code))

    def set_status(self, codes, s, g=''):
        for code in codes:
            if s == 'none':
                self.rec.pop(code, None)
            else:
                self.rec[code] = {'s': s, 'g': g}
        self.changed()

    CATS = [('univ', 'الجامعة'), ('college', 'الكلية'), ('major', 'التخصص'), ('sub', 'الفرعي'), ('ALL', 'الكل')]

    def cat_chips(self):
        items = []
        for key, nm in self.CATS:
            base = self.view_base(key)
            req = [c for c in base if c.kind == 'R']
            d = sum(1 for c in req if self.is_passed(c.code))
            items.append((key, '%s %d/%d' % (nm, d, len(req)) + (' ✔' if req and d == len(req) else '')))
        return chips(items, self.view, lambda k: (setattr(self, 'view', k), self.show_tab(1, top=True)), h=38)

    def cat_info(self):
        key = self.view
        base = self.view_base(key)
        req = [c for c in base if c.kind == 'R']
        done_r = sum(1 for c in req if self.is_passed(c.code))
        txt = 'إجباري: %d من %d مقرر (%d ساعة)' % (done_r, len(req), sum(c.cr for c in req))
        if key in ELEC_MIN:
            per = self.elective_hours()[1][key]
            txt += '\nاختياري: %d من %d ساعة مطلوبة' % (min(per, ELEC_MIN[key]), ELEC_MIN[key])
        elif key == 'ALL':
            tot, _p = self.elective_hours()
            txt += '\nاختياري: %d من %d ساعة مطلوبة' % (tot, sum(ELEC_MIN.values()))
        cur = sum(1 for c in base if self.rec.get(c.code, {}).get('s') == 'cur')
        if cur:
            txt += '\nبتدرس حالياً: %d' % cur
        return txt

    def refresh_courses_header(self):
        if getattr(self, '_chips_box', None) is not None and self.tab == 1:
            self._chips_box.clear_widgets()
            self._chips_box.add_widget(self.cat_chips())
            self._info_lbl.set(self.cat_info())

    def t_courses(self, box):
        self._rows = {}
        self._chips_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(42))
        self._chips_box.add_widget(self.cat_chips())
        box.add_widget(self._chips_box)
        self._info_lbl = ALabel(self.cat_info(), size=12, color=MUTED)
        box.add_widget(self._info_lbl)

        lst = self.list_box()

        def fill(reset=False):
            if reset:
                self.limits.pop('courses', None)
            lst.clear_widgets()
            self._rows = {}
            self.paged(lst, 'courses', self.visible_courses(), self.course_row, fill)

        def on_q(v):
            self.f_q = v
            self.debounce(lambda: fill(True))      # بحث حي: القايمة بس بتتحدّث والحقل بيفضل مفتوح
        q = ArInput(text=self.f_q, hint='بحث بالاسم أو الكود', on_text=on_q)
        q.ti.bind(on_text_validate=lambda *a: fill(True))
        go = Btn('بحث', bg=GOLD, fg=DARK, size=13, h=46, size_hint_x=None, width=dp(68))
        go.bind(on_release=lambda *a: fill(True))
        box.add_widget(hrow(go, q, h=46))
        box.add_widget(seg([('ALL', 'الكل'), ('R', 'إجباري'), ('E', 'اختياري')], self.f_kind,
                           lambda k: (setattr(self, 'f_kind', k), self.show_tab(1, top=True)), h=38))
        box.add_widget(toggle('إخفاء اللي خلّصته', self.f_left,
                              lambda v: (setattr(self, 'f_left', v), self.show_tab(1, top=True))))

        a = Btn('وصلت لحد فصل…', h=42, size=12)
        a.bind(on_release=lambda *x: self.wizard())
        b = Btn('علّم كل الإجباري هنا', h=42, size=12)
        b.bind(on_release=lambda *x: self.mark_cat())
        d = Btn('مسح الكل', bg=RED_BG, fg=RED, h=42, size=12)
        d.bind(on_release=lambda *x: confirm_popup('تأكيد', 'مسح كل المقررات المعلّمة؟', self.clear_all) if self.rec else None)
        box.add_widget(hrow(d, b, a, h=42))
        box.add_widget(ALabel('اضغط على المادة للتعليم السريع (منتهٍ/لا)، وعلى ⋯ لاختيار التقدير أو «يدرسها الآن» أو «راسب».',
                              size=11, color=MUTED))
        box.add_widget(lst)
        fill()

    def course_lines(self, c):
        e = self.rec.get(c.code, {})
        s, g = e.get('s', 'none'), e.get('g', '')
        if s == 'done' and g == 'F':
            sym, col, bg = '✗', RED, RED_BG
        elif s == 'done' and g in ('D', 'D+'):
            sym, col, bg = '☑', AMBER, AMBER_BG
        elif s == 'done':
            sym, col, bg = '☑', GREEN, GREEN_BG
        elif s == 'cur':
            sym, col, bg = '◔', BLUE, BLUE_BG
        else:
            sym, col, bg = '☐', MUTED, SURFACE
        pre = '، '.join(C[p].name for p in pre_of(c.code, self.set)) or '—'
        meta = '%s • %d ساعة • %s%s%s' % (c.code, c.cr, 'إجباري' if c.kind == 'R' else 'اختياري',
                                         (' • فصل %d' % c.sem) if c.sem else '',
                                         (' • ' + KIND_TXT[c.grp]) if self.view == 'ALL' else '')
        if g:
            meta += ' • تقدير ' + g
        lines = [(sym + '  ' + c.name, col if s != 'none' else None, 15, True), (meta, MUTED, 11),
                 ('المتطلب: ' + pre, MUTED, 11)]
        return lines, bg, col if s != 'none' else CARD2

    def course_row(self, c):
        lines, bg, acc = self.course_lines(c)
        card = TapCard(orient='horizontal', bg=bg, accent=acc, pad=10, spacing=8, radius=14)
        mb = menu_btn()
        mb.bind(on_release=lambda *a: self.status_menu(c))
        rl = RLabel(lines)
        card.add_widget(mb)
        card.add_widget(rl)
        self._rows[c.code] = (card, rl)

        def tap(*a):
            cur = self.rec.get(c.code, {}).get('s', 'none')
            self.apply_status(c, 'none' if cur != 'none' else 'done')
        card.bind(on_release=tap)
        return card

    def apply_status(self, c, s, g=''):
        """تحديث مادة واحدة في مكانها (من غير إعادة بناء الصفحة)."""
        self.set_status([c.code], s, g)
        row = self._rows.get(c.code)
        if row is not None:
            card, rl = row
            if self.f_left and self.is_passed(c.code) and card.parent is not None:
                card.parent.remove_widget(card)
                self._rows.pop(c.code, None)
            else:
                lines, bg, acc = self.course_lines(c)
                rl.set_lines(lines)
                card.set_bg(bg)
                card.set_accent(acc)
        self.refresh_courses_header()

    def status_menu(self, c):
        opts = [('done:', 'منتهٍ (بدون تقدير)')]
        opts += [('done:' + g, 'منتهٍ — تقدير ' + g) for g in GRADE_LIST[:-1]]
        opts += [('done:F', 'راسب (F)'), ('cur:', 'يدرسه الآن'), ('none:', 'لم يدرسه')]

        def pick(k):
            st, g = k.split(':')
            self.apply_status(c, st, g)
        choice_popup(c.name, opts, pick)

    def wizard(self):
        root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(6))
        root.add_widget(ALabel('أنهيت المقررات الإجبارية حتى الفصل رقم:', size=15, bold=True, halign='center'))
        val = [6]
        root.add_widget(stepper(6, 0, 10, lambda v: val.__setitem__(0, v)))
        root.add_widget(ALabel('هيعلّم كل الإجباري في الفصول 1…N كمنتهٍ. بعدها عدّل اللي رسبت فيه وأضف الاختياري اللي درسته.',
                               size=12, color=MUTED))
        rep = [False]
        root.add_widget(toggle('امسح اختياراتي الحالية أولاً', False, lambda v: rep.__setitem__(0, v)))
        p = open_popup('مساعد سريع', root, (0.9, 0.62))
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(46), spacing=dp(8))
        no = Btn('إلغاء', h=46)
        ok = Btn('تطبيق', bg=GOLD, fg=DARK, h=46)
        no.bind(on_release=lambda *a: p.dismiss())

        def go(*a):
            if rep[0]:
                self.rec = {}
            for c in COURSES:
                if c.kind == 'R' and 0 < c.sem <= val[0] and c.code not in self.rec:
                    self.rec[c.code] = {'s': 'done', 'g': ''}
            p.dismiss()
            self.changed()
            self.show_tab(1)
        ok.bind(on_release=go)
        row.add_widget(no)
        row.add_widget(ok)
        root.add_widget(row)

    def mark_cat(self):
        if self.view == 'ALL':
            info_popup('تنبيه', 'اختار نوع متطلب معين (الجامعة / الكلية / التخصص / الفرعي) الأول.', size=(0.85, 0.3))
            return
        for c in COURSES:
            if c.grp == self.view and c.kind == 'R' and c.code not in self.rec:
                self.rec[c.code] = {'s': 'done', 'g': ''}
        self.changed()
        self.show_tab(1)

    def clear_all(self):
        self.rec = {}
        self.changed()
        self.show_tab(1)

    # ───────────────── ٣) حالتي ─────────────────
    def tile(self, title, value, col):
        cd = Card(pad=8, spacing=2, auto=False, size_hint_y=1)
        cd.add_widget(ALabel(title, size=11, color=MUTED, halign='center'))
        cd.add_widget(Btn(value, bg=SURFACE, fg=col, size=17, h=36, bold=True))
        return cd

    def t_dash(self, box, p):
        an, my = p['an'], p['my']
        done_h = an['counted'] + an['cur_hours']
        grad = '—' if my is None else ('جاهز' if not my['terms'] else my['finish_label'])
        gpa_txt = '%.2f' % an['gpa'] if an['gpa'] is not None else '—'
        r1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(84), spacing=dp(10))
        r1.add_widget(self.tile('المنجز', '%d / %d' % (done_h, TOTAL_REQUIRED), GOLD))
        r1.add_widget(self.tile('المتبقي', '%d ساعة' % an['remaining'], TEAL))
        r2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(84), spacing=dp(10))
        r2.add_widget(self.tile('المعدل', gpa_txt, RED if an['probation'] else GREEN))
        r2.add_widget(self.tile('التخرج المتوقع', grad, BLUE))
        box.add_widget(r1)
        box.add_widget(r2)

        c = Card()
        pct = int(100.0 * done_h / TOTAL_REQUIRED)
        c.add_widget(ALabel('%d%% من متطلبات التخرج%s' % (pct, ('  •  فصول متبقية: %d' % my['n_terms']) if my and my['terms'] else ''),
                            size=14, bold=True))
        c.add_widget(Bar(done_h / float(TOTAL_REQUIRED), height=dp(10)))
        box.add_widget(c)

        c = Card(spacing=8)
        c.add_widget(sec('التقدم في كل مجموعة'))
        for g in ('univ', 'college', 'major', 'sub'):
            gi = an['groups'][g]
            d = gi['req_done'] + gi['req_cur']
            el = '%d / %d' % (gi['e_done'] + gi['e_cur'], gi['e_min']) if 'e_min' in gi else '—'
            tot = gi['req_total'] + gi.get('e_min', 0)
            dn = d + min(gi.get('e_done', 0) + gi.get('e_cur', 0), gi.get('e_min', 0))
            c.add_widget(RLabel([(GROUP_NAME[g], None, 14, True),
                                 ('إجباري %d / %d   •   اختياري %s' % (d, gi['req_total'], el), MUTED, 12)]))
            c.add_widget(Bar(dn / float(tot) if tot else 0, color=TEAL))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('شروط التخرج'))
        sym = {'ok': ('✔', GREEN), 'no': ('✘', RED), 'unk': ('؟', AMBER), 'wait': ('…', MUTED)}
        c.add_widget(RLabel([('%s  %s — %s' % (sym.get(s_, ('', None))[0], t, d), sym.get(s_, ('', None))[1], 13, False)
                             for t, s_, d in p['check']]))
        box.add_widget(c)

        c = Card()
        c.add_widget(sec('إيه اللي بيأخّرني؟'))
        colors = {'ok': GREEN, 'info': None, 'warn': AMBER, 'bad': RED}
        c.add_widget(RLabel([('• ' + m, colors.get(k), 13, False) for k, m in p['diag']]))
        box.add_widget(c)
