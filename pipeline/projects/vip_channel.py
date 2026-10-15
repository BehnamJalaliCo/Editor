"""Project: «کانال VIP تلگرام رایگان شد» (VID_20261014_165425_558).

Edit decision list as code. All `src` times are seconds in the original
recording; all `out` times are seconds in the edited master."""
import math

import gfx as G
import tlcore
from gfx import (GOLD, GOLD_HI, GOLD_LO, GREEN, INK, RED, WHITE, GRAY,
                 icon, life, out_back, out_cubic, in_cubic, prog, put, text, panel)
from tlcore import CLOSE, MED, W, WIDE
from widgets import comment_box, kinetic, notification, pill, stepper, typed_text

SOURCE_NAME = "VID_20261014_165425_558.mp4"
FACE_SRC = (330.0, 640.0)   # speaker's face in the source frame
TG_BLUE = (42, 171, 238)    # channel / bot accent
PINK = (233, 62, 120)

# Shots in playback order. `join` = the audio is continuous with the previous
# shot (a punch on a phrase boundary, no audio edit).
SHOTS = [
    # tag        src_in  src_out  framing        push/s  join
    ("HOOK",      3.20,  5.70,   CLOSE,         0.014, False),  # کانال تلگرام VIPمون کاملاً رایگان شده
    ("MUST_1",    6.00,  6.46,   MED,           0.0,   False),  # حتماً
    ("MUST_2",    6.46,  7.10,   (1.30, 850),   0.0,   True),   # حتماً
    ("MUST_3",    7.10,  7.46,   (1.48, 800),   0.0,   True),   # حتماً
    ("BOT",       7.46,  8.86,   MED,           0.010, True),   # وارد رباتمون بشین
    ("EX_A",      9.16, 10.68,   WIDE,          0.008, False),  # از طریق صرافیـ
    ("EX_B",     11.22, 12.70,   MED,           0.008, False),  # اوربیت یا
    ("EX_C",     12.94, 13.50,   CLOSE,         0.010, False),  # ال‌بنک
    ("LINK",     13.80, 16.12,   MED,           0.008, False),  # که براتون لینکش‌رو گذاشتم داخل ربات
    ("SIGNUP",   16.50, 18.38,   CLOSE,         0.012, False),  # ثبت‌نام بکنین با رفرال ما (و)
    ("JOIN",     20.48, 21.44,   MED,           0.010, False),  # وارد کانال بشین
    ("SIGNAL",   21.44, 22.78,   CLOSE,         0.012, True),   # از سیگنال‌ها استفاده بکنین
    ("EDU",      22.78, 25.62,   MED,           0.006, True),   # شما اگر آموزش دیده باشین یا ...
    ("EASY_A",   25.62, 27.40,   CLOSE,         0.010, True),   # سیگنال‌های ما طوری هست
    ("EASY_B",   27.40, 31.76,   MED,           0.010, True),   # که خیلی سهل و آسون ...
    ("CTA_A",    32.68, 34.08,   CLOSE,         0.014, False),  # برای دریافت کانال لطفاً
    ("CTA_B",    34.08, 36.08,   MED,           0.006, True),   # کلمه‌ی «کانال» رو برای من کامنت بکنین
    ("DM",       36.08, 37.58,   CLOSE,         0.012, True),   # دایرکت‌تونو چک بکنین
    ("SHARE",    37.86, 39.72,   MED,           0.008, False),  # برای دوستانتونم ارسال بکنین
    ("SIGNOFF",  39.72, 40.56,   CLOSE,         0.030, True),   # موفق باشید
]
OUTRO_SRC = (40.56, 41.02)
OUTRO_SPEED = 0.4
OUTRO_DUR = 2.70

# Verbatim transcript (corrected spelling). Timings come from a word-level
# re-transcription of the *edited* dialogue, so they are in output seconds;
# they are converted to source seconds below.
# k: g = gold keyword, m = green (free / easy), r = red (emphasis)
WORDS_OUT = [
    # HOOK (kinetic typography instead of captions)
    ("کانال", 0.02, 0.24, "g"), ("تلگرام", 0.24, 0.80, "g"), ("VIP‌مون", 0.80, 1.36, "g"),
    ("کاملاً", 1.36, 1.72, ""), ("رایگان", 1.72, 2.14, "m"), ("شده", 2.14, 2.48, ""),
    # MUST_1..3
    ("حتماً", 2.52, 2.96, "r"), ("حتماً", 2.96, 3.60, "r"), ("حتماً", 3.60, 3.96, "r"),
    # BOT
    ("وارد", 3.98, 4.28, ""), ("رباتمون", 4.28, 4.94, "g"), ("بشین", 4.94, 5.34, ""),
    # EX_A / EX_B / EX_C
    ("از", 5.38, 5.54, ""), ("طریق", 5.54, 5.92, ""), ("صرافی", 5.92, 6.86, "g"),
    ("اوربیت", 6.92, 7.74, "g"), ("یا", 7.74, 8.34, ""),
    ("ال‌بنک", 8.38, 8.90, "g"),
    # LINK
    ("که", 8.94, 9.02, ""), ("براتون", 9.02, 9.38, ""), ("لینکش‌رو", 9.38, 9.80, "g"),
    ("گذاشتم", 9.80, 10.26, ""), ("داخل", 10.26, 10.60, ""), ("ربات", 10.60, 11.20, "g"),
    # SIGNUP
    ("ثبت‌نام", 11.26, 11.70, "g"), ("بکنین", 11.70, 12.14, ""), ("با", 12.14, 12.32, ""),
    ("رفرال", 12.32, 12.74, "g"), ("ما", 12.74, 13.08, ""),
    # JOIN / SIGNAL
    ("وارد", 13.14, 13.46, ""), ("کانال", 13.46, 13.86, "g"), ("بشین", 13.86, 14.08, ""),
    ("از", 14.10, 14.28, ""), ("سیگنال‌ها", 14.28, 14.68, "g"), ("استفاده", 14.68, 15.08, ""),
    ("بکنین", 15.08, 15.42, ""),
    # EDU
    ("شما", 15.44, 15.66, ""), ("اگر", 15.66, 16.04, ""), ("آموزش", 16.04, 16.44, "g"),
    ("دیده", 16.44, 16.68, "g"), ("باشین", 16.68, 17.00, ""), ("یا", 17.00, 17.16, ""),
    ("آموزش", 17.16, 17.54, "g"), ("ندیده", 17.54, 17.92, "g"), ("باشین", 17.92, 18.26, ""),
    # EASY_A / EASY_B
    ("سیگنال‌های", 18.28, 19.18, "g"), ("ما", 19.18, 19.28, ""), ("طوری", 19.28, 19.62, ""),
    ("هست", 19.62, 20.04, ""),
    ("که", 20.06, 20.48, ""), ("خیلی", 20.48, 21.24, ""), ("سهل", 21.24, 21.72, "m"),
    ("و", 21.72, 21.76, "m"), ("آسون", 21.76, 22.22, "m"),
    ("شما", 22.22, 22.46, ""), ("بتونین", 22.46, 22.88, ""), ("سودهاتونو", 22.88, 23.82, "g"),
    ("بگیرین", 23.82, 24.36, ""),
    # CTA_A / CTA_B
    ("برای", 24.42, 24.66, ""), ("دریافت", 24.66, 25.18, ""), ("کانال", 25.18, 25.58, "g"),
    ("لطفاً", 25.58, 25.78, ""),
    ("کلمه‌ی", 25.84, 26.18, ""), ("«کانال»", 26.18, 26.58, "g"), ("رو", 26.58, 26.70, ""),
    ("برای", 26.70, 26.90, ""), ("من", 26.90, 27.00, ""), ("کامنت", 27.00, 27.40, "g"),
    ("بکنین", 27.40, 27.78, ""),
    # DM
    ("دایرکت‌تونو", 27.82, 28.50, "g"), ("چک", 28.50, 28.82, "g"), ("بکنین", 28.82, 29.26, ""),
    # SHARE
    ("برای", 29.32, 29.54, ""), ("دوستانتونم", 29.54, 30.24, "g"), ("ارسال", 30.24, 30.80, "g"),
    ("بکنین", 30.80, 31.14, ""),
    # SIGNOFF (end card takes over)
    ("موفق", 31.20, 31.60, "g"), ("باشید", 31.60, 31.98, ""),
]
CHUNK_SIZES = [3, 3, 1, 1, 1, 3, 3, 2, 1, 3, 3, 2, 3, 3, 4, 5, 4, 4, 5, 4, 4, 3, 4, 3, 4, 2]
NO_CAPTION_SHOTS = {"HOOK", "MUST_1", "MUST_2", "MUST_3", "SIGNOFF"}


def _to_src(t_out):
    acc = 0.0
    for _tag, a, b, *_ in SHOTS:
        if acc - 1e-6 <= t_out <= acc + (b - a) + 1e-6:
            return a + t_out - acc
        acc += b - a
    raise ValueError(t_out)


WORDS = [(w, _to_src(a), _to_src(b), k) for w, a, b, k in WORDS_OUT]

tlcore.setup(globals())
MUSIC_DROPS = [(SHOT["CTA_A"]["out_in"] - 0.15, None)]  # 2-beat drop marks the CTA turn


def oo(t):
    """Readability alias: times below are already output seconds."""
    return t


# ====================================================================== scenes
def scene_hook(t, L, B):
    s = S["HOOK"]
    if not (s["out_in"] <= t < s["out_out"]):
        return
    ex = s["out_out"] - 0.2
    e = prog(t, ex, 0.2)
    # "کانال تلگرام" pill
    k = out_back(prog(t, 0.04, 0.35), 1.8)
    pill(L, W / 2, 330, "کانال تلگرام", "plane", TG_BLUE, k=k * (1 + 0.4 * e), a=prog(t, 0.04, 0.1) * (1 - e))
    # giant "VIP" that lives behind the speaker's head
    if t >= 0.80:
        kv = 0.6 + 0.4 * out_back(prog(t, 0.80, 0.42))
        sp = text("VIP", "Black", 320, GOLD, stroke=6, stroke_fill=(60, 38, 4), shadow=10,
                  glow=(255, 170, 30), gradient=(GOLD_HI, GOLD_LO))
        put(B, sp, W / 2, 600, scale=kv * (1 + 0.5 * in_cubic(e)), alpha=prog(t, 0.80, 0.1) * (1 - e))
        put(L, icon("crown", 96, GOLD), W / 2 + 205, 455, scale=out_back(prog(t, 0.95, 0.3), 2.4) * (1 - e),
            rot=-18, alpha=1 - e)
    # access card: padlock opens on "رایگان"
    t0 = 1.36
    if t >= t0:
        k = out_back(prog(t, t0, 0.4), 1.3)
        a = prog(t, t0, 0.1) * (1 - e)
        y = 1350 + (1 - k) * 220
        opened = prog(t, 1.72, 0.30)
        col = tuple(int(c0 + (c1 - c0) * opened) for c0, c1 in zip(GOLD, GREEN))
        put(L, panel(700, 190, 46, INK, 232, border=col, border_a=200), W / 2, y, alpha=a)
        put(L, G.padlock(110, round(out_cubic(opened) * 20) / 20, col, INK), W / 2 + 250, y - 6, alpha=a)
        put(L, text("دسترسی VIP", "Black", 60, WHITE), W / 2 + 170, y - 26, alpha=a, anchor="r")
        put(L, text("اشتراک کانال تلگرام", "Medium", 36, GRAY), W / 2 + 170, y + 42, alpha=a, anchor="r")
        if t >= 1.72:
            ks = 1 + 0.9 * (1 - out_cubic(prog(t, 1.72, 0.22)))
            st = panel(250, 96, 22, GREEN, 255, border=WHITE, border_a=255)
            put(L, st, W / 2 - 245, y - 88, scale=ks, alpha=a * prog(t, 1.72, 0.06), rot=8)
            put(L, text("رایگان!", "Black", 58, WHITE), W / 2 - 245, y - 86, scale=ks,
                alpha=a * prog(t, 1.72, 0.06), rot=8)


MUST_STYLE = [(250, 86, WHITE, -4), (375, 108, GOLD, 3), (520, 132, RED, -2)]


def scene_must(t, L):
    t_end = S["BOT"]["out_in"] + 0.25
    if not (S["MUST_1"]["out_in"] <= t < t_end + 0.25):
        return
    for j, tag in enumerate(("MUST_1", "MUST_2", "MUST_3")):
        y, size, col, rot = MUST_STYLE[j]
        shake = 6 * math.sin((t - S[tag]["out_in"]) * 70) * (1 - prog(t, S[tag]["out_in"], 0.25))
        kinetic(L, t, S[tag]["out_in"], "حتماً", y, size, col, exit_t=t_end, rot=rot + shake * 0.3,
                glow=(255, 120, 60) if j == 2 else None, x=W / 2 + shake)


def bot_card(L, t, t0, t_exit, y, sub=None, glow_t=None):
    al, ki, ke = life(t, t0, t_exit, 0.35, 0.2)
    if not al:
        return
    k = out_back(ki, 1.5)
    a = min(1, ki * 2) * (1 - ke)
    bounce = 1.0
    if glow_t is not None and t >= glow_t:
        bounce = 1 + 0.08 * math.sin(math.pi * prog(t, glow_t, 0.3))
    put(L, panel(760, 170, 44, INK, 230, border=TG_BLUE, border_a=200), W / 2, y, scale=k * bounce, alpha=a)
    ix = W / 2 + 270 * k
    put(L, icon("disc", 116, TG_BLUE), ix, y, scale=k * bounce, alpha=a)
    put(L, icon("robot", 70, WHITE, TG_BLUE), ix, y, scale=k * bounce, alpha=a)
    put(L, text("رباتمون", "Black", 62, WHITE), ix - 90 * k, y - (24 if sub else 0) * k, scale=k, alpha=a, anchor="r")
    if sub:
        put(L, text(sub, "Bold", 34, GOLD), ix - 90 * k, y + 40 * k, scale=k, alpha=a, anchor="r")
    # "start" button, pulsing
    bx = W / 2 - 250 * k
    ph = (t * 1.4) % 1
    put(L, icon("ring", 120, TG_BLUE), bx, y, scale=k * (0.8 + 0.5 * ph), alpha=a * (1 - ph))
    put(L, panel(170, 76, 38, TG_BLUE, 255, shadow=False), bx, y, scale=k, alpha=a)
    put(L, text("شروع", "Black", 40, WHITE), bx, y + 2, scale=k, alpha=a)


def scene_bot(t, L):
    bot_card(L, t, 4.28, S["BOT"]["out_out"], 360)


def scene_exchanges(t, L):
    t_in, t_out = 5.50, S["EX_C"]["out_out"] + 0.30
    al, ki, ke = life(t, t_in, t_out, 0.3, 0.25)
    if not al:
        return
    a = (1 - ke)
    kinetic(L, t, t_in, "از طریق صرافی", 255, 60, WHITE, exit_t=t_out - 0.2)
    chips = [(6.92, "اوربیت", W / 2 + 225), (8.38, "ال‌بنک", W / 2 - 225)]
    for t0, lab, x in chips:
        if t < t0:
            continue
        k = out_back(prog(t, t0, 0.35), 1.8)
        put(L, panel(380, 124, 40, INK, 235, border=GOLD, border_a=180), x, 400, scale=k, alpha=a)
        put(L, icon("exchange", 76, INK, GOLD), x + 125 * k, 400, scale=k, alpha=a)
        put(L, text(lab, "Black", 54, WHITE), x - 35 * k, 403, scale=k, alpha=a)
    if t >= 7.74:
        k = out_back(prog(t, 7.74, 0.3), 2.4)
        put(L, icon("disc", 84, GOLD), W / 2, 400, scale=k, alpha=a)
        put(L, text("یا", "Black", 40, INK), W / 2, 403, scale=k, alpha=a)


def scene_link(t, L):
    s = S["LINK"]
    bot_card(L, t, s["out_in"] + 0.05, s["out_out"], 330,
             sub="لینک صرافی‌ها داخل ربات" if t >= 10.26 else None, glow_t=10.60)
    # link chip flies into the bot on "گذاشتم"
    t0, t1 = 9.38, 10.26
    if t0 <= t < t1 + 0.1:
        k = out_back(prog(t, t0, 0.25), 2)
        p = inout_(prog(t, 9.80, t1 - 9.80))
        x = 270 + (W / 2 + 270 - 270) * p
        y = 600 - 270 * p - 120 * math.sin(math.pi * p)
        sc = k * (1 - 0.55 * p)
        put(L, panel(300, 84, 42, WHITE, 250), x, y, scale=sc, alpha=1 - prog(t, t1, 0.1))
        put(L, icon("link", 50, (64, 156, 255)), x + 95 * sc, y, scale=sc, alpha=1 - prog(t, t1, 0.1))
        put(L, text("لینک", "Black", 44, INK), x - 25 * sc, y + 2, scale=sc, alpha=1 - prog(t, t1, 0.1))
    if t >= t1:  # landing burst
        p = prog(t, t1, 0.4)
        if p < 1:
            put(L, icon("ring", 200, GOLD), W / 2 + 270, 330, scale=0.5 + 0.9 * p, alpha=1 - p)


def inout_(x):
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


STEPS_A = [("ثبت‌نام با رفرال", 11.26, 12.74), ("ورود به کانال", 13.14, 13.86),
           ("استفاده از سیگنال‌ها", 14.28, 15.08)]
STEPS_B = [("کامنت «کانال»", 25.84, 27.40), ("چک دایرکت", 27.82, 28.82), ("ارسال برای دوستان", 29.54, 30.80)]


def scene_steps(t, L):
    stepper(L, t, STEPS_A, S["SIGNUP"]["out_in"], S["SIGNAL"]["out_out"])
    stepper(L, t, STEPS_B, S["CTA_B"]["out_in"], S["SHARE"]["out_out"])
    # context chips under the first stepper
    for t0, t1, lab, ic, col in [(12.32, 13.10, "با کد رفرال ما", "tag", GOLD),
                                 (13.46, 14.20, "کانال VIP", "crown", GOLD),
                                 (14.28, 15.30, "سیگنال‌ها", "chart", GREEN)]:
        al, ki, ke = life(t, t0, t1, 0.3, 0.18)
        if al:
            pill(L, W / 2, 420 - ke * 30, lab, ic, INK, k=out_back(ki, 1.8), a=min(1, ki * 3) * (1 - ke),
                 size=44, ic_col=INK, ic_bg=col)


def scene_edu(t, L):
    t_in, t_out = 16.04, S["EASY_A"]["out_out"]
    al, _, ke = life(t, t_in, t_out, 0.3, 0.2)
    if not al:
        return
    a = 1 - ke
    ok_t = 18.28  # "سیگنال‌های ما ..." -> both qualify
    for t0, lab, ic, x in [(16.04, "آموزش‌دیده", "cap", W / 2 + 230), (17.16, "آموزش‌ندیده", "sprout", W / 2 - 230)]:
        if t < t0:
            continue
        k = out_back(prog(t, t0, 0.35), 1.6)
        put(L, panel(400, 230, 44, INK, 232, border=GOLD, border_a=120), x, 400, scale=k, alpha=a)
        put(L, icon(ic, 96, GOLD), x, 350, scale=k, alpha=a)
        put(L, text(lab, "Black", 50, WHITE), x, 455, scale=k, alpha=a)
        if t >= ok_t:
            kk = out_back(prog(t, ok_t + (0 if x > W / 2 else 0.12), 0.3), 2.5)
            put(L, icon("disc", 70, GREEN), x + 170, 300, scale=kk, alpha=a)
            put(L, G.partial_check(70, out_cubic(prog(t, ok_t + 0.1, 0.3)), WHITE, 13), x + 170, 300,
                scale=kk, alpha=a)
    if t >= 17.00:
        k = out_back(prog(t, 17.00, 0.3), 2.4)
        put(L, icon("disc", 84, GOLD), W / 2, 400, scale=k, alpha=a)
        put(L, text("یا", "Black", 40, INK), W / 2, 403, scale=k, alpha=a)


def scene_easy(t, L):
    t_out = S["EASY_B"]["out_out"] - 0.1
    if not (20.40 <= t < t_out + 0.25):
        return
    kinetic(L, t, 20.48, "خیلی", 270, 84, WHITE, exit_t=t_out)
    kinetic(L, t, 21.24, "سهل و آسون", 420, 140, GREEN, exit_t=t_out, glow=(30, 200, 120))
    # smooth underline drawn on "آسون"
    p = out_cubic(prog(t, 21.76, 0.35))
    if p > 0:
        ln = int(560 * p)
        put(L, panel(max(8, ln), 12, 6, GOLD, int(255 * (1 - prog(t, t_out, 0.2))), shadow=False),
            W / 2 + 280 - ln / 2, 520)


def scene_cta(t, L):
    s = S["CTA_A"]
    kinetic(L, t, 24.42, "برای دریافت کانال", 280, 78, WHITE, exit_t=s["out_out"] - 0.15)
    if s["out_in"] <= t < s["out_out"]:
        k = out_back(prog(t, 25.18, 0.3), 2)
        if t >= 25.18:
            pill(L, W / 2, 420, "VIP رایگان", "crown", GREEN, k=k, a=1 - prog(t, s["out_out"] - 0.15, 0.15),
                 size=50, ic_col=GOLD, ic_bg=INK)
    b = S["CTA_B"]
    al, ki, ke = life(t, b["out_in"], b["out_out"], 0.3, 0.15)
    if al:
        a = min(1, ki * 2) * (1 - ke)
        cy = 1385 + (1 - out_back(ki)) * 160
        sent = 27.00
        typed = "" if t >= sent + 0.25 else typed_text("کانال", t, 26.18)
        comment_box(L, t, cy, typed, sent, a)
        if t >= sent + 0.2:
            k = out_back(prog(t, sent + 0.2, 0.35), 1.8)
            by = cy - 20 - 75 * out_cubic(prog(t, sent + 0.2, 0.4))
            put(L, panel(300, 84, 42, GOLD, 255), W / 2 + 250, by, scale=k, alpha=a)
            put(L, text("کانال", "Black", 44, INK), W / 2 + 270, by + 2, scale=k, alpha=a)
            put(L, icon("heart", 34, RED), W / 2 + 145, by, scale=k, alpha=a)
        if t < sent + 0.25:
            k = out_back(prog(t, b["out_in"] + 0.1, 0.3), 2)
            bob = 14 * math.sin((t - b["out_in"]) * 12)
            put(L, icon("arrow_down", 88, GOLD), W / 2 - 330, cy - 120 + bob, scale=k, alpha=a)
    notification(L, t, 27.82, S["DM"]["out_out"], 470, "دایرکت جدید", "لینک کانال VIP",
                 hl_t=28.50, tap_t=28.82, accent=PINK)


def scene_share(t, L):
    s = S["SHARE"]
    al, ki, ke = life(t, s["out_in"] + 0.05, s["out_out"], 0.3, 0.2)
    if not al:
        return
    a = min(1, ki * 2) * (1 - ke)
    cx, cy = W / 2, 470
    friends = [(W / 2 + 300, 560, PINK), (W / 2, 600, TG_BLUE), (W / 2 - 300, 560, GOLD)]
    k0 = out_back(ki, 1.6)
    put(L, icon("disc", 120, GOLD), cx, cy - 60, scale=k0, alpha=a)
    put(L, icon("plane", 64, INK, GOLD), cx - 2, cy - 58, scale=k0, alpha=a)
    for j, (fx, fy, col) in enumerate(friends):
        tj = 29.54 + j * 0.10
        if t < tj:
            continue
        k = out_back(prog(t, tj, 0.3), 2.2)
        put(L, icon("disc", 104, col), fx, fy, scale=k, alpha=a)
        put(L, icon("person", 60, WHITE), fx, fy + 4, scale=k, alpha=a)
        tf = 30.24 + j * 0.09  # a small plane flies to each friend on "ارسال"
        if t >= tf:
            p = out_cubic(prog(t, tf, 0.35))
            if p < 1:
                x = cx + (fx - cx) * p
                y = cy - 60 + (fy - 60 - (cy - 60)) * p - 50 * math.sin(math.pi * p)
                put(L, icon("plane", 40, WHITE), x, y, alpha=a)
            else:
                put(L, icon("disc", 44, GREEN), fx + 40, fy - 40, alpha=a,
                    scale=out_back(prog(t, tf + 0.35, 0.25), 2.5))
                put(L, G.partial_check(44, out_cubic(prog(t, tf + 0.38, 0.25)), WHITE, 13), fx + 40, fy - 40, alpha=a)


def scene_outro(t, L):
    t0 = S["SIGNOFF"]["out_in"] + 0.2  # L-cut: the end card arrives under "موفق باشید"
    if t < t0:
        return
    lt = t - t0
    bd = Image_backdrop(out_cubic(prog(lt, 0, 0.5)))
    if bd is not None:
        L.alpha_composite(bd)
    k1 = out_back(prog(lt, 0.15, 0.4), 1.6)
    put(L, text("همین الان کامنت کن", "Black", 84, WHITE, shadow=10), W / 2, 520 - (1 - k1) * 40,
        alpha=prog(lt, 0.15, 0.2))
    k2 = out_back(prog(lt, 0.32, 0.45), 2.2)
    put(L, text("«کانال»", "Black", 150, GOLD, stroke=6, stroke_fill=(50, 30, 0), shadow=12, glow=(255, 150, 0)),
        W / 2, 690, scale=k2, alpha=prog(lt, 0.32, 0.1))
    if lt >= 0.55:
        k3 = out_back(prog(lt, 0.55, 0.45))
        comment_box(L, t, 890 + (1 - k3) * 120, typed_text("کانال", lt, 0.85), a=prog(lt, 0.55, 0.15),
                    pulse=lt > 1.3)
    if lt >= 1.0:
        put(L, icon("arrow_down", 96, GOLD), W / 2, 1040 + 14 * math.sin(lt * 9), scale=out_back(prog(lt, 1.0, 0.3), 2))
    chips = [(1.1, "crown", "کانال VIP تلگرام، کاملاً رایگان", GOLD),
             (1.3, "plane", "لینک کانال در دایرکت شما", PINK),
             (1.5, "person", "برای دوستانت هم بفرست", (42, 171, 238))]
    for j, (td, ic, lab, col) in enumerate(chips):
        if lt < td:
            continue
        k = out_cubic(prog(lt, td, 0.35))
        y = 1190 + j * 104
        put(L, panel(820, 86, 43, INK, 225, border=col, border_a=160), W / 2 + (1 - k) * 120, y, alpha=k)
        put(L, icon(ic, 52, col, INK), W / 2 + 350 + (1 - k) * 120, y, alpha=k)
        put(L, text(lab, "Bold", 40, WHITE), W / 2 + 300 + (1 - k) * 120, y + 2, alpha=k, anchor="r")
    if lt >= 1.8:
        put(L, text("معامله در بازار رمزارز با ریسک همراه است", "Medium", 30, (200, 200, 206)),
            W / 2, 1530, alpha=prog(lt, 1.8, 0.3) * 0.9)


_backdrops = {}


def Image_backdrop(k):
    """Bottom-up darkening for the end card while the picture is still sharp."""
    if k <= 0.01:
        return None
    q = round(k * 20) / 20
    if q not in _backdrops:
        from PIL import Image
        import numpy as np
        col = (np.clip((np.arange(1920) - 250) / 900, 0, 1) ** 0.8 * 205 * q).astype(np.uint8)
        im = Image.new("RGBA", (1080, 1920), INK + (0,))
        im.putalpha(Image.fromarray(np.repeat(col[:, None], 1080, 1)))
        _backdrops[q] = im
    return _backdrops[q]


# ====================================================================== engine hooks
def camera_fx(s, lt):
    """Per-shot camera moves on top of framing + push. -> (zoom mult, blur samples)"""
    mult, nblur = 1.0, 1
    dur = s["out_out"] - s["out_in"]
    if s["tag"] == "HOOK":
        k = prog(lt, 0, 0.36)
        mult *= 1 + 0.20 * (1 - out_cubic(k))
        nblur = 5 if k < 1 else 1
        k2 = prog(lt, dur - 0.20, 0.20)  # whip out
        mult *= 1 + 0.28 * in_cubic(k2)
        if k2 > 0:
            nblur = 7
        if lt >= 1.72:  # punch on "رایگان"
            mult *= 1.06
    elif s["tag"] == "MUST_1":  # whip in
        k = prog(lt, 0, 0.26)
        mult *= 1 + 0.28 * (1 - out_cubic(k))
        nblur = 7 if k < 1 else 1
    elif s["tag"] in ("MUST_2", "MUST_3", "SIGNUP", "CTA_A"):  # beat bumps
        mult *= 1 + 0.05 * (1 - out_cubic(prog(lt, 0, 0.18)))
    elif s["tag"] == "EX_A":  # pull back to the room
        k = prog(lt, 0, 0.30)
        mult *= 1 + 0.22 * (1 - out_cubic(k))
        nblur = 5 if k < 1 else 1
    elif s["tag"] == "EDU" and lt >= 17.00 - s["out_in"]:  # punch on "یا"
        mult *= 1.10
    return mult, nblur


def scrim_windows():
    return [(0.0, S["BOT"]["out_out"]), (S["EX_A"]["out_in"] + 0.1, S["SIGNAL"]["out_out"]),
            (16.0, S["EASY_B"]["out_out"]), (S["CTA_A"]["out_in"], S["SHARE"]["out_out"])]


def caption_y(tag):
    return 1190 if tag == "CTA_B" else 1350


def draw_behind(t, L, B):
    scene_hook(t, L, B)


def draw_front(t, L):
    scene_must(t, L)
    scene_bot(t, L)
    scene_exchanges(t, L)
    scene_link(t, L)
    scene_steps(t, L)
    scene_edu(t, L)
    scene_easy(t, L)
    scene_cta(t, L)
    scene_share(t, L)


def draw_top(t, L):
    scene_outro(t, L)


# ====================================================================== sound
def cues(A):
    c = []
    add = lambda t, fx, g=1.0, pan=0.0: c.append((t, fx, g, pan))
    # HOOK
    add(0.0, A.sfx_impact(), 0.9)
    add(0.0, A.sfx_whoosh(0.35), 0.5)
    add(0.06, A.sfx_pop(), 0.7)
    add(0.80, A.sfx_soft_hit(), 0.8)
    for k in range(4):
        add(0.84 + k * 0.07, A.bell(2093 + k * 330, 0.5, 7.0) * 0.14, 1.0, (-1) ** k * 0.35)
    add(1.36, A.sfx_whoosh(0.35), 0.45, 0.3)
    add(1.70, A.sfx_tick(), 1.0)
    add(1.72, A.sfx_soft_hit(), 0.9)
    add(1.74, A.sfx_success(), 0.55)
    add(S["MUST_1"]["out_in"] - 0.28, A.sfx_whoosh(0.5), 0.75, -0.2)
    # three "حتماً" hits, each a little bigger
    for j, tag in enumerate(("MUST_1", "MUST_2", "MUST_3")):
        add(S[tag]["out_in"], A.sfx_soft_hit(), 0.6 + 0.15 * j)
        add(S[tag]["out_in"], A.sfx_pop(), 0.5 + 0.1 * j)
    add(4.28, A.sfx_pop(), 0.6)
    add(4.30, A.sfx_notify(), 0.35)
    # exchanges
    add(S["EX_A"]["out_in"] - 0.2, A.sfx_whoosh(0.4, up=False), 0.5)
    add(5.50, A.sfx_pop(), 0.5)
    add(6.92, A.sfx_pop(), 0.6, 0.3)
    add(7.74, A.sfx_tick(), 0.8)
    add(8.38, A.sfx_pop(), 0.6, -0.3)
    # link into the bot
    add(S["LINK"]["out_in"] + 0.05, A.sfx_pop(), 0.45)
    add(9.80, A.sfx_whoosh(0.45), 0.6, -0.3)
    add(10.26, A.sfx_tap(), 0.9)
    add(10.28, A.sfx_coin(), 0.25)
    # steps
    add(S["SIGNUP"]["out_in"], A.sfx_pop(), 0.6)
    add(12.32, A.sfx_pop(), 0.5)
    for t in (12.74, 13.86, 15.08):
        add(t, A.sfx_check(), 0.8)
    add(13.46, A.sfx_pop(), 0.5)
    add(14.28, A.sfx_pop(), 0.5)
    # education
    add(16.04, A.sfx_pop(), 0.6, 0.3)
    add(17.00, A.sfx_tick(), 0.8)
    add(17.16, A.sfx_pop(), 0.6, -0.3)
    add(18.28, A.sfx_success(), 0.6)
    # easy
    add(20.48, A.sfx_whoosh(0.3), 0.4)
    add(21.24, A.sfx_soft_hit(), 0.7)
    add(21.76, A.sfx_whoosh(0.35), 0.4, 0.2)
    # CTA
    add(S["CTA_A"]["out_in"] - 0.15, A.sfx_whoosh(0.3), 0.5)
    add(25.18, A.sfx_pop(), 0.5)
    add(S["CTA_B"]["out_in"], A.sfx_pop(), 0.6)
    for k in range(5):
        add(26.18 + k * 0.075, A.sfx_type(), 0.8)
    add(27.00, A.sfx_whoosh(0.25), 0.45, 0.4)
    add(27.02, A.sfx_tap(), 0.8)
    add(27.40, A.sfx_check(), 0.7)
    add(27.82, A.sfx_notify(), 0.85)
    add(28.82, A.sfx_tap(), 0.8)
    for j in range(3):
        add(29.54 + j * 0.10, A.sfx_pop(), 0.45, (j - 1) * 0.4)
        add(30.24 + j * 0.09, A.sfx_whoosh(0.25), 0.3, (j - 1) * 0.5)
    add(30.80, A.sfx_success(), 0.55)
    # outro
    add(BODY_DUR - 1.0, A.sfx_riser(1.0), 0.5)
    add(BODY_DUR, A.sfx_impact(), 0.8)
    for k in range(5):
        add(S["SIGNOFF"]["out_in"] + 0.2 + 0.85 + k * 0.075, A.sfx_type(), 0.6)
    add(S["SIGNOFF"]["out_in"] + 0.2 + 1.3, A.sfx_notify(), 0.5)
    return c
