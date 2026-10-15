"""Project: «۳۵۰ تتر هدیه صرافی» (VID_20261014_165439_885).

Edit decision list as code. All `src` times are seconds in the original
recording; all `out` times are seconds in the edited master."""
import math

from PIL import Image, ImageDraw

import gfx as G
import tlcore
from gfx import (GOLD, GOLD_HI, GOLD_LO, GREEN, INK, INK2, RED, WHITE, GRAY, BLUE,
                 icon, life, out_back, out_cubic, in_cubic, prog, put, text, panel)
from tlcore import CLOSE, MED, W, WIDE
from widgets import clamp_, comment_box, typed_text

FACE_SRC = (345.0, 650.0)   # speaker's face in the source frame

# Shots in playback order. `join` = the audio is continuous with the previous
# shot (a punch-in on a phrase boundary, no audio edit).
SHOTS = [
    # tag        src_in  src_out  framing  push/s  join
    ("HOOK",     11.40, 15.98,   CLOSE,   0.010, False),
    ("CTX_A",     4.74,  7.30,   WIDE,    0.008, False),
    ("CTX_B",     7.92, 11.18,   MED,     0.008, False),
    ("CTA_1",    16.76, 19.16,   CLOSE,   0.020, False),
    ("CTA_2",    19.88, 22.66,   MED,     0.006, False),
    ("CTA_3",    22.86, 25.08,   CLOSE,   0.010, False),
    ("CTA_4",    25.08, 28.64,   MED,     0.008, True),
    ("REQ_1",    28.64, 33.06,   MED,     0.006, True),
    ("REQ_2",    33.26, 36.82,   (1.30, 880),   0.008, False),
    ("REQ_3",    37.08, 41.38,   MED,     0.006, False),
    ("PAYOFF",   41.38, 44.14,   CLOSE,   0.035, True),
]
# Outro: the last 0.52 s of the take, speed-ramped to 0.4x, then held.
OUTRO_SRC = (44.14, 44.66)
OUTRO_SPEED = 0.4
OUTRO_DUR = 2.70


# Verbatim transcript (corrected spelling), word timings in source seconds.
# k: g = gold keyword, m = money/green keyword, r = warning/red keyword.
WORDS = [
    # CTX_A
    ("با", 4.76, 4.98, ""), ("یه", 4.98, 5.18, ""), ("صرافی", 5.18, 5.56, "g"),
    ("صحبت", 5.56, 6.00, ""), ("کردم", 6.00, 6.30, ""), ("براتون", 6.30, 7.00, ""),
    ("به", 7.02, 7.30, ""),
    # CTX_B
    ("۱۰۰۰", 8.00, 8.48, "g"), ("نفر", 8.48, 8.82, "g"), ("اول", 8.82, 9.14, "g"),
    ("که", 9.14, 9.32, ""), ("ثبت‌نام", 9.32, 9.82, ""), ("بکنن", 9.82, 10.12, ""),
    ("داخل", 10.12, 10.40, ""), ("این", 10.40, 10.60, ""), ("صرافی", 10.60, 11.10, "g"),
    # CTA_2
    ("کلمه‌ی", 19.90, 20.68, ""), ("«صرافی»", 20.68, 21.10, "g"), ("رو", 21.10, 21.20, ""),
    ("برای", 21.20, 21.36, ""), ("من", 21.36, 21.52, ""), ("این", 21.52, 21.60, ""),
    ("پایین", 21.60, 21.84, "g"), ("بنویسین", 21.84, 22.40, ""),
    # CTA_3
    ("و", 22.90, 23.20, ""), ("دایرکت‌تونو", 23.20, 24.30, "g"), ("چک", 24.30, 24.56, "g"),
    ("بکنید", 24.56, 25.06, ""),
    # CTA_4
    ("و", 25.08, 25.18, ""), ("از", 25.18, 25.38, ""), ("طریق", 25.38, 25.58, ""),
    ("لینکی", 25.58, 26.00, "g"), ("که", 26.00, 26.04, ""), ("براتون", 26.04, 26.38, ""),
    ("ارسال", 26.38, 26.76, ""), ("میشه", 26.76, 27.20, ""),
    ("ثبت‌نام‌تونو", 27.20, 28.08, "g"), ("انجام", 28.08, 28.46, ""), ("بدین", 28.46, 28.64, ""),
    # REQ_1
    ("راستی", 28.64, 29.42, ""), ("حتماً", 29.42, 30.00, "r"), ("باید", 30.00, 30.30, ""),
    ("زبان", 30.30, 30.84, ""), ("این", 30.84, 31.10, ""), ("برنامه", 31.10, 31.86, ""),
    ("فارسی", 31.86, 32.56, "g"), ("باشه", 32.56, 33.04, ""),
    # REQ_2
    ("و", 33.30, 33.74, ""), ("اینکه", 33.74, 34.26, ""), ("بدون", 34.26, 34.84, "r"),
    ("VPN", 34.84, 35.34, "r"), ("باید", 35.34, 35.76, ""), ("وارد", 35.76, 36.16, ""),
    ("بشین", 36.16, 36.80, ""),
    # REQ_3
    ("ایمیل", 37.10, 38.24, "g"), ("و", 38.24, 38.44, ""), ("شماره‌تماس‌تون", 38.44, 39.38, "g"),
    ("باید", 39.38, 39.66, ""), ("حتماً", 39.66, 40.36, "r"), ("وارد", 40.36, 40.72, ""),
    ("بکنید", 40.72, 41.36, ""),
    # PAYOFF
    ("تا", 41.40, 41.62, ""), ("این", 41.62, 41.88, ""), ("۳۵۰", 41.88, 42.46, "m"),
    ("تتر", 42.46, 42.94, "m"), ("بهتون", 42.94, 43.20, ""), ("تعلق", 43.20, 43.72, ""),
    ("بگیره", 43.72, 44.12, ""),
]

# Caption chunks (word counts, in order). Chunks never cross a shot boundary
# and break on phrase boundaries.
CHUNK_SIZES = [3, 4, 3, 3, 3, 3, 5, 4, 4, 4, 3, 3, 5, 3, 4, 3, 4, 4, 3]

# Shots where the bottom captions are replaced by kinetic typography.
NO_CAPTION_SHOTS = {"HOOK", "CTA_1"}

tlcore.setup(globals())
SOURCE_NAME = "VID_20261014_165439_885.mp4"
MUSIC_DROPS = [(SHOT["REQ_1"]["out_in"] - 0.15, None)]  # None = 2 beats
BEAT = 0.605  # music tempo (s/beat) as shipped


# ---------------------------------------------------------------- scenes
def big_number(B, t, t0, y, size=300, count=True, exit_t=None):
    """"۳۵۰" headline that lives *behind* the speaker (layer B is masked)."""
    if t < t0:
        return
    k = prog(t, t0, 0.55)
    val = int(round(350 * out_cubic(k))) if count else 350
    s = str(val).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    sp = text(s, "Black", size, GOLD, stroke=6, stroke_fill=(60, 38, 4), shadow=10,
              glow=(255, 170, 30), gradient=(GOLD_HI, GOLD_LO))
    sc = 0.6 + 0.4 * out_back(prog(t, t0, 0.42))
    a = prog(t, t0, 0.12)
    if exit_t is not None:
        e = prog(t, exit_t, 0.2)
        sc *= 1 + 0.5 * in_cubic(e); a *= 1 - e
    put(B, sp, W / 2, y, scale=sc, alpha=a)


def usdt_pill(L, t, t0, y, exit_t=None):
    if t < t0:
        return
    p = panel(330, 96, 48, GREEN, 245, shadow=True)
    k = out_back(prog(t, t0, 0.35))
    a = prog(t, t0, 0.1)
    if exit_t is not None:
        e = prog(t, exit_t, 0.18); a *= 1 - e; k *= 1 + 0.4 * e
    put(L, p, W / 2, y, scale=k, alpha=a)
    put(L, icon("coin", 70), W / 2 + 112 * k, y, scale=k, alpha=a, rot=(1 - prog(t, t0, 0.5)) * 200)
    put(L, text("تتر  USDT", "Black", 46, WHITE), W / 2 - 34 * k, y + 2, scale=k, alpha=a)


def scene_hook(t, L, B):
    s = S["HOOK"]
    if not (s["out_in"] <= t < s["out_out"]):
        return
    ex = s["out_out"] - 0.2
    big_number(B, t, 0.0, 585, exit_t=ex)
    usdt_pill(L, t, o(12.34), 335, exit_t=ex)
    # voucher ticket slides in on "ووچر", gift bow lands on "هدیه"
    t0 = o(13.80) - 0.05
    if t >= t0:
        k = out_back(prog(t, t0, 0.45), 1.2)
        a = prog(t, t0, 0.12) * (1 - prog(t, ex, 0.2))
        x = W / 2 + (1 - k) * 700
        rot = (1 - k) * -14 + (-3)
        tk = ticket()
        put(L, tk, x, 1345, alpha=a, rot=rot)
        g0 = o(14.74)
        if t >= g0:
            kg = out_back(prog(t, g0, 0.35), 2.2)
            put(L, icon("gift", 150, GOLD, RED), x + 300, 1215, scale=kg, alpha=a, rot=-12)
            ks = out_back(prog(t, g0 + 0.08, 0.3), 2.5)
            put(L, stamp(), x - 300, 1205, scale=ks, alpha=a, rot=10)


_ticket = None


def ticket():
    global _ticket
    if _ticket is not None:
        return _ticket
    w, h = 720, 230
    sp = panel(w, h, 30, grad=(GOLD_HI, GOLD_LO), shadow=True)
    sp = sp.copy()
    d = ImageDraw.Draw(sp)
    pad = 40
    # notches + perforation
    for cy in (pad + h // 2,):
        d.ellipse([pad - 26, cy - 26, pad + 26, cy + 26], fill=(0, 0, 0, 0))
        d.ellipse([pad + w - 26, cy - 26, pad + w + 26, cy + 26], fill=(0, 0, 0, 0))
    xs = pad + 230
    for yy in range(pad + 18, pad + h - 18, 22):
        d.line([(xs, yy), (xs, yy + 11)], fill=(120, 76, 6, 200), width=4)
    put(sp, text("VOUCHER", "Black", 34, (90, 56, 4)), pad + 115, pad + 70)
    put(sp, icon("coin", 86), pad + 115, pad + 150)
    put(sp, text("ووچر هدیه", "Black", 70, INK), pad + 470, pad + 82)
    put(sp, text("۳۵۰ USDT", "Black", 58, (60, 38, 4)), pad + 470, pad + 162)
    _ticket = sp
    return sp


_stamp = None


def stamp():
    global _stamp
    if _stamp is None:
        sp = panel(190, 84, 18, GREEN, 255, border=WHITE, border_a=255, shadow=True).copy()
        put(sp, text("هدیه", "Black", 50, WHITE), sp.width / 2, sp.height / 2 + 2)
        _stamp = sp
    return _stamp


def scene_context(t, L):
    a_ = S["CTX_A"]
    # exchange card (CTX_A)
    t0, t1 = o(5.18), a_["out_out"]
    al, ki, ke = life(t, t0 - 0.05, t1, 0.3, 0.2)
    if al:
        sc = out_back(ki) * (1 - 0.15 * ke)
        a = min(1, ki * 3) * (1 - ke)
        y = 330
        put(L, panel(560, 150, 40, INK, 225, border=GOLD, border_a=110), W / 2, y, scale=sc, alpha=a)
        put(L, icon("exchange", 104, INK, GOLD), W / 2 + 175 * sc, y, scale=sc, alpha=a)
        put(L, text("صرافی", "Black", 76, WHITE), W / 2 - 50 * sc, y + 4, scale=sc, alpha=a)
        # "talked to them": chat bubble with typing dots
        tc = o(5.56)
        if t >= tc:
            kc = out_back(prog(t, tc, 0.3), 2)
            bx, by = W / 2 - 250 * sc, y - 80 * sc
            put(L, icon("chat", 96, WHITE), bx, by, scale=kc, alpha=a)
            for j in range(3):
                ph = (t - tc) * 7 - j * 0.9
                dy = -6 * max(0, math.sin(ph))
                put(L, icon("disc", 14, INK), bx - 22 + j * 22, by - 6 + dy, scale=kc, alpha=a)
    # "first 1000 people" infographic (CTX_B)
    b_ = S["CTX_B"]
    t0, t1 = b_["out_in"] + 0.05, b_["out_out"]
    al, ki, ke = life(t, t0, t1, 0.3, 0.2)
    if not al:
        return
    sc = out_back(ki, 1.3) * (1 - 0.12 * ke)
    a = min(1, ki * 3) * (1 - ke)
    cy = 380
    reveal = t >= o(10.60)
    ph = 330 if not reveal else 330 + 120 * out_cubic(prog(t, o(10.60), 0.3))
    put(L, panel(820, int(ph), 44, INK, 228, border=GOLD, border_a=90), W / 2, cy + (ph - 330) / 2, scale=sc, alpha=a)
    put(L, text("۱۰۰۰", "Black", 120, GOLD, glow=(255, 160, 20)), W / 2 + 170 * sc, cy - 80 * sc, scale=sc, alpha=a)
    put(L, text("نفر اول", "Black", 72, WHITE), W / 2 - 150 * sc, cy - 74 * sc, scale=sc, alpha=a)
    # 2 x 10 grid of people popping in as a wave (right -> left)
    for r in range(2):
        for c in range(10):
            td = t0 + 0.25 + (c + r * 10) * 0.035
            if t < td:
                continue
            kk = out_back(prog(t, td, 0.25), 2.4)
            x = W / 2 + (330 - c * 73) * sc
            y = cy + (40 + r * 82) * sc
            col = GOLD if (r * 10 + c) < 20 else GRAY
            put(L, icon("person", 58, col), x, y, scale=kk * sc, alpha=a)
    if reveal:
        k = out_back(prog(t, o(10.60), 0.35), 1.6)
        yb = cy + 225 * sc
        put(L, text("هدیه", "Black", 58, WHITE), W / 2 + 250, yb, scale=k, alpha=a)
        put(L, icon("arrow_down", 54, GOLD), W / 2 + 140, yb, scale=k, alpha=a, rot=-90)
        put(L, panel(330, 86, 43, GREEN, 245, shadow=False), W / 2 - 110, yb, scale=k, alpha=a)
        put(L, icon("coin", 62), W / 2 - 110 + 120 * k, yb, scale=k, alpha=a)
        put(L, text("۳۵۰ USDT", "Black", 46, WHITE), W / 2 - 140, yb + 2, scale=k, alpha=a)


def scene_cta1(t, L):
    s = S["CTA_1"]
    al, ki, ke = life(t, s["out_in"], s["out_out"], 0.2, 0.15)
    if not al:
        return
    a = 1 - ke
    t1 = o(16.80)
    if t >= t1:
        k = out_cubic(prog(t, t1, 0.25))
        put(L, text("پس لطفاً", "Black", 74, WHITE, stroke=6, shadow=8), W / 2, 270 + (1 - k) * 30, alpha=a * k)
    t2 = o(18.16)
    if t >= t2:
        k = out_back(prog(t, t2, 0.32), 2.0)
        y = 420
        put(L, text("هرچه سریع‌تر!", "Black", 124, GOLD, stroke=8, stroke_fill=(40, 24, 0), shadow=10,
                    glow=(255, 150, 0)), W / 2 + 60, y, scale=k, alpha=a)
        # stopwatch with a racing hand
        sx, sy = W / 2 - 390, y
        put(L, icon("stopwatch", 130, WHITE), sx, sy, scale=k, alpha=a)
        ang = (t - t2) * 900
        hand = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hand)
        cx, cy = 65, 72
        hd.line([(cx, cy), (cx + 34 * math.sin(math.radians(ang)), cy - 34 * math.cos(math.radians(ang)))],
                fill=G.rgba(GOLD), width=8)
        hd.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=G.rgba(GOLD))
        put(L, hand, sx, sy, scale=k, alpha=a)
        # speed streaks
        for j, (yy, ln) in enumerate([(-40, 160), (0, 230), (40, 130)]):
            p = prog(t, t2 + j * 0.04, 0.35)
            if 0 < p < 1:
                x0 = W - 40 - p * 300
                streak = panel(int(ln * (1 - p) + 10), 8, 4, GOLD, int(220 * (1 - p)), shadow=False)
                put(L, streak, x0, y + yy, anchor="l")


STEPS = [("کامنت «صرافی»", 20.68, 21.90), ("چک دایرکت", 23.20, 26.38), ("ثبت‌نام با لینک", 27.20, 27.70)]


def scene_stepper(t, L):
    t_in, t_out = S["CTA_2"]["out_in"], S["CTA_4"]["out_out"]
    al, ki, ke = life(t, t_in, t_out, 0.3, 0.2)
    if not al:
        return
    a = min(1, ki * 2) * (1 - ke)
    yy = 250 - (1 - out_cubic(ki)) * 60
    put(L, panel(940, 170, 40, INK, 220, border=WHITE, border_a=40), W / 2, yy, alpha=a)
    xs = [W / 2 + 300, W / 2, W / 2 - 300]
    # connector lines (fill as steps complete)
    for j in range(2):
        put(L, panel(220, 6, 3, (70, 72, 80), 255, shadow=False), (xs[j] + xs[j + 1]) / 2, yy - 28, alpha=a)
        done = o(STEPS[j][2])
        p = out_cubic(prog(t, done, 0.35))
        if p > 0:
            ln = max(6, int(220 * p))
            put(L, panel(ln, 6, 3, GREEN, 255, shadow=False), xs[j] - 40 - ln / 2, yy - 28, alpha=a)
    for j, (lab, ton, tdone) in enumerate(STEPS):
        x = xs[j]
        on, dn = t >= o(ton), t >= o(tdone)
        k = out_back(prog(t, o(ton), 0.35), 2.2) if on else 0
        col = GREEN if dn else GOLD if on else (70, 72, 80)
        sc = 1 + 0.18 * k * (0 if dn else 1)
        put(L, icon("disc", 64, col), x, yy - 28, scale=sc, alpha=a)
        if dn:
            put(L, G.partial_check(64, out_cubic(prog(t, o(tdone), 0.3)), WHITE, 12), x, yy - 28, scale=sc, alpha=a)
        else:
            put(L, text("۱۲۳"[j], "Black", 38, INK if on else WHITE), x, yy - 26, scale=sc, alpha=a)
        put(L, text(lab, "Bold", 34, WHITE if on else GRAY), x, yy + 42, alpha=a)


def scene_cta2(t, L):
    s = S["CTA_2"]
    al, ki, ke = life(t, s["out_in"], s["out_out"], 0.3, 0.15)
    if not al:
        return
    a = min(1, ki * 2) * (1 - ke)
    cy = 1385 + (1 - out_back(ki)) * 160
    sent = o(21.90)
    typed = "" if t >= sent + 0.25 else typed_text("صرافی", t, o(20.68))
    comment_box(L, t, cy, typed, sent, a)
    if t >= sent + 0.2:  # posted: comment bubble rises
        k = out_back(prog(t, sent + 0.2, 0.35), 1.8)
        by = cy - 20 - 75 * out_cubic(prog(t, sent + 0.2, 0.4))
        put(L, panel(300, 84, 42, GOLD, 255), W / 2 + 250, by, scale=k, alpha=a)
        put(L, text("صرافی", "Black", 44, INK), W / 2 + 270, by + 2, scale=k, alpha=a)
        put(L, icon("heart", 34, RED), W / 2 + 145, by, scale=k, alpha=a)
    ta = o(21.52)
    if t >= ta and t < sent + 0.25:
        k = out_back(prog(t, ta, 0.3), 2)
        bob = 14 * math.sin((t - ta) * 12)
        put(L, icon("arrow_down", 88, GOLD), W / 2 - 330, cy - 120 + bob, scale=k, alpha=a)


def scene_dm(t, L):
    t0 = o(23.20)
    t_exit = o(27.20)
    al, ki, ke = life(t, t0 - 0.05, t_exit + 0.25, 0.4, 0.25)
    if not al:
        return
    k = out_back(ki, 1.1)
    a = min(1, ki * 2) * (1 - ke)
    y = 470 - (1 - k) * 200 - ke * 60
    put(L, panel(900, 170, 40, WHITE, 248), W / 2, y, alpha=a)
    ix = W / 2 + 360
    put(L, icon("disc", 104, (233, 62, 120)), ix, y, alpha=a)
    put(L, icon("plane", 58, WHITE, (233, 62, 120)), ix - 2, y + 2, alpha=a)
    put(L, text("دایرکت جدید", "Black", 42, INK), ix - 80, y - 34, alpha=a, anchor="r")
    put(L, text("الان", "Medium", 30, GRAY), W / 2 - 400, y - 34, alpha=a, anchor="l")
    # link chip
    tl = o(25.58)
    hl = out_cubic(prog(t, tl, 0.25))
    chip_col = tuple(int(c0 + (c1 - c0) * hl) for c0, c1 in zip((236, 240, 248), (222, 236, 255)))
    put(L, panel(520, 62, 31, chip_col, 255, shadow=False), ix - 80 - 260, y + 36, alpha=a)
    put(L, icon("link", 44, BLUE), ix - 80 - 40, y + 36, alpha=a)
    put(L, text("لینک ثبت‌نام", "Bold", 34, BLUE if hl > 0.5 else INK2), ix - 80 - 80, y + 38, alpha=a, anchor="r")
    if hl > 0:
        ln = int(240 * hl)
        put(L, panel(max(4, ln), 4, 2, BLUE, 255, shadow=False), ix - 160 - ln / 2, y + 62, alpha=a)
    # tap ripple on "ارسال"
    tt = o(26.38)
    if t >= tt:
        p = prog(t, tt, 0.45)
        put(L, icon("ring", 110, BLUE), ix - 300, y + 36, scale=0.4 + 0.9 * p, alpha=a * (1 - p))
        put(L, icon("disc", 46, (40, 40, 48)), ix - 300 + 20, y + 36 + 20, alpha=a * 0.55 * (1 - prog(t, tt + 0.3, 0.3)))


def scene_signup(t, L):
    t0 = o(27.20)
    t1 = S["CTA_4"]["out_out"]
    al, ki, ke = life(t, t0 + 0.15, t1, 0.35, 0.2)
    if not al:
        return
    k = out_back(ki, 1.6)
    a = min(1, ki * 2) * (1 - ke)
    y = 480
    put(L, panel(600, 150, 75, GREEN, 245), W / 2, y, scale=k, alpha=a)
    put(L, icon("disc", 104, WHITE), W / 2 + 222 * k, y, scale=k, alpha=a)
    put(L, G.partial_check(104, out_cubic(prog(t, t0 + 0.3, 0.35)), GREEN, 13), W / 2 + 222 * k, y, scale=k, alpha=a)
    put(L, text("ثبت‌نام انجام شد", "Black", 52, WHITE), W / 2 - 50 * k, y + 2, scale=k, alpha=a)


REQS = [
    # (icon builder, label, t_show_src, t_mark_src, mark)
    ("globe", "زبان برنامه: فارسی", 30.30, 32.06, "ok"),
    ("shield", "ورود بدون VPN", 34.26, 34.84, "no"),
    ("mailphone", "ایمیل + شماره تماس", 37.10, 39.86, "ok"),
]


def req_icon(kind, size):
    box = panel(size, size, 22, INK2, 255, border=GOLD, border_a=120, shadow=False).copy()
    c = box.width / 2
    if kind == "globe":
        put(box, icon("globe", int(size * 0.66), GOLD), c, c)
        put(box, text("فا", "Black", int(size * 0.26), WHITE, stroke=4, stroke_fill=INK2), c + 2, c + 2)
    elif kind == "shield":
        put(box, icon("shield", int(size * 0.66), GOLD), c, c)
        put(box, text("VPN", "Black", int(size * 0.18), INK), c, c - 4)
    else:
        put(box, icon("mail", int(size * 0.46), GOLD, INK2), c + size * 0.12, c - size * 0.08)
        put(box, icon("phone", int(size * 0.46), WHITE, INK2), c - size * 0.18, c + size * 0.1)
    return box


_req_icons = {}


def scene_reqs(t, L):
    t_in, t_out = S["REQ_1"]["out_in"], S["REQ_3"]["out_out"]
    al, ki, ke = life(t, t_in, t_out, 0.3, 0.2)
    if not al:
        return
    a = (1 - ke)
    # header: alert pill with a small shake on "راستی"
    k = out_back(prog(t, t_in, 0.35), 2.2)
    shake = 8 * math.sin((t - t_in) * 60) * (1 - prog(t, t_in, 0.35))
    hy = 225
    put(L, panel(330, 82, 41, RED, 245), W / 2 + shake, hy, scale=k, alpha=a)
    put(L, icon("alert", 50, WHITE, RED), W / 2 + 110 * k + shake, hy, scale=k, alpha=a)
    put(L, text("نکات مهم", "Black", 44, WHITE), W / 2 - 30 * k + shake, hy + 2, scale=k, alpha=a)
    shown = [r for r in REQS if t >= o(r[2]) - 0.05]
    if not shown:
        return
    rows_h = 92
    top = 300
    ph = 24 + rows_h * len(shown)
    put(L, panel(860, int(ph), 34, INK, 222, border=WHITE, border_a=35), W / 2, top + ph / 2, alpha=a)
    for j, (ic, lab, ts, tm, mark) in enumerate(shown):
        y = top + 12 + rows_h * j + rows_h / 2
        kr = out_cubic(prog(t, o(ts) - 0.05, 0.3))
        dx = (1 - kr) * 80
        if ic not in _req_icons:
            _req_icons[ic] = req_icon(ic, 70)
        put(L, _req_icons[ic], W / 2 + 370 + dx, y, alpha=a * kr)
        put(L, text(lab, "Black", 44, WHITE), W / 2 + 310 + dx, y + 2, alpha=a * kr, anchor="r")
        if t >= o(tm):
            p = prog(t, o(tm), 0.3)
            km = out_back(p, 2.5)
            if mark == "ok":
                put(L, icon("disc", 62, GREEN), W / 2 - 360, y, scale=km, alpha=a)
                put(L, G.partial_check(62, out_cubic(prog(t, o(tm) + 0.05, 0.3)), WHITE, 13), W / 2 - 360, y, scale=km, alpha=a)
            else:
                put(L, icon("disc", 62, RED), W / 2 - 360, y, scale=km, alpha=a)
                put(L, icon("cross", 62, WHITE), W / 2 - 360, y, scale=km * 0.8, alpha=a)
                # strike through the VPN icon
                ls = out_cubic(prog(t, o(tm), 0.2))
                ln = int(84 * ls)
                if ln > 2:
                    put(L, panel(ln, 8, 4, RED, 255, shadow=False), W / 2 + 370 + dx, y, alpha=a, rot=-40)


def scene_payoff(t, L, B):
    s = S["PAYOFF"]
    t0 = o(41.88)
    if not (t0 - 0.05 <= t < s["out_out"] + 0.1):
        return
    ex = s["out_out"] - 0.15
    big_number(B, t, t0, 560, size=280, count=False, exit_t=ex)
    usdt_pill(L, t, o(42.46), 320, exit_t=ex)
    # coins rain onto the scene
    for j, (x, delay, rot0, sz) in enumerate([(170, 0.0, 30, 110), (900, 0.08, -20, 96), (300, 0.2, 60, 76),
                                              (790, 0.28, 10, 84), (120, 0.36, -40, 64), (980, 0.42, 25, 70)]):
        tj = t0 + 0.05 + delay
        if t < tj:
            continue
        p = prog(t, tj, 0.7)
        yy = -120 + (560 + j * 55) * out_cubic(p) - 30 * math.sin(math.pi * clamp_(p * 2 - 1))
        a = 1 - prog(t, ex, 0.2)
        put(L, icon("coin", sz), x, yy, alpha=a, sx=abs(math.cos((t - tj) * 5 + j)) + 0.15, scale=1, rot=rot0 * (1 - p))


def scene_outro(t, L):
    t0 = BODY_DUR
    if t < t0:
        return
    lt = t - t0
    k1 = out_back(prog(lt, 0.15, 0.4), 1.6)
    put(L, text("همین الان کامنت کن", "Black", 84, WHITE, shadow=10), W / 2, 520 - (1 - k1) * 40, alpha=prog(lt, 0.15, 0.2))
    k2 = out_back(prog(lt, 0.32, 0.45), 2.2)
    put(L, text("«صرافی»", "Black", 150, GOLD, stroke=6, stroke_fill=(50, 30, 0), shadow=12, glow=(255, 150, 0)),
        W / 2, 690, scale=k2, alpha=prog(lt, 0.32, 0.1))
    k3 = out_back(prog(lt, 0.55, 0.45))
    if lt >= 0.55:
        comment_box(L, t, 890 + (1 - k3) * 120, typed_text("صرافی", lt, 0.75), a=prog(lt, 0.55, 0.15),
                    pulse=lt > 1.2)
    if lt >= 0.9:
        bob = 14 * math.sin(lt * 9)
        put(L, icon("arrow_down", 96, GOLD), W / 2, 1040 + bob, scale=out_back(prog(lt, 0.9, 0.3), 2))
    chips = [(1.0, "gift", "۳۵۰ USDT هدیه برای ۱۰۰۰ نفر اول", GOLD),
             (1.25, "plane", "لینک ثبت‌نام در دایرکت شما", (233, 62, 120))]
    for j, (td, ic, lab, col) in enumerate(chips):
        if lt < td:
            continue
        k = out_cubic(prog(lt, td, 0.35))
        y = 1190 + j * 104
        put(L, panel(820, 86, 43, INK, 225, border=col, border_a=160), W / 2 + (1 - k) * 120, y, alpha=k)
        put(L, icon(ic, 52, col, INK), W / 2 + 350 + (1 - k) * 120, y, alpha=k)
        put(L, text(lab, "Bold", 40, WHITE), W / 2 + 300 + (1 - k) * 120, y + 2, alpha=k, anchor="r")
    if lt >= 1.55:
        put(L, text("زبان فارسی  •  بدون VPN  •  ایمیل و شماره تماس", "Medium", 34, (225, 225, 230)),
            W / 2, 1420, alpha=prog(lt, 1.55, 0.3))


# ---------------------------------------------------------------- engine hooks
def camera_fx(s, lt):
    """Per-shot camera moves on top of framing + push. -> (zoom mult, blur samples)"""
    mult, nblur = 1.0, 1
    if s["tag"] == "HOOK":
        k = prog(lt, 0, 0.36)
        mult *= 1 + 0.20 * (1 - out_cubic(k))
        if k < 1:
            nblur = 5
        k2 = prog(lt, s["out_out"] - s["out_in"] - 0.20, 0.20)
        mult *= 1 + 0.28 * in_cubic(k2)
        if k2 > 0:
            nblur = 7
        if lt >= o(14.74) - s["out_in"]:  # punch on "هدیه"
            mult *= 1.07
    if s["tag"] == "CTX_A":
        k = prog(lt, 0, 0.30)
        mult *= 1 + 0.30 * (1 - out_cubic(k))
        if k < 1:
            nblur = 7
    if s["tag"] == "REQ_1":  # "راستی": quick settle punch
        k = prog(lt, 0, 0.22)
        mult *= 1 + 0.06 * (1 - out_cubic(k))
    return mult, nblur


def scrim_windows():
    """Top darkening only while top-zone graphics are on screen."""
    return [(0.0, S["HOOK"]["out_out"]), (o(5.18), S["CTX_B"]["out_out"]),
            (S["CTA_1"]["out_in"], S["REQ_3"]["out_out"]), (o(41.88), BODY_DUR)]


def caption_y(tag):
    return 1190 if tag == "CTA_2" else 1350


def draw_behind(t, L, B):
    scene_hook(t, L, B)
    scene_payoff(t, L, B)


def draw_front(t, L):
    scene_context(t, L)
    scene_cta1(t, L)
    scene_stepper(t, L)
    scene_cta2(t, L)
    scene_dm(t, L)
    scene_signup(t, L)
    scene_reqs(t, L)


def draw_top(t, L):
    scene_outro(t, L)


# ---------------------------------------------------------------- sound
def cues(A):
    c = []
    add = lambda t, fx, g=1.0, pan=0.0: c.append((t, fx, g, pan))
    # HOOK
    add(0.0, A.sfx_impact(), 0.9)
    add(0.0, A.sfx_whoosh(0.35), 0.5)
    for k in range(10):
        add(0.05 + k * 0.05, A.sfx_tick(), 0.7, (-1) ** k * 0.2)
    add(0.58, A.sfx_coin(), 0.75)
    add(o(12.34), A.sfx_pop(), 0.8)
    add(o(13.80) - 0.08, A.sfx_whoosh(0.4), 0.55, 0.3)
    add(o(14.74), A.sfx_pop(), 0.8)
    add(o(14.74) + 0.03, A.sfx_coin(), 0.35)
    # transition hook -> context
    add(S["CTX_A"]["out_in"] - 0.28, A.sfx_whoosh(0.5), 0.75, -0.2)
    add(o(5.18), A.sfx_pop(), 0.6)
    add(S["CTX_B"]["out_in"], A.sfx_whoosh(0.3, up=False), 0.35)
    for k in range(8):
        add(o(8.05) + 0.1 + k * 0.045, A.sfx_tick(), 0.45)
    add(o(10.60), A.sfx_pop(), 0.6)
    add(o(10.62), A.sfx_coin(), 0.35)
    # CTA
    add(S["CTA_1"]["out_in"] - 0.15, A.sfx_whoosh(0.3), 0.5)
    add(o(18.16), A.sfx_whoosh(0.35), 0.5, 0.2)
    add(o(18.16) + 0.05, A.sfx_clock(), 0.8)
    add(S["CTA_2"]["out_in"], A.sfx_pop(), 0.6)
    t0 = o(20.68)
    for k in range(5):
        add(t0 + k * 0.075, A.sfx_type(), 0.8)
    add(o(21.52), A.sfx_pop(), 0.4)
    add(o(21.90), A.sfx_whoosh(0.25), 0.45, 0.4)
    add(o(21.90) + 0.02, A.sfx_tap(), 0.8)
    add(o(23.20), A.sfx_notify(), 0.85)
    add(o(26.38), A.sfx_tap(), 0.9)
    add(o(27.20), A.sfx_success(), 0.8)
    # REQ
    add(S["REQ_1"]["out_in"], A.sfx_alert(), 0.9)
    add(S["REQ_1"]["out_in"], A.sfx_soft_hit(), 0.8)
    add(o(30.30), A.sfx_pop(), 0.5)
    add(o(31.86) + 0.2, A.sfx_check(), 0.8)
    add(o(34.26), A.sfx_pop(), 0.5)
    add(o(34.84), A.sfx_strike(), 0.8)
    add(o(37.10), A.sfx_pop(), 0.5)
    add(o(39.66) + 0.2, A.sfx_check(), 0.8)
    # PAYOFF
    add(o(41.88), A.sfx_soft_hit(), 0.9)
    add(o(41.88) + 0.05, A.sfx_coin(), 0.6)
    for k in range(4):
        add(o(42.0) + 0.25 + k * 0.13, A.bell(2637 + k * 220, 0.4, 7.0) * 0.12, 1.0, (-1) ** k * 0.4)
    # OUTRO
    add(BODY_DUR - 1.1, A.sfx_riser(1.1), 0.5)
    add(BODY_DUR, A.sfx_impact(), 0.8)
    t0 = BODY_DUR + 0.75
    for k in range(5):
        add(t0 + k * 0.075, A.sfx_type(), 0.6)
    add(BODY_DUR + 1.35, A.sfx_notify(), 0.5)
    return c
