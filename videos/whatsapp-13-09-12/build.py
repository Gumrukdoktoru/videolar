#!/usr/bin/env python3
"""Build the talking-head-recut composition for the 13.09.12 video.

Writes storyboard.json, public/cards/card-XX.html and public/index.html.
Every animation time below is an absolute second taken from transcript.json
(word start times), so each effect lands on the word it illustrates.
Run from anywhere: python3 videos/whatsapp-13-09-12/build.py
"""
import json
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public")
FPS = 30
W, H = 1080, 1920
DUR = 58.68  # clamped to the source video duration (58.689s)


def q(t):
    """Quantize an absolute time to the frame grid."""
    return round(round(t * FPS) / FPS, 4)


# ───────────────────────── card spec helpers ─────────────────────────
class Card:
    def __init__(self, cid, start, end, intent, accent, hints, theme="paper"):
        self.id, self.start, self.end = cid, start, end
        self.intent, self.accent, self.hints, self.theme = intent, accent, hints, theme
        self.parts = []   # html snippets inside .panel
        self.anims = []   # (selector-suffix, kind, abs_at, duration, params)
        self.css = ""
        self.nstrip = 0

    def add(self, thunk, cls="", lead=0.06):
        """Wrap one content block in its own background strip that appears
        just before the first animation inside it (i.e. when it is spoken)."""
        mark = len(self.anims)
        html = thunk()
        times = [a[2] for a in self.anims[mark:]]
        at = max(self.start, min(times) - lead) if times else self.start
        sid = f"{self.id}-s{self.nstrip}"
        self.nstrip += 1
        self.parts.append(self.el("div", sid, ("strip " + cls).strip(), html, "slide-in", at, 0.32,
                                  **{"from": "bottom", "distance": 28}))

    def anim(self, el_id, kind, at, dur, **p):
        self.anims.append((el_id, kind, at, dur, p))

    def attrs(self, kind, at, dur, **p):
        a = f'data-anim="{kind}" data-anim-at="{q(at - self.start)}" data-anim-duration="{dur}"'
        for k, v in p.items():
            v = json.dumps(v) if isinstance(v, (dict, list)) else v
            a += f" data-anim-{k.replace('_', '-')}='{v}'"
        return a

    def el(self, tag, el_id, cls, inner, kind=None, at=None, dur=0.4, style="", **p):
        a = ""
        if kind:
            a = " " + self.attrs(kind, at, dur, **p)
            self.anim(el_id, kind, at, dur, **p)
        st = f' style="{style}"' if style else ""
        return f'<{tag} id="{el_id}" class="{cls}"{st}{a}>{inner}</{tag}>'

    def words(self, el_id, cls, words, red=()):
        """A line whose words appear exactly when they are spoken."""
        out = []
        for i, (txt, t) in enumerate(words):
            wid = f"{el_id}-w{i}"
            c = "w red" if i in red else "w"
            out.append(self.el("span", wid, c, escape(txt), "slide-in", t, 0.28,
                               **{"from": "bottom", "distance": 22}))
        return f'<div id="{el_id}" class="{cls}">' + " ".join(out) + "</div>"

    def kinetic(self, el_id, cls, text, at, stagger=0.025, red_words=()):
        """Per-character pop; each word wrapped so lines only break between words."""
        ws = []
        for wi, word in enumerate(text.split(" ")):
            chars = "".join(f'<span class="char">{escape(c)}</span>' for c in word)
            c = "word red" if wi in red_words else "word"
            ws.append(f'<span class="{c}">{chars}</span>')
        a = self.attrs("kinetic-chars", at, 0.42, stagger=stagger, pattern="pop")
        self.anim(el_id, "kinetic-chars", at, 0.42, stagger=stagger)
        return f'<div id="{el_id}" class="{cls}" {a}>' + " ".join(ws) + "</div>"

    def meta(self, label, num):
        rule = self.el("div", f"{self.id}-rule", "rule", "", "grow-x", self.start + 0.12, 0.5,
                       target_w=PANEL_INNER)
        m = self.el("div", f"{self.id}-meta", "meta",
                    f'<span>{escape(label)}</span><span class="num">{num} / 08</span>',
                    "fade-in", self.start + 0.3, 0.35)
        self.parts.append(f'<div class="strip meta-strip">{rule}{m}</div>')


PANEL_W = 912
PANEL_PAD = 28
PANEL_INNER = PANEL_W - 2 * PANEL_PAD

cards = []

# 01 ── greeting ─────────────────────────────────────────────────────
c = Card("card-01", 0.15, 6.45, "Open with the greeting and wish good luck to everyone sitting the exam",
         0, {"kicker": "SINAV DUYURUSU", "title": "Hayırlı uğurlu olsun!",
             "detail": "Tüm meslektaşlarıma, sınava girecek arkadaşlarıma"})
c.meta("SINAV DUYURUSU", "01")
c.add(lambda: c.words("card-01-hello", "eyebrow", [("Herkese", 0.25), ("merhaba", 0.4), ("arkadaşlar", 0.6)]))
c.add(lambda: c.words("card-01-who", "body", [("Tüm", 1.64), ("meslektaşlarıma,", 2.12), ("sınava", 3.04),
                                              ("girecek", 3.36), ("arkadaşlarıma", 3.64)], red=(1, 4)))
c.add(lambda: c.kinetic("card-01-title", "title", "Hayırlı uğurlu olsun!", 4.38, red_words=(1,)))
cards.append(c)

# 02 ── exam date published → application dates matter ─────────────
c = Card("card-02", 6.85, 14.95, "Exam date is out; what matters now is the application window",
         1, {"kicker": "SINAV TAKVİMİ", "title": "Sınav tarihi yayınlandı",
             "focus": "Başvuru tarihleri"})
c.meta("SINAV TAKVİMİ", "02")
c.add(lambda: '<div class="row">'
      + c.kinetic("card-02-title", "title", "Sınav tarihi", 6.9)
      + c.el("div", "card-02-stamp", "slab", "YAYINLANDI", "scale-pop", 7.78, 0.45,
             from_scale=1.9, rotate=-4)
      + "</div>")
c.add(lambda: c.el("div", "card-02-label", "label red-ink", "DİKKAT ETMEMİZ GEREKEN", "fade-in", 9.66, 0.35))
c.add(lambda: c.kinetic("card-02-focus", "title xl", "Başvuru tarihleri", 13.14, stagger=0.03, red_words=(1,))
      + c.el("div", "card-02-line", "underline", "", "grow-x", 14.18, 0.45, target_w=720))
cards.append(c)

# 03 ── Hacettepe system + 19 → 30 Ekim ───────────────────────────────
c = Card("card-03", 15.15, 22.75, "Where and when: Hacettepe exam system, 19 to 30 October",
         0, {"kicker": "BAŞVURU", "title": "Hacettepe Üniversitesi",
             "data": {"start": "19 Ekim", "end": "30 Ekim", "days": 12}})
c.meta("BAŞVURU NEREDEN?", "03")
c.add(lambda: c.kinetic("card-03-title", "title", "Hacettepe Üniversitesi", 15.24, stagger=0.02))
c.add(lambda: c.words("card-03-sub", "body", [("sınav", 16.7), ("sisteminden", 17.08), ("giriş", 17.52),
                                              ("yapılacak", 17.88)]))


def dates_row(card):
    arrow = ('<svg class="arrow" viewBox="0 0 120 40" width="120" height="40">'
             + card.el("path", "card-03-arrow", "arrow-path", "", "draw-path", 20.3, 0.45)
             .replace('<path ', '<path d="M4 20 H104 M88 6 L106 20 L88 34" ')
             + "</svg>")
    return ('<div class="dates">'
            + card.el("div", "card-03-d1", "date",
                      '<b>19</b><span>EKİM</span><small>BAŞLANGIÇ</small>', "scale-pop", 18.46, 0.42)
            + arrow
            + card.el("div", "card-03-d2", "date",
                      '<b>30</b><span>EKİM</span><small>BİTİŞ</small>', "scale-pop", 20.76, 0.42)
            + card.el("div", "card-03-days", "chip",
                      '<b id="card-03-n">0</b> GÜN', "slide-in", 21.8, 0.35,
                      **{"from": "right", "distance": 40})
            + "</div>")


c.add(lambda: dates_row(c), "wide")
c.anim("card-03-n", "count-up", 21.85, 0.6, **{"from": 0, "to": 12, "format": ",d"})
cards.append(c)

# 04 ── daily reminders + how-to videos ─────────────────────────────
c = Card("card-04", 22.85, 29.0, "We will remind you every day and share how-to-apply videos",
         2, {"kicker": "SİZE DESTEK", "checklist": ["Her gün hatırlatma", "Başvuru anlatım videoları"]})


def check_row(card, n, text, t_text, t_tick):
    tick = ('<svg viewBox="0 0 48 48" width="48" height="48">'
            + card.el("path", f"card-04-tick{n}", "tick", "", "draw-path", t_tick, 0.35)
            .replace('<path ', '<path d="M10 25 L20 35 L39 13" ')
            + "</svg>")
    return card.el("div", f"card-04-row{n}", "check", f'<span class="box">{tick}</span>'
                   f'<span class="ctext">{escape(text)}</span>', "slide-in", t_text, 0.4,
                   **{"from": "left", "distance": 60})


c.meta("SİZİN İÇİN", "04")
c.add(lambda: c.words("card-04-lead", "eyebrow", [("Sizlere", 22.9), ("tabii", 23.34), ("ki", 23.54)]))
c.add(lambda: check_row(c, 1, "Her gün hatırlatma", 23.9, 24.74))
c.add(lambda: check_row(c, 2, "Başvuru anlatım videoları", 26.12, 27.7))
c.add(lambda: c.el("div", "card-04-foot", "label", "SİZLERE İLETECEĞİZ →", "fade-in", 28.1, 0.35))
cards.append(c)

# 05 ── don't all rush on day one, the system will lock ─────────────
c = Card("card-05", 29.1, 35.95, "Request: don't all upload on day one, the system will lock",
         1, {"kicker": "RİCAM", "title": "Hep beraber yüklenmeyelim", "warning": "Sistem kilitlenecek"},
         theme="red")
c.meta("SİZLERDEN RİCAM", "05")
c.add(lambda: c.words("card-05-when", "body", [("İlk", 30.34), ("gün", 30.86), ("sistem", 31.14),
                                               ("açıldığında", 31.56)]))
c.add(lambda: c.kinetic("card-05-title", "title", "Hep beraber yüklenmeyelim.", 32.36, stagger=0.02))
c.add(lambda: '<div class="row">'
      + c.el("div", "card-05-time", "chip ghost", "ZAMANIMIZ VAR", "fade-in", 33.8, 0.3)
      + c.el("div", "card-05-warn", "slab ink",
             '<svg viewBox="0 0 40 36" width="44" height="40"><path d="M20 2 L38 34 H2 Z" '
             'fill="none" stroke="#fff" stroke-width="4" stroke-linejoin="round"/>'
             '<path d="M20 13 V23 M20 27 V29" stroke="#fff" stroke-width="4" stroke-linecap="round"/></svg>'
             'SİSTEM KİLİTLENECEK', "slide-in", 34.76, 0.3, **{"from": "right", "distance": 80})
      + "</div>")
c.anim("card-05-warn", "morph-to", 35.14, 0.45,
       props={"keyframes": {"x": [0, -16, 14, -10, 7, -3, 0]}})
cards.append(c)

# 06 ── past experience → calm, patient ─────────────────────────────
c = Card("card-06", 36.3, 45.85, "From past experience there will be small glitches; stay calm and patient",
         4, {"kicker": "GEÇMİŞ DÖNEM TECRÜBESİ", "title": "Küçük küçük hatalar olacak",
             "mantra": ["Sakin", "Sabırlı", "Bekleyelim"]}, theme="ink")
c.meta("GEÇMİŞ DÖNEM TECRÜBESİ", "06")
n0 = len(c.parts)
c.add(lambda: c.words("card-06-past", "body", [("Geçmiş", 36.3), ("dönemlerin", 36.98), ("tecrübesi:", 37.38)]))
c.add(lambda: c.kinetic("card-06-err", "title", "Küçük küçük hatalar olacak.", 38.86, stagger=0.02,
                        red_words=(2,)))
stage_a, c.parts = c.parts[n0:], c.parts[:n0]
c.add(lambda: c.words("card-06-so", "body", [("Onun", 40.28), ("için", 40.62), ("ilk", 40.86), ("gün", 41.12),
                                             ("yüklenmeyelim.", 42.22)]))
c.add(lambda: '<div class="mantra">'
      + c.el("div", "card-06-m1", "mword", "Sakin.", "scale-pop", 43.12, 0.4)
      + c.el("div", "card-06-m2", "mword", "Sabırlı.", "scale-pop", 44.22, 0.4)
      + c.el("div", "card-06-m3", "mword red", "Bekleyelim.", "scale-pop", 45.12, 0.4)
      + "</div>")
stage_b, c.parts = c.parts[n0:], c.parts[:n0]
c.parts.append('<div class="stage-a" id="card-06-a">' + "".join(stage_a) + "</div>")
c.parts.append('<div class="stage-b" id="card-06-b">' + "".join(stage_b) + "</div>")
c.anim("card-06-a", "fade-out", 40.0, 0.25)
c.anim("card-06-b", "fade-in", 40.18, 0.2)
cards.append(c)

# 07 ── 19 Ekim, day one we don't upload ─────────────────────────────
c = Card("card-07", 45.95, 51.0, "Applications open 19 October; we don't upload on day one",
         1, {"kicker": "HATIRLATMA", "title": "19 Ekim", "stamp": "İlk gün yüklenmiyoruz"})
c.meta("HATIRLATMA", "07")
c.add(lambda: c.el("div", "card-07-date", "big", '<span class="red">19</span> EKİM', "scale-pop", 46.0, 0.45))
c.add(lambda: c.words("card-07-open", "body", [("başvurular", 47.64), ("başlıyor", 48.18)]))
c.add(lambda: c.el("div", "card-07-stamp", "stamp", "İLK GÜN<br/>YÜKLENMİYORUZ", "scale-pop", 49.98, 0.4,
                   from_scale=2.2, rotate=-6), "stamp-strip")
cards.append(c)

# 08 ── we'll keep you posted moment by moment ──────────────────────
c = Card("card-08", 51.05, DUR, "Close: we'll keep you informed at every step",
         3, {"kicker": "TAKİPTE KALIN", "title": "An be an", "detail": "bütün süreçlerden bilgilendireceğiz"},
         theme="ink")
bell = ('<svg viewBox="0 0 64 64" width="88" height="88"><path d="M32 8c-10 0-17 8-17 18v12l-6 8h46l-6-8V26'
        'c0-10-7-18-17-18z" fill="#e8190f"/><circle cx="32" cy="52" r="6" fill="#e8190f"/></svg>')
c.meta("TAKİPTE KALIN", "08")
c.add(lambda: '<div class="row">'
      + c.kinetic("card-08-title", "title xl", "An be an", 51.94, stagger=0.04)
      + c.el("div", "card-08-bell", "bell", bell, "scale-pop", 52.3, 0.4)
      + "</div>")
c.add(lambda: c.words("card-08-all", "body", [("bütün", 52.62), ("süreçlerden", 52.86),
                                              ("bilgilendireceğiz.", 55.68)], red=(2,)))
c.anim("card-08-bell", "morph-to", 53.0, 1.1,
       props={"keyframes": {"rotation": [0, 22, -18, 12, -8, 4, 0]}})
cards.append(c)


# ───────────────────────── card CSS ─────────────────────────
def card_css(cid, theme):
    s = f'.card[data-card-id="{cid}"]'
    bg, ink, muted = {"paper": ("#ffffff", "#111111", "#555555"),
                      "red": ("#e8190f", "#ffffff", "rgba(255,255,255,.82)"),
                      "ink": ("#111111", "#ffffff", "rgba(255,255,255,.7)")}[theme]
    red = "#111111" if theme == "red" else "#e8190f"
    return f"""
{s} .root {{ position:absolute; inset:0; background:transparent; }}
{s} .panel {{ position:absolute; left:48px; bottom:320px; width:{PANEL_W}px; color:{ink};
  font-family:'Inter', sans-serif; display:flex; flex-direction:column; align-items:flex-start; }}
{s} .strip {{ background:{bg}; padding:16px {PANEL_PAD}px 18px; max-width:{PANEL_W}px; box-sizing:border-box;
  box-shadow:0 22px 50px -24px rgba(0,0,0,.6); }}
{s} .strip.meta-strip {{ width:{PANEL_W}px; padding:22px {PANEL_PAD}px 14px; }}
{s} .strip.wide {{ width:{PANEL_W}px; padding-bottom:26px; }}
{s} .strip.stamp-strip {{ padding:26px {PANEL_PAD}px 30px; }}
{s} .rule {{ height:6px; width:0; background:{ink}; }}
{s} .meta {{ display:flex; justify-content:space-between; font:800 21px/1 'Inter', sans-serif;
  letter-spacing:.2em; color:{ink}; margin-top:12px; }}
{s} .meta .num {{ color:{red}; }}
{s} .eyebrow {{ font:600 30px/1.2 'Inter', sans-serif; color:{muted}; }}
{s} .body {{ font:600 38px/1.25 'Inter', sans-serif; color:{muted}; }}
{s} .w {{ display:inline-block; }}
{s} .red {{ color:{red}; }}
{s} .title {{ font:900 92px/0.98 'Inter', sans-serif; letter-spacing:-.035em; color:{ink}; }}
{s} .title.xl {{ font-size:112px; }}
{s} .word {{ display:inline-block; white-space:nowrap; }}
{s} .word.red {{ color:{red}; }}
{s} .char {{ display:inline-block; }}
{s} .row {{ display:flex; align-items:center; gap:24px; flex-wrap:wrap; }}
{s} .slab {{ display:inline-flex; align-items:center; gap:14px; background:{red}; color:#fff;
  padding:16px 22px; font:900 40px/1 'Inter', sans-serif; letter-spacing:.02em; }}
{s} .slab.ink {{ background:#111111; }}
{s} .label {{ font:800 22px/1 'Inter', sans-serif; letter-spacing:.2em; color:{muted}; }}
{s} .label.red-ink {{ color:{red}; }}
{s} .underline {{ height:12px; width:0; background:{red}; margin-top:-8px; }}
{s} .dates {{ display:flex; align-items:center; gap:18px; margin-top:4px; }}
{s} .date {{ background:#111111; color:#fff; padding:14px 22px 16px; display:flex; flex-direction:column;
  align-items:flex-start; min-width:178px; }}
{s} .date b {{ font:900 92px/0.9 'Inter', sans-serif; letter-spacing:-.04em; color:#fff; }}
{s} .date span {{ font:900 32px/1.1 'Inter', sans-serif; letter-spacing:.08em; color:#e8190f; }}
{s} .date small {{ font:800 16px/1 'Inter', sans-serif; letter-spacing:.2em; color:rgba(255,255,255,.7); margin-top:6px; }}
{s} .arrow-path {{ fill:none; stroke:#111111; stroke-width:7; stroke-linecap:square; }}
{s} .chip {{ margin-left:auto; background:{red}; color:#fff; padding:14px 18px; font:900 30px/1 'Inter', sans-serif;
  letter-spacing:.06em; align-self:flex-end; }}
{s} .chip b {{ font-size:44px; }}
{s} .chip.ghost {{ margin-left:0; background:transparent; color:{ink}; border:4px solid {ink}; align-self:center; }}
{s} .check {{ display:flex; align-items:center; gap:22px; }}
{s} .box {{ width:64px; height:64px; flex:none; background:#e8190f; display:flex; align-items:center; justify-content:center; }}
{s} .tick {{ fill:none; stroke:#fff; stroke-width:6; stroke-linecap:square; }}
{s} .ctext {{ font:900 54px/1.05 'Inter', sans-serif; letter-spacing:-.025em; }}
{s} .stage-a, {s} .stage-b {{ display:flex; flex-direction:column; align-items:flex-start; }}
{s} .stage-b {{ position:absolute; left:0; bottom:0; opacity:0; }}
{s} .mantra {{ display:flex; gap:22px; flex-wrap:wrap; }}
{s} .mword {{ font:900 84px/1 'Inter', sans-serif; letter-spacing:-.035em; }}
{s} .mword.red {{ color:#e8190f; }}
{s} .big {{ font:900 150px/0.9 'Inter', sans-serif; letter-spacing:-.045em; }}
{s} .stamp {{ align-self:flex-start; border:8px solid #e8190f; color:#e8190f; padding:14px 22px;
  font:900 54px/1.02 'Inter', sans-serif; letter-spacing:.01em; transform:rotate(-6deg); }}
{s} .bell {{ transform-origin:50% 10%; }}
"""


# ───────────────────────── GSAP compile ─────────────────────────
def gsap(card):
    host = f'.card-host[data-card-id="{card.id}"]'
    panel = f'.card[data-card-id="{card.id}"] .panel'
    s, e = q(card.start), q(card.end)
    L = [f"// ── {card.id} [{s} → {e}] {card.intent}",
         f"tl.set('{host}', {{ visibility: 'visible' }}, {s});",
         f"tl.fromTo('{host}', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: 'power2.out' }}, {s});",
         f"tl.fromTo('{panel}', {{ y: 70, scale: 0.97 }}, {{ y: 0, scale: 1, duration: 0.55, ease: 'power3.out' }}, {s});"]
    for el_id, kind, at, d, p in card.anims:
        sel = f'.card[data-card-id="{card.id}"] #{el_id}'
        T = q(at)
        if kind == "fade-in":
            L.append(f"tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: {d}, ease: 'power2.out' }}, {T});")
        elif kind == "fade-out":
            L.append(f"tl.to('{sel}', {{ opacity: 0, duration: {d}, ease: 'power2.in' }}, {T});")
        elif kind == "slide-in":
            dist = p.get("distance", 60)
            axis, sign = {"left": ("x", -1), "right": ("x", 1), "top": ("y", -1), "bottom": ("y", 1)}[p["from"]]
            L.append(f"tl.fromTo('{sel}', {{ opacity: 0, {axis}: {sign * dist} }}, "
                     f"{{ opacity: 1, {axis}: 0, duration: {d}, ease: 'power3.out' }}, {T});")
        elif kind == "kinetic-chars":
            L.append(f"tl.from('{sel} .char', {{ opacity: 0, y: 26, scale: 0.6, duration: {d}, "
                     f"ease: 'back.out(2)', stagger: {p['stagger']} }}, {T});")
        elif kind == "grow-x":
            L.append(f"tl.fromTo('{sel}', {{ width: 0 }}, {{ width: {p['target_w']}, duration: {d}, ease: 'power3.inOut' }}, {T});")
        elif kind == "scale-pop":
            fs, rot = p.get("from_scale", 0.55), p.get("rotate", 0)
            ease = "power4.in" if fs > 1 else "back.out(1.8)"
            L.append(f"tl.fromTo('{sel}', {{ opacity: 0, scale: {fs}, rotation: {rot * (3 if fs > 1 else 0)} }}, "
                     f"{{ opacity: 1, scale: 1, rotation: {rot}, duration: {d}, ease: '{ease}' }}, {T});")
        elif kind == "draw-path":
            L.append(f"(function(){{const el=document.querySelector('{sel}');if(el){{const L=el.getTotalLength();"
                     f"tl.set(el,{{strokeDasharray:L,strokeDashoffset:L}},0);"
                     f"tl.to(el,{{strokeDashoffset:0,duration:{d},ease:'power2.inOut'}},{T});}}}})();")
        elif kind == "count-up":
            L.append(f"(function(){{const o={{v:{p['from']}}};tl.to(o,{{v:{p['to']},duration:{d},ease:'power2.out',"
                     f"onUpdate:function(){{const el=document.querySelector('{sel}');if(el)el.textContent=__fmt(o.v,'{p['format']}');}}}},{T});}})();")
        elif kind == "morph-to":
            props = dict(p["props"])
            props["duration"] = d
            L.append(f"tl.to('{sel}', {json.dumps(props)}, {T});")
    L += [f"tl.to('{host}', {{ opacity: 0, duration: 0.3, ease: 'power2.in' }}, {q(e - 0.3)});",
          f"tl.to('{panel}', {{ y: 30, duration: 0.3, ease: 'power2.in' }}, {q(e - 0.3)});",
          f"tl.set('{host}', {{ visibility: 'hidden' }}, {e});"]
    return "\n".join(L)


# Video punch-ins on the emphasised words (scale the wrapper, never the <video>)
PUNCH = [  # (in_at, scale, out_at)
    (7.78, 1.07, 14.3),    # "yayınlandı"
    (18.46, 1.07, 22.1),   # "19 Ekim'de"
    (35.14, 1.11, 35.75),  # "kilitlenecek"
    (49.98, 1.08, 50.55),  # "ilk gün yüklenmiyoruz"
]


def video_motion():
    L = ["// ── video punch-ins on emphasised words"]
    for a, sc, b in PUNCH:
        L.append(f"tl.to('#video-wrap', {{ scale: {sc}, duration: 0.28, ease: 'power3.out' }}, {q(a)});")
        L.append(f"tl.to('#video-wrap', {{ scale: 1, duration: 0.55, ease: 'power2.inOut' }}, {q(b)});")
    L.append(f"tl.to('#video-wrap', {{ scale: 1.06, duration: {q(DUR - 51.2)}, ease: 'none' }}, 51.2);")
    L.append(f"tl.fromTo('#progress', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {DUR}, ease: 'none' }}, 0);")
    return "\n".join(L)


# ───────────────────────── write files ─────────────────────────
os.makedirs(os.path.join(PUB, "cards"), exist_ok=True)
hosts = []
for c in cards:
    frag = (f'<div class="card" data-card-id="{c.id}">\n<style>{card_css(c.id, c.theme)}</style>\n'
            f'<div class="root"><div class="panel">\n' + "\n".join(c.parts) + "\n</div></div>\n</div>\n")
    with open(os.path.join(PUB, "cards", f"{c.id}.html"), "w") as f:
        f.write(frag)
    hosts.append(f'<div id="host-{c.id}" class="card-host clip" data-card-id="{c.id}" data-start="{q(c.start)}" '
                 f'data-duration="{q(c.end - c.start)}" data-track-index="2" '
                 f'style="left:0;top:0;width:{W}px;height:{H}px;visibility:hidden;opacity:0;">\n{frag}</div>')

LATIN = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, "
         "U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
LATIN_EXT = ("U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, "
             "U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF")
faces = "".join(
    f'@font-face {{ font-family: "Inter"; src: url("fonts/inter-{sub}-{w}.woff2") format("woff2"); '
    f'font-weight: {w}; font-display: block; unicode-range: {rng}; }}\n'
    for w in (400, 600, 800, 900) for sub, rng in (("latin", LATIN), ("latin-ext", LATIN_EXT)))

index = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8" />
<style>
{faces}
:root {{ --bg:#ffffff; --text:#111111; --accent-0:#e8190f; --accent-1:#111111; --accent-2:#e8190f; --accent-3:#555555; --accent-4:#e8190f; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000;
  font-family: "Inter", sans-serif; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; }}
.video-wrapper {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; overflow:hidden;
  transform-origin:50% 30%; }}
.video-wrapper video {{ width:100%; height:100%; object-fit:cover; }}
.legibility {{ position:absolute; inset:0; pointer-events:none;
  background: linear-gradient(180deg, rgba(0,0,0,.28) 0%, transparent 9%, transparent 50%, rgba(0,0,0,.55) 72%, rgba(0,0,0,.62) 100%); }}
#progress {{ position:absolute; left:0; top:0; width:{W}px; height:10px; background:#e8190f; transform-origin:0 50%; }}
.card-host {{ position:absolute; pointer-events:none; overflow:hidden; }}
.card-host .card {{ position:relative; width:100%; height:100%; overflow:hidden; }}
.card-host .char {{ display:inline-block; visibility:visible; }}
</style>
</head>
<body>
<div id="stage" data-composition-id="talking-head-recut" data-start="0" data-duration="{DUR}"
  data-fps="{FPS}" data-width="{W}" data-height="{H}">
<div class="video-wrapper" id="video-wrap">
<video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0"
  data-duration="{DUR}" data-track-index="1"></video>
</div>
<div class="legibility"></div>
<div id="progress"></div>
{chr(10).join(hosts)}
<script src="vendor/gsap.min.js"></script>
<script>
(function () {{
window.__fmt = function (v, fmt) {{
  if (typeof fmt === "string" && /^\\.[0-9]+f$/.test(fmt)) return Number(v).toFixed(Number(fmt.slice(1, -1)));
  if (fmt === ",d") return Math.round(v).toLocaleString();
  return String(Math.round(v));
}};
const tl = window.gsap.timeline({{ paused: true }});
{video_motion()}
{chr(10).join(gsap(c) for c in cards)}
window.__timelines = window.__timelines || {{}};
window.__timelines["talking-head-recut"] = tl;
}})();
</script>
</div>
</body>
</html>
"""
with open(os.path.join(PUB, "index.html"), "w") as f:
    f.write(index)

storyboard = {
    "schemaVersion": 3,
    "composition": {"fps": FPS, "width": W, "height": H, "durationSeconds": DUR,
                    "layout": "portrait", "themeId": "mono", "seed": 1309},
    "videoTrack": {"sourcePath": "input-video.mp4", "startSec": 0, "endSec": DUR,
                   "bounds": {"x": 0, "y": 0, "width": W, "height": H}},
    "subtitles": {"enabled": False},
    "cards": [{"id": c.id, "intent": c.intent, "startSec": c.start, "endSec": c.end,
               "accentIndex": c.accent, "zone": "video-overlay", "contentHints": c.hints,
               "archetype": "swiss-" + c.theme} for c in cards],
}
with open(os.path.join(HERE, "storyboard.json"), "w") as f:
    json.dump(storyboard, f, ensure_ascii=False, indent=2)
print(f"wrote {len(cards)} cards → public/index.html")
