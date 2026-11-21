# -*- coding: utf-8 -*-
"""الشاشات: ٤) القسم  ٥) تسجيل  ٦) خطتي"""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import engine as E
from engine import C, COURSES, PROBATION_LOAD, Student, pre_of, recommended_codes, term_label, term_offers
from tabs_a import KIND_TXT, lab_row, sec
from ui import (RED_BG, AMBER, AMBER_BG, BLUE, BLUE_BG, CARD2, DARK, GOLD, GREEN, GREEN_BG, INK, MUTED, PICK_BG, RED, SURFACE, TEAL,
                ALabel, ArInput, Btn, Card, RLabel, TapCard, chips, choice_popup, hrow, info_popup, seg, stepper)

SUMMER_KEY = 'SUMMER*'
LEVEL_TXT = {'crit': 'لازم يتفتح', 'imp': 'يفضل يتفتح', 'ok': 'ممكن بديل'}
LEVEL_COL = {'crit': RED, 'imp': AMBER, 'ok': GREEN}
STATE_TXT = {'open': '✔ مفتوح', 'closed': '✘ مش مفتوح', 'unknown': '؟ لسه ما أعلنوش'}


class TabsB:
    # ───────────────── ٤) القسم ─────────────────
    def dept_scopes(self):
        s = self.set
        offers = s.setdefault('offers', {})
        out = []
        for typ, yr in E.term_sequence(s['start_type'], s['start_year'], 6, s.get('use_summer', True)):
            k = E.tkey(typ, yr)
            out.append((k, term_label(typ, yr, s['months']) + ('   ✔ معلن' if k in offers else '')))
        if s.get('use_summer', True):
            out.append((SUMMER_KEY, 'كل الصيفيات (افتراضي)' + ('   ✔' if s.get('summer_codes') is not None else '')))
        return out

    def load_dept_scope(self):
        s = self.set
        codes = s.get('summer_codes') if self.dept_key == SUMMER_KEY else s.setdefault('offers', {}).get(self.dept_key)
        self.dept_mode = 'auto' if codes is None else 'list'
        self.dept_sel = set(codes or [])

    def dept_save(self):
        s = self.set
        val = sorted(self.dept_sel) if self.dept_mode == 'list' else None
        if self.dept_key == SUMMER_KEY:
            s['summer_codes'] = val
        elif val is None:
            s.setdefault('offers', {}).pop(self.dept_key, None)
        else:
            s.setdefault('offers', {})[self.dept_key] = val
        self.changed()

    def dept_rows(self):
        st = Student(self.rec)
        q = self.dept_q.strip().lower()
        rows = []
        for c in COURSES:
            if q and q not in c.name.lower() and q not in c.code.lower():
                continue
            if self.dept_view != 'ALL' and c.grp != self.dept_view:
                continue
            passed = st.passed(c.code) and not st.low(c.code)
            missing = [p for p in pre_of(c.code, self.set) if not st.satisfied(p)]
            if self.dept_filter == 'avail' and (passed or st.cur(c.code) or missing):
                continue
            if self.dept_filter == 'req' and (c.kind != 'R' or passed or st.cur(c.code)):
                continue
            note = ('خلّصته' if passed else 'بتدرسه الآن' if st.cur(c.code) else
                    ('ناقص متطلب: ' + '، '.join(C[p].name for p in missing)) if missing else 'جاهز ليك ✔')
            rows.append((c, note))
        rows.sort(key=lambda r: (r[0].sem if r[0].sem else 99, 0 if r[0].kind == 'R' else 1, r[0].code))
        return rows

    def dept_cat_chips(self):
        items = []
        for key, nm in self.CATS:
            n = sum(1 for c in self.view_base(key) if c.code in self.dept_sel)
            items.append((key, nm + (' (%d)' % n if n else '')))
        return chips(items, self.dept_view, lambda k: (setattr(self, 'dept_view', k), self.show_tab(3, top=True)), h=38)

    def refresh_dept_chips(self):
        if self._dchips is not None and self.tab == 3:
            self._dchips.clear_widgets()
            self._dchips.add_widget(self.dept_cat_chips())

    def t_dept(self, box):
        scopes = self.dept_scopes()
        keys = [k for k, _ in scopes]
        if self.dept_key not in keys:
            self.dept_key = keys[0]
            self.load_dept_scope()
        label = dict(scopes)[self.dept_key]

        c = Card()
        c.add_widget(sec('الفصل اللي بتسجّل فيه'))
        b = Btn(label + '   ▼', bg=GOLD, fg=DARK, h=48)

        def pick_scope(k):
            self.dept_key = k
            self.load_dept_scope()
            self.show_tab(3, top=True)
        b.bind(on_release=lambda *a: choice_popup('اختار الفصل', scopes, pick_scope))
        c.add_widget(b)

        def set_mode(m):
            self.dept_mode = m
            self.dept_save()
            self.show_tab(3)
        c.add_widget(seg([('auto', 'لسه ما أعلنوش'), ('list', 'القسم أعلن مواد')], self.dept_mode, set_mode))
        if self.dept_mode == 'list':
            c.add_widget(ALabel('علّمت %d مادة مفتوحة. اختارهم من الأقسام تحت.' % len(self.dept_sel), size=13, bold=True,
                                color=GREEN))
        else:
            c.add_widget(ALabel('لو القسم أعلن، اختار «القسم أعلن مواد» وعلّم المواد المفتوحة من تحت.', size=12, color=MUTED))
        box.add_widget(c)

        # ── المواد المفتوحة (نفس أقسام «موادي» + الكل) — قبل أي حاجة طويلة عشان تظهر على طول ──
        box.add_widget(sec('المواد المفتوحة'))
        self._dchips = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(42))
        self._dchips.add_widget(self.dept_cat_chips())
        box.add_widget(self._dchips)
        box.add_widget(seg([('avail', 'المتاحة لي'), ('req', 'الإجباري المتبقي'), ('all', 'كل المواد')],
                           self.dept_filter, lambda k: (setattr(self, 'dept_filter', k), self.show_tab(3, top=True)), h=38))

        lst = self.list_box()
        state = {'rows': []}

        def fill(reset=False):
            if reset:
                self.limits.pop('dept', None)
            lst.clear_widgets()
            state['rows'] = self.dept_rows()
            self.paged(lst, 'dept', state['rows'], lambda r: self.dept_row(r[0], r[1]), fill)

        def on_q(v):
            self.dept_q = v
            self.debounce(lambda: fill(True))
        q = ArInput(text=self.dept_q, hint='بحث بالاسم أو الكود', on_text=on_q)
        q.ti.bind(on_text_validate=lambda *a: fill(True))
        go2 = Btn('بحث', bg=GOLD, fg=DARK, size=13, h=46, size_hint_x=None, width=dp(68))
        go2.bind(on_release=lambda *a: fill(True))
        box.add_widget(hrow(go2, q, h=46))

        def all_():
            self.dept_mode = 'list'
            self.dept_sel |= {c.code for c, _ in self.dept_rows()}
            self.dept_save()
            self.show_tab(3)

        def clr():
            self.dept_sel = set()
            self.dept_save()
            self.show_tab(3)
        a = Btn('تحديد كل الظاهر', h=42, size=13)
        a.bind(on_release=lambda *x: all_())
        d = Btn('مسح التحديد', h=42, size=13)
        d.bind(on_release=lambda *x: clr())
        box.add_widget(hrow(d, a, h=42))
        box.add_widget(lst)
        fill()

        # ── إيه اللازم يتفتح؟ (مطوية افتراضياً) ──
        c = Card()
        tg = Btn('إيه اللازم يتفتح من القسم؟   ' + ('▲' if self.crit_open else '▼'), bg=CARD2, fg=GOLD, h=46)

        def toggle_crit(*a):
            self.crit_open = not self.crit_open
            self.show_tab(3)
        tg.bind(on_release=toggle_crit)
        c.add_widget(tg)
        if self.crit_open:
            c.add_widget(lab_row('أبحث في أول (عدد) فصول', stepper(self.set.get('look', 2), 1, 4,
                                                                  lambda v: (self.set.__setitem__('look', v), self.changed()))))
            go = Btn('اعرف إيه اللازم يتفتح', bg=GOLD, fg=DARK, h=48)
            go.bind(on_release=lambda *a: self.compute_crit())
            c.add_widget(go)
            self.show_crit(c)
        box.add_widget(c)

    def dept_lines(self, c, note, on):
        return [(('☑  ' if on else '☐  ') + c.name, GREEN if on else None, 15, True),
                ('%s • %d ساعة • فصل %s • %s — %s' % (c.code, c.cr, c.sem if c.sem else '—',
                                                    'إجباري' if c.kind == 'R' else 'اختياري', KIND_TXT[c.grp]), MUTED, 11),
                (note, TEAL if 'جاهز' in note else MUTED, 11)]

    def dept_row(self, c, note):
        on = c.code in self.dept_sel
        card = TapCard(bg=GREEN_BG if on else SURFACE, accent=GREEN if on else CARD2, pad=10, radius=14)
        rl = RLabel(self.dept_lines(c, note, on))
        card.add_widget(rl)

        def tap(*a):
            self.dept_mode = 'list'
            if c.code in self.dept_sel:
                self.dept_sel.discard(c.code)
            else:
                self.dept_sel.add(c.code)
            self.dept_save()
            on2 = c.code in self.dept_sel
            card.set_bg(GREEN_BG if on2 else SURFACE)
            card.set_accent(GREEN if on2 else CARD2)
            rl.set_lines(self.dept_lines(c, note, on2))
            self.refresh_dept_chips()
        card.bind(on_release=tap)
        return card

    def compute_crit(self):
        def with_p(p):
            look = self.set.get('look', 2)

            def done(res):
                self.crit_cache = res
                self.crit_open = True
                if self.tab == 3:
                    self.show_tab(3)
            self.run_async(lambda: E.critical_to_open(p['st'], p['cfg'], p['prefs'], look), done)
        self.with_pack(with_p)

    def show_crit(self, card):
        cr = self.crit_cache
        if cr is None:
            card.add_widget(ALabel('اضغط الزر عشان تعرف تطلب من القسم إيه.', size=12, color=MUTED))
            return
        if not cr or not cr['base'] or not cr['base']['terms']:
            card.add_widget(ALabel('مفيش مقررات متبقية تحتاج فتح من القسم.', size=13, color=GREEN))
            return
        items = cr['items']
        n = {k: sum(1 for i in items if i['level'] == k) for k in LEVEL_TXT}
        closed = [i for i in items if i['level'] == 'crit' and i['state'] == 'closed']
        lines = [('لو القسم فتح اللازم هتتخرج %s.' % cr['base']['finish_label'], GOLD, 14, True),
                 ('لازم يتفتح: %d • يفضل: %d • ممكن بديل: %d' % (n['crit'], n['imp'], n['ok']), MUTED, 12)]
        if closed:
            lines.append(('⚠ %d مادة لازم تتفتح والقسم مش فاتحها — اطلبها!' % len(closed), RED, 13, True))
        card.add_widget(RLabel(lines))
        for i in items:
            cd = Card(bg=SURFACE, accent=LEVEL_COL[i['level']], pad=10, radius=12)
            cd.add_widget(RLabel([('%s — %s%s' % (i['code'], i['name'], ' (إعادة)' if i['retake'] else ''), None, 14, True),
                                  ('%s • %s • %s' % (i['label'], LEVEL_TXT[i['level']], STATE_TXT[i['state']]),
                                   LEVEL_COL[i['level']], 11),
                                  (i['why'], MUTED, 11)]))
            card.add_widget(cd)
        rq = Btn('نص الطلب الجاهز للقسم', bg=GOLD, fg=DARK, h=48)
        rq.bind(on_release=lambda *a: self.show_request())
        card.add_widget(rq)

    def show_request(self):
        def with_p(p):
            cr = self.crit_cache
            txt = E.dept_request_text(p['cfg'], cr['items'] if cr else [], p['cfg'].get('name', ''))
            if not txt:
                info_popup('طلب للقسم', 'مفيش مقررات حرجة أو مهمة محتاجة طلب خاص — أي مقررات متاحة هتنفع.', size=(0.88, 0.3))
                return
            info_popup('طلب للقسم', txt, [('نسخ', lambda: self.copy_text(txt)), ('مشاركة', lambda: self.share_text(txt))],
                       size=(0.94, 0.85))
        self.with_pack(with_p)

    # ───────────────── ٥) تسجيل ─────────────────
    def reg_key(self):
        return E.tkey(self.set['start_type'], self.set['start_year'])

    def reg_picks(self):
        return set(self.set.setdefault('picks', {}).get(self.reg_key(), [])) & self._reg_ok

    def reg_set_picks(self, s):
        self.set.setdefault('picks', {})[self.reg_key()] = sorted(s)
        self.schedule_save()

    def refresh_reg_total(self, p):
        cfg = p['cfg']
        picks = self.reg_picks()
        tot = sum(C[c].cr for c in picks)
        mx = cfg['cap']
        mn = min(int(cfg.get('min_load') or 0), mx)
        lim = 'الأدنى %d — الأقصى %d' % (mn, mx) if mn else 'الأقصى %d' % mx
        head = ('اخترت %d مادة = %d ساعة  (%s)' % (len(picks), tot, lim), None, 14, True)
        if not picks:
            tail, col = 'اضغط على مادة عشان تختارها', AMBER
        elif tot > mx:
            tail, col = '✘ زيادة %d ساعة عن الأقصى' % (tot - mx), RED
        elif tot < mn:
            tail, col = '⚠ ناقص %d ساعة عن الأدنى' % (mn - tot), AMBER
        else:
            tail, col = '✔ تمام', GREEN
        self._reg_tot.set_lines([head, (tail, col, 14, True)])

    def t_reg(self, box, p):
        cfg, my = p['cfg'], p['my']
        nxt = term_label(cfg['start_type'], cfg['start_year'], cfg.get('months'))
        rec, term = recommended_codes(p)
        valid_rec = term is not None and term['typ'] == cfg['start_type'] and term['year'] == cfg['start_year']
        recs = set(rec) if valid_rec else set()
        self._reg_recs = sorted(recs)
        self._reg_ok = {c.code for c, reasons in p['elig'] if not reasons}
        height = my['height'] if my else {}

        c = Card()
        c.add_widget(ALabel('الفصل اللي بتسجّل فيه: %s' % nxt, size=15, bold=True, color=GOLD))
        c.add_widget(ALabel('الموصى بيه: %d مادة (%d ساعة)' % (len(recs), sum(C[x].cr for x in recs)), size=13, color=TEAL))
        notes = []
        off = term_offers(cfg, cfg['start_type'], cfg['start_year'])
        if off is not None:
            notes.append('القسم فاتح %d مادة في الفصل ده — اختار منهم بس.' % len(off))
        if p['an']['probation']:
            notes.append('معدلك أقل من 2.00: أقصى حد %d ساعة.' % PROBATION_LOAD)
        if my and my['terms'] and not valid_rec:
            notes.append('خطتك ما فيهاش مواد في %s — شوف تبويب «خطتي».' % nxt)
        notes.append('أخضر = موصى بيها • أزرق = متاحة • رمادي = مش متاحة (مكتوب السبب).')
        c.add_widget(ALabel('\n'.join(notes), size=11, color=MUTED))
        box.add_widget(c)

        tc = Card(bg=CARD2)
        self._reg_tot = RLabel([('', None, 14, True)], halign='center')
        tc.add_widget(self._reg_tot)
        box.add_widget(tc)

        a = Btn('اختار الموصى بيه', bg=GOLD, fg=DARK, h=44, size=12)
        d = Btn('مسح اختياراتي', h=44, size=12)
        cp = Btn('نسخ / مشاركة', bg=TEAL, fg=INK, h=44, size=12, bold=True)

        def pick_rec(*x):
            self.reg_set_picks(set(self._reg_recs) & self._reg_ok)
            self.show_tab(4)

        def clear(*x):
            self.reg_set_picks(set())
            self.show_tab(4)
        a.bind(on_release=pick_rec)
        d.bind(on_release=clear)
        cp.bind(on_release=lambda *x: self.copy_register())
        box.add_widget(hrow(cp, d, a, h=44))

        picks = self.reg_picks()
        rows = []
        for cr_, reasons in p['elig']:
            if cr_.code in recs:
                state, order = 'rec', 0
            elif not reasons:
                state, order = 'ok', 1
            else:
                state, order = 'no', 2
            h = height.get(cr_.code, 0)
            prio = 'لازم' if h >= 4 else ('مهمة' if h >= 2 else '')
            why = '؛ '.join(reasons) if reasons else ('مطلوبة للتخرج' if cr_.kind == 'R' else (
                'ضمن اختيارات خطتك' if my and cr_.code in my['chosen'] else 'اختيارية'))
            if p['st'].failed(cr_.code):
                why = 'راسب فيها — لازم تعيدها. ' + why
                prio = 'لازم'
            rows.append((order, 0 if prio == 'لازم' else 1, cr_.sem, cr_.code, cr_, state, prio, why))
        rows.sort(key=lambda r: r[:4])
        self.paged(box, 'reg', rows, lambda r: self.reg_row(p, r[4], r[5], r[6], r[7], r[4].code in picks))
        self.refresh_reg_total(p)

    def reg_lines(self, c, state, prio, why, picked):
        sym = '☑' if picked else ('☐' if state != 'no' else '•')
        tag = {'rec': 'موصى بيها', 'ok': 'متاحة', 'no': 'مش متاحة'}[state]
        mc = {'rec': GREEN, 'ok': BLUE, 'no': MUTED}[state]
        return [(sym + '  ' + c.name, GOLD if picked else (MUTED if state == 'no' else None), 15, True),
                ('%s • %d ساعة • %s • %s — %s%s' % (c.code, c.cr, tag, 'إجباري' if c.kind == 'R' else 'اختياري',
                                                  KIND_TXT[c.grp], (' • أولوية: ' + prio) if prio else ''), mc, 11),
                (why, MUTED, 11)]

    def reg_row(self, p, c, state, prio, why, picked):
        bg = {'rec': GREEN_BG, 'ok': BLUE_BG, 'no': SURFACE}[state]
        acc = {'rec': GREEN, 'ok': BLUE, 'no': CARD2}[state]
        card = TapCard(bg=PICK_BG if picked else bg, accent=GOLD if picked else acc, pad=10, radius=14)
        rl = RLabel(self.reg_lines(c, state, prio, why, picked))
        card.add_widget(rl)
        if state == 'no':
            return card

        def tap(*a):
            s = self.reg_picks()
            s.symmetric_difference_update({c.code})
            self.reg_set_picks(s)
            on = c.code in s
            card.set_bg(PICK_BG if on else bg)
            card.set_accent(GOLD if on else acc)
            rl.set_lines(self.reg_lines(c, state, prio, why, on))
            self.refresh_reg_total(p)
        card.bind(on_release=tap)
        return card

    def copy_register(self):
        codes = sorted(self.reg_picks()) or self._reg_recs
        if not codes:
            info_popup('تنبيه', 'لسه ما اخترتش مواد.', size=(0.85, 0.28))
            return
        txt = 'موادي للتسجيل:\n' + '\n'.join('%s — %s (%d)' % (c, C[c].name, C[c].cr) for c in codes)
        info_popup('موادي', txt, [('نسخ', lambda: self.copy_text(txt)), ('مشاركة', lambda: self.share_text(txt))],
                   size=(0.92, 0.75))

    # ───────────────── ٦) خطتي ─────────────────
    def t_plan(self, box):
        box.add_widget(seg([('plans', 'الخطط'), ('tracks', 'المسارات'), ('goal', 'هدف المعدل')], self.plan_sub,
                           lambda k: (setattr(self, 'plan_sub', k), self.show_tab(5, top=True))))
        if self.plan_sub == 'plans':
            self.t_plans(box)
        elif self.plan_sub == 'goal':
            self.t_goal(box)
        else:
            self.t_tracks(box)

    # ───────────────── هدف المعدل: أجيب كام في كل مادة؟ ─────────────────
    GOAL_PRESETS = [2.0, 2.5, 3.0, 3.3, 3.5, 3.7, 4.0]
    GOAL_LETTER = {2.0: 'C', 3.0: 'B', 3.3: 'B+', 3.7: 'A-', 4.0: 'A'}

    def t_goal(self, box):
        s = self.set
        goal = float(s.get('goal_gpa') or 3.3)
        c = Card()
        c.add_widget(sec('عايز تتخرج بمعدل كام؟'))
        c.add_widget(ALabel('اختار هدفك (A- = 3.7 • B+ = 3.3 وهو حد مرتبة الشرف) أو اكتب معدل تاني:', size=12, color=MUTED))
        sel = '%.2f' % goal
        c.add_widget(chips([('%.2f' % v, '%.1f%s' % (v, ('  ' + self.GOAL_LETTER[v]) if v in self.GOAL_LETTER else '')) for v in self.GOAL_PRESETS], sel,
                           lambda k: (s.__setitem__('goal_gpa', float(k)), self.schedule_save(), self.show_tab(5, top=True))))
        typed = {'v': ''}
        inp = ArInput(hint='معدل تاني (من 1 لـ 4) مثال: 3.45', numeric=True, on_text=lambda v: typed.__setitem__('v', v))

        def apply_custom(*a):
            try:
                v = float(typed['v'])
            except ValueError:
                info_popup('تنبيه', 'اكتب رقم صحيح بين 1 و 4.', size=(0.8, 0.25))
                return
            if not 1.0 <= v <= 4.0:
                info_popup('تنبيه', 'المعدل لازم يكون بين 1 و 4.', size=(0.8, 0.25))
                return
            s['goal_gpa'] = round(v, 2)
            self.schedule_save()
            self.show_tab(5, top=True)
        ok = Btn('احسب', bg=GOLD, fg=DARK, size=13, h=46, size_hint_x=None, width=dp(68))
        ok.bind(on_release=apply_custom)
        inp.ti.bind(on_text_validate=apply_custom)
        c.add_widget(hrow(ok, inp, h=46))
        c.add_widget(ALabel('هدفك الحالي: %.2f' % goal, size=15, bold=True, color=TEAL, halign='center'))
        box.add_widget(c)
        sv = self._sv
        self.with_pack(lambda p: self._goal_fill(box, sv, p, goal))

    def _goal_fill(self, box, sv, p, goal):
        if self.tab != 5 or sv is not self._sv or self.plan_sub != 'goal':
            return
        try:
            r = E.goal_plan(p, goal)
            self._goal_cards(box, p, r, goal)
        except Exception:
            import traceback
            box.add_widget(ALabel('حصل خطأ:\n' + traceback.format_exc()[-600:], size=11, color=RED))

    def _goal_cards(self, box, p, r, goal):
        base = r['base_gpa']
        if r['empty']:
            c = Card(bg=BLUE_BG, accent=BLUE)
            c.add_widget(ALabel('مفيش مواد متبقية في الخطة — معدلك النهائي ' + ('%.2f' % base if base is not None else '—') +
                                '. ' + ('✔ محقق هدفك.' if base is not None and base >= goal - 1e-9 else
                                        'مش هتقدر ترفعه غير بإعادة مواد (اتكلم مع المرشد الأكاديمي).'),
                                size=13, bold=True, color=GOLD))
            box.add_widget(c)
            return
        c = Card()
        c.add_widget(sec('وضعك الحالي'))
        lines = []
        if base is not None:
            lines.append(('معدلك الحالي: %.2f  (على %d ساعة%s)' % (base, r['base_hours'], ' — معدل مدخل يدوي' if r['manual'] else ''),
                          None, 14, True))
        else:
            lines.append(('لسه مفيش تقديرات مدخلة — الحساب هيبدأ من الصفر.', AMBER, 13, True))
        lines.append(('الباقي: %d مادة = %d ساعة (من خطتك الحالية + اللي بتدرسه الآن)' % (r['n'], r['hours']), MUTED, 12))
        lines.append(('أقصى معدل ممكن لو جبت أعلى تقدير في كل الباقي: %.2f' % r['max_gpa'], MUTED, 12))
        c.add_widget(RLabel(lines))
        box.add_widget(c)

        c = Card(bg=GREEN_BG if r['feasible'] else RED_BG, accent=GREEN if r['feasible'] else RED)
        if not r['feasible']:
            c.add_widget(RLabel([('✘ مش ممكن توصل %.2f' % goal, RED, 16, True),
                                 ('أقصى معدل تقدر توصله %.2f. جرّب هدف أقل. وفي كل الأحوال الراسب بيتحسب له C كحد أقصى لما يعيد.'
                                  % r['max_gpa'], MUTED, 12)]))
        else:
            na = r['need_avg']
            head = '✔ ممكن توصل %.2f' % goal
            if na <= 1.0:
                sub = 'أي نجاح في الباقي بيحققه — بس خلّي بالك من شرط C- للمواد المطلوبة كمتطلب سابق.'
            else:
                sub = 'محتاج متوسط حوالي %.2f نقطة في باقي المواد (يعني %s تقريباً).' % (na, self._letter_for(na))
            dist = {}
            for it in r['items']:
                n_, h_ = dist.get(it['letter'], (0, 0))
                dist[it['letter']] = (n_ + 1, h_ + it['cr'])
            order = [l for l, _g in reversed(E.GRADE_STEPS)]
            parts = ['%s في %d مادة (%d ساعة)' % (l, dist[l][0], dist[l][1]) for l in order if l in dist]
            c.add_widget(RLabel([(head, GREEN, 16, True), (sub, None, 13, False),
                                 ('التوزيع المطلوب (أقل حاجة تحقق هدفك):', GOLD, 13, True)] +
                                [('• ' + t, None, 13, False) for t in parts] +
                                [('المعدل المتوقع بالتوزيع ده: %.2f' % r['final_gpa'], TEAL, 13, True)]))
        box.add_widget(c)

        notes = ['ده أدنى توزيع يحقق هدفك — لو جبت أعلى في مادة، تقدر تنزل في مادة تانية.',
                 'المواد اللي متطلب لمواد تانية لازم C- على الأقل.',
                 'الراسب لما يعيد المقرر بيتحسب له C كحد أقصى (حسب اللائحة).']
        if goal >= 3.3 and p['an']['fail']:
            notes.append('⚠ مرتبة الشرف في اللائحة بشرط ما تكونش رسبت في أي مقرر — وإنت راسب في: ' +
                         '، '.join(x.name for x in p['an']['fail']))
        elif goal >= 3.3:
            notes.append('مرتبة الشرف (٣٫٣ فأكثر) بشرط ما ترسبش في أي مقرر.')
        nc = Card(bg=CARD2)
        nc.add_widget(RLabel([(t, MUTED, 11, False) for t in notes]))
        box.add_widget(nc)

        box.add_widget(sec('كام أجيب في كل مادة؟'))
        groups = []
        for it in r['items']:
            if not groups or groups[-1][0] != it['label']:
                groups.append((it['label'], []))
            groups[-1][1].append(it)
        for label, its in groups:
            cd = Card(accent=CARD2, pad=12)
            lines = [('%s  —  %d ساعة' % (label, sum(i['cr'] for i in its)), GOLD, 14, True)]
            for it in its:
                lines.append(('• %s (%d)%s   ←   %s' % (it['name'], it['cr'], ' (إعادة)' if it['retake'] else '', it['letter']),
                              None, 13, False))
            cd.add_widget(RLabel(lines))
            box.add_widget(cd)

    @staticmethod
    def _letter_for(avg):
        best = E.GRADE_STEPS[-1][0]
        for l, g in E.GRADE_STEPS:
            if g >= avg - 1e-9:
                return l
        return best

    def compute_plans(self):
        def with_p(p):
            def done(res):
                self.plans = res
                self._plans_tried = True
                self.plan_sel = res[0][0] if res else None
                if self.tab == 5:
                    self.show_tab(5)
            self.run_async(lambda: E.preset_plans(p['st'], p['cfg'], p['prefs']), done)
        self.with_pack(with_p)

    def t_plans(self, box):
        if not self.plans and not self._plans_tried:
            self.compute_plans()
            return
        b = Btn('إعادة حساب الخطط', bg=GOLD, fg=DARK, h=46)
        b.bind(on_release=lambda *a: self.compute_plans())
        box.add_widget(b)
        if not self.plans:
            box.add_widget(ALabel('تعذّر بناء خطط — راجع المقررات والإعدادات.', size=13, color=RED))
            return
        fast = next((x for x in self.plans if x[0] == 'fast'), None)
        nos = next((x for x in self.plans if x[0] == 'nosum'), None)
        txt = ''
        if fast and nos:
            fp, np_ = fast[4], nos[4]
            if not fp['terms']:
                txt = 'خلّصت كل المقررات — مفيش حاجة تتسجل.'
            elif fp['finish_key'] < np_['finish_key']:
                sm = ['%s (%s)' % (t['label'], '، '.join(C[c].name for c in t['codes'])) for t in fp['terms']
                      if t['typ'] == 'U' and t['codes']]
                txt = 'الصيفي هيخليك تتخرج %s بدل %s.\nالصيفي المطلوب: %s' % (fp['finish_label'], np_['finish_label'], ' | '.join(sm))
            else:
                txt = 'مش محتاج صيفي: بتتخرج %s بالحمل الأقصى سواء نزلت صيفي أو لأ.' % fp['finish_label']
        if txt:
            c = Card(bg=BLUE_BG, accent=BLUE)
            c.add_widget(ALabel(txt, size=13, bold=True, color=GOLD))
            box.add_widget(c)
        for k, n, cap, s_, pl in self.plans:
            on = k == self.plan_sel
            cd = TapCard(bg=GREEN_BG if on else SURFACE, accent=GOLD if on else CARD2, pad=12)
            cd.add_widget(RLabel([(n, GOLD if on else None, 15, True),
                                  ('التخرج: %s • %d فصل • %d صيفي' % (pl['finish_label'], pl['n_terms'], pl['n_summers']), MUTED, 12)]))
            cd.bind(on_release=lambda w, k=k: (setattr(self, 'plan_sel', k), self.show_tab(5)))
            box.add_widget(cd)
        sel = next((x for x in self.plans if x[0] == self.plan_sel), self.plans[0])
        pl = sel[4]
        box.add_widget(sec('جدول الفصول — ' + sel[1]))
        if not pl['terms']:
            box.add_widget(ALabel('خلّصت كل المتطلبات', size=13, color=GREEN))
            return
        for t in pl['terms']:
            cd = Card(bg=AMBER_BG if t['typ'] == 'U' else SURFACE, accent=AMBER if t['typ'] == 'U' else CARD2, pad=12)
            if not t['codes']:
                lines = [(t['label'], MUTED, 14, True),
                         ('فصل انتظار — مفيش مواد متاحة (بتتفتح في فصل تاني أو القسم مش فاتحها)', MUTED, 11)]
            else:
                lines = [('%s  —  %d ساعة' % (t['label'], t['credits']), GOLD, 14, True)]
                for c in t['codes']:
                    tag = (' (إعادة)' if c in t['retake'] else '') + (' (إضافي)' if c in t.get('extra', ()) else '')
                    lines.append(('• %s%s (%d)' % (C[c].name, tag, C[c].cr), None, 13, False))
            cd.add_widget(RLabel(lines))
            box.add_widget(cd)

    def compute_tracks(self):
        def with_p(p):
            def done(res):
                self.tracks = res
                self.track_sel = res[0]['key'] if res else None
                if self.tab == 5:
                    self.show_tab(5)
            self.run_async(lambda: E.track_report(p['st'], p['cfg']), done)
        self.with_pack(with_p)

    def t_tracks(self, box):
        cur = next((t[1] for t in E.TRACKS if t[0] == self.set.get('track', 'auto')), 'تلقائي (الأسرع)')
        box.add_widget(ALabel('المسار الحالي: ' + cur, size=13, bold=True, color=TEAL))
        b = Btn('قارن المسارات', bg=GOLD, fg=DARK, h=46)
        b.bind(on_release=lambda *a: self.compute_tracks())
        box.add_widget(b)
        if not self.tracks:
            box.add_widget(ALabel('اضغط «قارن المسارات» عشان تشوف أسرع مسار اختياري ليك.', size=12, color=MUTED))
            return
        p = self.cache
        best = min(r['plan']['finish_key'] for r in self.tracks)
        if p and p['my'] and p['my']['chain']:
            box.add_widget(ALabel('المسار الحرج (أطول سلسلة متطلبات): %s = %d فصل على الأقل' % (
                E.chain_names(p['my']['chain']), len(p['my']['chain'])), size=11, color=MUTED))
        for r in self.tracks:
            pl = r['plan']
            on = r['key'] == self.track_sel
            cd = TapCard(bg=GREEN_BG if pl['finish_key'] == best else SURFACE, accent=GOLD if on else CARD2, pad=12)
            cd.add_widget(RLabel([(r['name'] + ('   ◀' if on else ''), GOLD if on else None, 15, True),
                                  ('التخرج: %s • %d فصل • %d صيفي' % (pl['finish_label'], pl['n_terms'], pl['n_summers']), MUTED, 12)]))
            cd.bind(on_release=lambda w, k=r['key']: (setattr(self, 'track_sel', k), self.show_tab(5)))
            box.add_widget(cd)
        r = next((x for x in self.tracks if x['key'] == self.track_sel), self.tracks[0])
        st = p['st'] if p else Student(self.rec)
        lines = [(r['name'], GOLD, 15, True), (r['desc'], MUTED, 12)]
        if r['courses']:
            lines.append(('مقررات المسار:', TEAL, 13, True))
            for c in r['courses']:
                mark = '✔ خلصته' if (st.passed(c) or st.cur(c)) else ('● هتدرسه في الخطة' if c in r['plan']['chosen'] else '○ اختياري')
                lines.append(('%s  %s  (%d ساعة) — %s' % (mark, C[c].name, C[c].cr, KIND_TXT[C[c].grp]), None, 12, False))
        lines.append(('الاختياري اللي هتدرسه في هذا المسار:', TEAL, 13, True))
        for c in r['chosen']:
            lines.append(('• %s (%d)' % (C[c].name, C[c].cr), None, 12, False))
        d = Card(bg=CARD2)
        d.add_widget(RLabel(lines))
        box.add_widget(d)
        ad = Btn('اعتمد المسار ده واحسب خطتي', bg=GOLD, fg=DARK, h=50)
        ad.bind(on_release=lambda *a: self.adopt_track(r['key']))
        box.add_widget(ad)

    def adopt_track(self, key):
        self.set['track'] = key
        self.changed()
        self.plan_sub = 'plans'
        self.show_tab(5)
