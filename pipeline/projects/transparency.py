"""Project: «شفاف‌ترین کانال سیگنال» (VID_20261015_073338_440).

Edit decision list as code. All `src` times are seconds in the original
recording (decoded at 30 fps, 720x1280 reference space); all `out` times
are seconds in the edited master."""
import math

import gfx as G
import tlcore
from gfx import (GOLD, GREEN, INK, INK2, RED, WHITE, GRAY,
                 icon, life, out_back, out_cubic, prog, put, text, panel, text_w)
from tlcore import W
from widgets import comment_box, kinetic, notification, pill, stepper, typed_text

SOURCE_NAME = "VID_20261015_073338_440.mp4"
FACE_SRC = (360.0, 620.0)   # speaker's eyes, reference space

# Framing presets for this take (low-res source: keep zoom modest).
WIDE3 = (1.04, 960)
MED3 = (1.16, 860)
CLOSE3 = (1.30, 800)
TIGHT3 = (1.45, 760)

SHOTS = [
    # tag        src_in   src_out  framing  push/s  join
    # --- HOOK: the paying channel's track record
    ("HOOK_A",     5.05,    7.11,  MED3,    0.010, False),  # رفتم یه دونه کانال دیدم
    ("HOOK_B",     7.11,    9.68,  CLOSE3,  0.012, True),   # ده تا دونه در روز کلاً سیگنال می‌ده
    ("HOOK_C",     9.68,   12.62,  MED3,    0.010, True),   # نه تاش استاپ می‌خوره، یه دونه‌ش سود داره
    ("HYPE",      12.62,   16.44,  CLOSE3,  0.010, True),   # اونم کردن تو بوق و کرنا ...
    ("PRICE_A",   16.44,   17.94,  MED3,    0.008, True),   # کاربراش هم همه راضی، ورودیش
    ("PRICE_B",   18.40,   21.14,  TIGHT3,  0.015, False),  # هم دو میلیون و هفتصد هزار تومنه
    # --- reaction (moved from the top of the take, next to what it reacts to)
    ("WALL",       0.81,    5.04,  CLOSE3,  0.012, False),  # اصلاً نمی‌دونم چی بگم ... با سر برم تو دیوار
    # --- transparency
    ("TRANS_A",   21.88,   25.18,  MED3,    0.008, False),  # ما این همه شفاف‌سازی کنیم، سفید کار کنیم
    ("TRANS_B",   25.62,   26.12,  CLOSE3,  0.0,   False),  # یعنی
    ("TRANS_C",   26.62,   31.98,  MED3,    0.008, False),  # شفاف‌تر از پیج ما و سایت ما ...
    ("SITE_A",    31.98,   36.22,  CLOSE3,  0.010, True),   # سایت کوین‌پرو ... تمام سیگنال‌هامونو گذاشتیم
    ("SITE_B",    36.22,   38.72,  MED3,    0.008, True),   # چجوری سود گرفتیم، کدوم تی‌پی سود گرفتیم
    # --- our terms
    ("OURS_A",    44.90,   47.48,  CLOSE3,  0.010, False),  # کلاً پنجاه تتر ورودیمونه
    ("OURS_B",    47.48,   50.24,  MED3,    0.008, True),   # اونم تازه حساب خودتو شارژ می‌کنی
    ("OURS_C",    50.24,   54.12,  CLOSE3,  0.012, True),   # اصلاً به ما پولی نمی‌دی، ورودیمون رایگانه
    # --- ask ChatGPT
    ("GPT_A",     73.00,   77.40,  MED3,    0.008, False),  # اصلاً برو توی ChatGPT بزن ربات تریدیار، ببین
    ("GPT_B",     77.56,   82.76,  CLOSE3,  0.008, False),  # اصلاً کدوم یک از این کامیونیتی‌هایی ...
    ("GPT_C",     82.76,   83.72,  MED3,    0.0,   True),   # توی ChatGPT هستن
    ("GPT_D",     83.72,   85.26,  TIGHT3,  0.010, True),   # ما توی ChatGPT هستیم
    ("GPT_E",     85.26,   90.80,  MED3,    0.008, True),   # برو ما رو سرچ بکن ... واقعیتشون چجوریه
    ("GPT_F",     92.05,   95.79,  CLOSE3,  0.010, False),  # هر سوالی در مورد رباتمون داری از ChatGPT بپرس
    ("GPT_G",     95.79,   99.94,  MED3,    0.010, True),   # دیگه بالاتر از این شفافیت ...
    # --- payoff (mirror of the hook)
    ("RES",       99.94,  103.54,  CLOSE3,  0.012, True),   # بیا تو کانالمون عضوش شو، روزی ده تا تی‌پی می‌زنیم
    ("LANG",     119.62,  122.12,  MED3,    0.010, False),  # دیگه ما نمی‌دونیم به چه زبونی بگیم
    ("TRADE_A",  133.60,  136.40,  MED3,    0.008, False),  # اگه می‌خوای ترید بکنی، بدون دغدغه
    ("TRADE_B",  136.40,  140.44,  CLOSE3,  0.010, True),   # سود بکنی توی این بازار، بیا توی کانال ما سود بگیر
    # --- CTA
    ("CTA_A",    140.44,  142.51,  MED3,    0.006, True),   # کلمه‌ی کانال رو واسه من کامنت بکن
    ("CTA_B",    142.51,  143.94,  CLOSE3,  0.010, True),   # برو دایرکتتو چک کن
    ("CTA_C",    143.94,  149.37,  MED3,    0.008, True),   # اونجا سایتمون رو گذاشتم، کانالمون ... همه‌چیمون هست
    ("CTA_D",    149.37,  150.90,  CLOSE3,  0.012, True),   # شفاف شفاف
    ("SIGNOFF",  151.40,  152.32,  CLOSE3,  0.030, False),  # موفق باشین
]
OUTRO_SRC = (152.32, 152.80)
OUTRO_SPEED = 0.4
OUTRO_DUR = 2.70

# Verbatim transcript (corrected spelling, numerals for numbers). Timings come
# from a word-level re-transcription of the *edited* dialogue (output seconds)
# and are converted to source seconds below.
# k: g = gold keyword, m = green (money / free / good), r = red (stop / price)
WORDS_OUT = [
    ("رفتم", 0.00, 0.74, ""),
    ("یه", 0.74, 0.94, ""),
    ("دونه", 0.94, 1.20, ""),
    ("کانال", 1.20, 1.80, "g"),
    ("دیدم", 1.80, 2.16, ""),
    ("۱۰", 2.16, 2.70, "m"),
    ("تا", 2.70, 2.92, ""),
    ("دونه", 2.92, 3.12, ""),
    ("در", 3.12, 3.42, ""),
    ("روز", 3.42, 3.58, ""),
    ("کلاً", 3.58, 3.86, ""),
    ("سیگنال", 3.86, 4.40, "g"),
    ("می‌ده", 4.40, 4.74, ""),
    ("۹", 4.74, 5.14, "r"),
    ("تاش", 5.14, 5.50, ""),
    ("استاپ", 5.50, 6.00, "r"),
    ("می‌خوره", 6.00, 6.38, ""),
    ("یه", 6.38, 6.58, ""),
    ("دونه‌ش", 6.58, 6.94, ""),
    ("سود", 6.94, 7.16, "m"),
    ("داره", 7.16, 7.50, ""),
    ("اونم", 7.50, 8.04, ""),
    ("کردن", 8.04, 8.42, ""),
    ("تو", 8.42, 8.65, ""),
    ("بوق‌و", 8.65, 8.89, "g"),
    ("کرنا", 8.89, 9.12, "g"),
    ("که", 9.12, 9.34, ""),
    ("آقا", 9.34, 9.52, ""),
    ("ما", 9.52, 9.64, ""),
    ("داریم", 9.64, 10.00, ""),
    ("سود", 10.00, 10.28, "m"),
    ("می‌دیم", 10.28, 10.62, ""),
    ("فلان", 10.62, 10.96, ""),
    ("بیسار", 10.96, 11.30, ""),
    ("کاربراش", 11.30, 11.86, ""),
    ("هم", 11.86, 12.02, ""),
    ("همه", 12.02, 12.20, ""),
    ("راضی", 12.20, 12.66, ""),
    ("ورودیش", 12.66, 13.50, ""),
    ("هم", 13.50, 13.72, ""),
    ("۲", 13.72, 13.92, "r"),
    ("میلیون", 13.92, 14.32, "r"),
    ("و", 14.32, 14.42, ""),
    ("۷۰۰", 14.42, 14.84, "r"),
    ("هزار", 14.84, 15.14, "r"),
    ("تومنه", 15.14, 15.58, "r"),
    ("اصلاً", 15.58, 16.02, ""),
    ("نمی‌دونم", 16.02, 16.80, ""),
    ("چی", 16.80, 17.06, ""),
    ("بگم", 17.06, 17.32, ""),
    ("اصلاً", 17.32, 17.60, ""),
    ("وای", 17.60, 18.06, ""),
    ("دوس‌دارم", 18.06, 18.38, ""),
    ("با", 18.38, 18.70, ""),
    ("سر", 18.70, 18.98, ""),
    ("برم", 18.98, 19.24, ""),
    ("تو", 19.24, 19.40, ""),
    ("دیوار", 19.40, 19.62, "r"),
    ("ما", 19.88, 20.04, ""),
    ("این", 20.04, 20.40, ""),
    ("همه", 20.40, 20.62, ""),
    ("شفاف‌سازی", 20.62, 21.46, "g"),
    ("کنیم", 21.46, 21.74, ""),
    ("سفید", 21.74, 22.44, "g"),
    ("کار", 22.44, 22.76, ""),
    ("کنیم", 22.76, 23.12, ""),
    ("یعنی", 23.12, 23.36, ""),
    ("شفاف‌تر", 23.36, 24.72, "g"),
    ("از", 24.72, 24.96, ""),
    ("پیج", 24.96, 25.40, "g"),
    ("ما", 25.40, 25.66, ""),
    ("و", 25.66, 25.94, ""),
    ("سایت", 25.94, 26.48, "g"),
    ("ما", 26.48, 26.68, ""),
    ("اصلاً", 26.68, 26.98, ""),
    ("نداریم", 26.98, 27.66, ""),
    ("تو", 27.66, 27.80, ""),
    ("کامیونیتی", 27.80, 28.44, "g"),
    ("فارسی", 28.44, 29.00, "g"),
    ("سایت", 29.00, 29.82, "g"),
    ("coinepro.com", 29.82, 31.00, "g"),
    ("می‌تونی", 31.00, 31.30, ""),
    ("بری", 31.30, 31.54, ""),
    ("تمام", 31.54, 32.00, ""),
    ("سیگنال‌هامونو", 32.00, 32.78, "g"),
    ("گذاشتیم", 32.78, 33.34, ""),
    ("چجوری", 33.34, 33.68, ""),
    ("سود", 33.68, 33.98, "m"),
    ("گرفتیم", 33.98, 34.40, ""),
    ("کدوم", 34.40, 34.74, ""),
    ("تی‌پی", 34.74, 35.04, "g"),
    ("سود", 35.04, 35.34, "m"),
    ("گرفتیم", 35.34, 35.76, ""),
    ("کلاً", 35.76, 36.12, ""),
    ("۵۰", 36.12, 36.84, "m"),
    ("تتر", 36.84, 37.38, "m"),
    ("ورودیمونه", 37.38, 38.38, ""),
    ("اونم", 38.38, 38.72, ""),
    ("تازه", 38.72, 39.38, ""),
    ("حساب", 39.38, 39.76, ""),
    ("خودتو", 39.76, 40.24, ""),
    ("شارژ", 40.24, 40.66, ""),
    ("می‌کنی", 40.66, 41.14, ""),
    ("اصلاً", 41.14, 41.68, ""),
    ("به", 41.68, 42.20, ""),
    ("ما", 42.20, 42.36, ""),
    ("پولی", 42.36, 42.82, "r"),
    ("نمی‌دی", 42.82, 43.28, ""),
    ("ورودیمون", 43.28, 44.00, ""),
    ("رایگانه", 44.00, 44.86, "m"),
    ("اصلاً", 44.86, 45.48, ""),
    ("برو", 45.48, 45.76, ""),
    ("توی", 45.76, 46.02, ""),
    ("ChatGPT", 46.02, 46.78, "g"),
    ("بزن", 46.78, 47.22, ""),
    ("ربات", 47.22, 47.86, "g"),
    ("تریدیار", 47.86, 48.74, "g"),
    ("ببین", 48.74, 49.50, ""),
    ("اصلاً", 49.50, 49.76, ""),
    ("کدوم‌یکی", 49.76, 50.64, ""),
    ("از", 50.64, 50.70, ""),
    ("این", 50.70, 50.88, ""),
    ("کامیونیتی‌هایی", 50.88, 51.68, ""),
    ("که", 51.68, 51.76, ""),
    ("دارن", 51.76, 52.02, ""),
    ("الان", 52.02, 52.26, ""),
    ("توی", 52.26, 52.44, ""),
    ("سیگنال", 52.44, 53.36, "g"),
    ("VIP", 53.36, 53.82, "g"),
    ("کار", 53.82, 54.10, ""),
    ("می‌کنن", 54.10, 54.48, ""),
    ("توی", 54.48, 54.68, ""),
    ("ChatGPT", 54.68, 55.34, "g"),
    ("هستن", 55.34, 55.54, ""),
    ("ما", 55.54, 55.76, ""),
    ("توی", 55.76, 56.00, ""),
    ("ChatGPT", 56.00, 56.58, "g"),
    ("هستیم", 56.58, 57.06, ""),
    ("برو", 57.06, 57.50, ""),
    ("ما", 57.50, 57.66, ""),
    ("رو", 57.66, 57.84, ""),
    ("سرچ", 57.84, 58.14, ""),
    ("بکن", 58.14, 58.46, ""),
    ("بگو", 58.46, 59.08, ""),
    ("به", 59.08, 59.20, ""),
    ("ChatGPT", 59.20, 59.78, "g"),
    ("آقا", 59.78, 60.00, ""),
    ("سودشون", 60.00, 60.50, ""),
    ("چجوریه", 60.50, 61.02, ""),
    ("واقعیتشون", 61.02, 61.88, ""),
    ("چجوریه", 61.88, 62.48, ""),
    ("هر", 62.48, 63.32, ""),
    ("سؤالی", 63.32, 63.78, ""),
    ("در", 63.78, 63.98, ""),
    ("مورد", 63.98, 64.30, ""),
    ("رباتمون", 64.30, 64.96, "g"),
    ("داری", 64.96, 65.16, ""),
    ("از", 65.16, 65.34, ""),
    ("ChatGPT", 65.34, 65.90, "g"),
    ("بپرس", 65.90, 66.32, ""),
    ("دیگه", 66.32, 66.84, ""),
    ("بالاتر", 66.84, 67.48, ""),
    ("از", 67.48, 67.68, ""),
    ("این", 67.68, 67.80, ""),
    ("شفافیت", 67.80, 68.50, "g"),
    ("دیگه", 68.50, 68.72, ""),
    ("بعید", 68.72, 69.06, ""),
    ("می‌دونم", 69.06, 69.46, ""),
    ("کسی", 69.46, 69.74, ""),
    ("داشته", 69.74, 70.10, ""),
    ("باشه", 70.10, 70.48, ""),
    ("بیا", 70.48, 71.00, ""),
    ("تو", 71.00, 71.10, ""),
    ("کانالمون", 71.10, 71.64, "g"),
    ("عضوش‌شو", 71.64, 72.08, ""),
    ("روزی", 72.08, 72.50, ""),
    ("۱۰", 72.50, 72.92, "m"),
    ("تا", 72.92, 73.18, ""),
    ("تی‌پی", 73.18, 73.46, "g"),
    ("می‌زنیم", 73.46, 74.04, ""),
    ("دیگه", 74.04, 74.90, ""),
    ("ما", 74.90, 75.04, ""),
    ("نمی‌دونیم", 75.04, 75.54, ""),
    ("به", 75.54, 75.64, ""),
    ("چه", 75.64, 75.78, ""),
    ("زبونی", 75.78, 76.14, ""),
    ("بگیم", 76.14, 76.50, ""),
    ("اگر", 76.50, 77.04, ""),
    ("می‌خوای", 77.04, 77.34, ""),
    ("ترید", 77.34, 77.66, "g"),
    ("بکنی", 77.66, 78.10, ""),
    ("بدون", 78.10, 78.72, ""),
    ("دغدغه", 78.72, 79.30, "m"),
    ("سود", 79.30, 80.22, "m"),
    ("بکنی", 80.22, 80.62, ""),
    ("توی", 80.62, 80.80, ""),
    ("این", 80.80, 81.02, ""),
    ("بازار", 81.02, 81.46, ""),
    ("بیا", 81.46, 82.00, ""),
    ("توی", 82.00, 82.20, ""),
    ("کانالمون", 82.20, 82.72, "g"),
    ("سود", 82.72, 83.02, "m"),
    ("بگیر", 83.02, 83.34, ""),
    ("کلمه‌ی", 83.34, 84.14, ""),
    ("کانالو", 84.14, 84.54, "g"),
    ("واسه", 84.54, 84.78, ""),
    ("من", 84.78, 84.92, ""),
    ("کامنت", 84.92, 85.32, "g"),
    ("بکن", 85.32, 85.70, ""),
    ("برو", 85.70, 85.98, ""),
    ("دایرکتتو", 85.98, 86.62, "g"),
    ("چک", 86.50, 86.70, ""),
    ("کن", 86.70, 86.94, ""),
    ("اونجا", 87.14, 87.42, ""),
    ("سایتمونو", 87.42, 88.06, "g"),
    ("گذاشتم", 88.06, 88.68, ""),
    ("کانالمونو", 88.68, 89.60, "g"),
    ("گذاشتم", 89.60, 90.16, ""),
    ("رباتمونو", 90.16, 90.82, "g"),
    ("گذاشتم", 90.82, 91.18, ""),
    ("همه‌چیمون", 91.18, 92.06, ""),
    ("هست", 92.06, 92.26, ""),
    ("شفاف", 92.26, 93.20, "g"),
    ("شفاف", 93.20, 93.86, "g"),
    ("موفق", 93.86, 94.30, "m"),
    ("باشین", 94.30, 94.80, ""),
]
NO_CAPTION_SHOTS = {"SIGNOFF"}
CAPTION_PLATE = True  # captions sit over the lit microphone in this take


def _shots_out():
    acc, res = 0.0, []
    for tag, a, b, *_ in SHOTS:
        res.append((tag, a, acc, acc + (b - a)))
        acc += b - a
    return res


def _words_src():
    """Assign each word to the shot holding its midpoint, clamp it inside that
    shot, convert to source seconds."""
    out = []
    so = _shots_out()
    for w, a, b, k in WORDS_OUT:
        mid = (a + b) / 2
        for tag, src_in, o0, o1 in so:
            if o0 <= mid < o1 or (tag == so[-1][0] and mid >= o0):
                a2, b2 = max(a, o0), min(b, o1 - 0.01)
                out.append((w, src_in + a2 - o0, src_in + max(b2, a2 + 0.05) - o0, k, tag))
                break
    return out


_WS = _words_src()
WORDS = [w[:4] for w in _WS]


PHRASE_END = {"دیدم", "می‌ده", "می‌خوره", "داره", "کرنا", "بیسار", "راضی", "تومنه", "بگم", "دیوار", "کنیم",
              "فارسی", "بری", "گذاشتیم", "گرفتیم", "ورودیمونه", "می‌کنی", "نمی‌دی", "رایگانه", "تریدیار", "ببین",
              "هستن", "هستیم", "بکن", "چجوریه", "بپرس", "شفافیت", "باشه", "عضوش‌شو", "می‌زنیم", "بگیم",
              "بکنی", "دغدغه", "بازار", "بگیر", "کن", "گذاشتم", "هست", "شفاف"}


def _split(widths, n0=0):
    n = len(widths)
    k = math.ceil(n / 4)
    while True:
        base, extra = divmod(n, k)
        parts = [base + (1 if j < extra else 0) for j in range(k)]
        pos, ok = 0, True
        for m in parts:
            ok &= sum(widths[pos:pos + m]) <= 800
            pos += m
        if ok or k == n:
            return parts
        k += 1


def _chunks():
    """Caption chunks: break at phrase ends, then balance long phrases into
    <= 4 words / <= 800 px; tiny phrases merge with a neighbour when they fit.
    Never across a shot boundary."""
    phrases = []  # (tag, [widths])
    for w, *_, tag in _WS:
        if not phrases or phrases[-1][0] != tag or phrases[-1][2]:
            phrases.append([tag, [], False])
        phrases[-1][1].append(text_w(w, "Black", 66) + 18)
        phrases[-1][2] = w in PHRASE_END
    merged = []
    for ph in phrases:
        if merged and merged[-1][0] == ph[0] and (len(ph[1]) == 1 or len(merged[-1][1]) == 1) \
                and len(merged[-1][1]) + len(ph[1]) <= 4 and sum(merged[-1][1]) + sum(ph[1]) <= 800:
            merged[-1][1] += ph[1]
        else:
            merged.append([ph[0], list(ph[1])])
    sizes = []
    for _tag, widths in merged:
        sizes += _split(widths)
    return sizes


CHUNK_SIZES = _chunks()

tlcore.setup(globals())
MUSIC_DROPS = [(SHOT["WALL"]["out_in"] - 0.1, SHOT["WALL"]["out_out"] - 0.05),
               (SHOT["CTA_A"]["out_in"] - 0.15, None)]

TG_BLUE = (42, 171, 238)
PINK = (233, 62, 120)
GLASS = (210, 236, 255)


def fa_num(n):
    return f"{n:,}".replace(",", "٬").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


# ====================================================================== widgets (this video)
def tiles(L, t, cx, cy, t_in, states, scale=1.0, a=1.0):
    """2x5 signal tiles. states: list of (t_change, kind) per tile, kind in {'red','green'}."""
    for j in range(10):
        r, c = divmod(j, 5)
        x = cx + (2 - c) * 104 * scale            # RTL: first tile on the right
        y = cy + (r - 0.5) * 104 * scale
        td = t_in + j * 0.045
        if t < td:
            continue
        k = out_back(prog(t, td, 0.25), 2.2) * scale
        col, mark = INK2, None
        tc, kind = states[j] if states else (None, None)
        if tc is not None and t >= tc:
            p = prog(t, tc, 0.18)
            col = RED if kind == "red" else GREEN
            mark = ("cross" if kind == "red" else "check", p)
            k *= 1 + 0.15 * math.sin(math.pi * p)
        put(L, panel(92, 92, 22, col, 240, border=WHITE, border_a=40), x, y, scale=k, alpha=a)
        if mark:
            name, p = mark
            if name == "check":
                put(L, G.partial_check(70, out_cubic(p), WHITE, 13), x, y, scale=k, alpha=a)
            else:
                put(L, icon("cross", 62, WHITE), x, y, scale=k * out_back(p, 2), alpha=a)
        else:
            put(L, icon("chart", 46, (120, 124, 134)), x, y, scale=k, alpha=a)


def label(L, t, t0, s, y, col, exit_t=None, size=46):
    if t < t0 or (exit_t is not None and t > exit_t + 0.2):
        return
    k = out_back(prog(t, t0, 0.3), 1.8)
    a = prog(t, t0, 0.08) * (1 - (prog(t, exit_t, 0.2) if exit_t else 0))
    w = text_w(s, "Black", size) + 70
    put(L, panel(int(w), int(size * 1.9), int(size * 0.95), col, 245), W / 2, y, scale=k, alpha=a)
    put(L, text(s, "Black", size, WHITE if col != WHITE else INK), W / 2, y + 2, scale=k, alpha=a)


def card(L, x, y, w, h, k, a, border=GOLD, fill=INK, alpha=232):
    put(L, panel(w, h, 40, fill, alpha, border=border, border_a=170), x, y, scale=k, alpha=a)


def shine(L, t, t0, x, y, w, h, dur=0.6):
    """Glass highlight sweeping across a w x h box (transparency metaphor)."""
    p = prog(t, t0, dur)
    if p <= 0 or p >= 1:
        return
    band = panel(70, int(h * 1.3), 20, WHITE, 120, shadow=False)
    put(L, band, x + w / 2 - p * (w + 70), y, rot=-18, alpha=math.sin(math.pi * p))


# ====================================================================== scenes
def scene_hook(t, L):
    t1 = S["HYPE"]["out_in"] + 0.6
    if t >= t1 + 0.3:
        return
    a = 1 - prog(t, t1, 0.25)
    al, ki, _ = life(t, 0.05, 99, 0.35, 0.1)
    # channel card
    if t < S["HOOK_B"]["out_in"] + 0.1:
        e = prog(t, S["HOOK_B"]["out_in"] - 0.1, 0.2)
        pill(L, W / 2, 320, "یه کانال سیگنال", "plane", INK, k=out_back(ki, 1.6) * (1 - 0.3 * e),
             a=min(1, ki * 2) * (1 - e), size=50, ic_col=WHITE, ic_bg=TG_BLUE)
        return
    states = [(4.80 + j * 0.10, "red") for j in range(9)] + [(6.94, "green")]
    tiles(L, t, W / 2, 330, 2.16, states, a=a)
    if t < 4.74:
        label(L, t, 3.42, "۱۰ سیگنال در روز", 520, INK, exit_t=4.70)
    elif t < 6.40:
        label(L, t, 5.50, "۹ تاش استاپ", 520, RED, exit_t=6.36)
    else:
        label(L, t, 6.94, "فقط ۱ سود", 520, GREEN, exit_t=t1)


def scene_hype(t, L):
    s = S["HYPE"]
    if not (s["out_in"] + 0.3 <= t < S["PRICE_A"]["out_out"]):
        return
    e = prog(t, S["PRICE_A"]["out_out"] - 0.2, 0.2)
    # megaphone blasting the single green tile
    k = out_back(prog(t, 8.42, 0.35), 2)
    if t >= 8.42:
        wob = 4 * math.sin(t * 40) * (1 - prog(t, 8.42, 0.8))
        put(L, icon("disc", 150, GOLD), W / 2 + 280, 330, scale=k, alpha=1 - e)
        put(L, icon("megaphone", 96, INK, GOLD), W / 2 + 280, 330, scale=k, alpha=1 - e, rot=8 + wob)
        put(L, panel(92, 92, 22, GREEN, 240), W / 2 + 80, 330, scale=k, alpha=1 - e)
        put(L, G.partial_check(70, 1, WHITE, 13), W / 2 + 80, 330, scale=k, alpha=1 - e)
    if t >= 9.52:  # the slogan, in quotes
        kb = out_back(prog(t, 9.52, 0.35), 1.8)
        put(L, panel(520, 110, 55, WHITE, 250), W / 2 - 150, 480, scale=kb, alpha=1 - e)
        put(L, text("«ما داریم سود می‌دیم!»", "Black", 44, INK), W / 2 - 150, 482, scale=kb, alpha=1 - e)
    if t >= 11.3:  # "کاربراش هم همه راضی"
        for j in range(5):
            kj = out_back(prog(t, 11.5 + j * 0.08, 0.25), 2.5)
            put(L, icon("star", 60, GOLD), W / 2 - 300 + j * 70, 620, scale=kj, alpha=1 - e)


def scene_price(t, L):
    s = S["PRICE_B"]
    if not (s["out_in"] <= t < s["out_out"] + 0.2):
        return
    e = prog(t, s["out_out"] - 0.1, 0.25)
    k = out_back(prog(t, s["out_in"], 0.35), 1.6)
    # counter follows the spoken amount: ۲ میلیون ... ۷۰۰ هزار
    if t < 13.92:
        val = 0
    elif t < 14.42:
        val = 2_000_000
    else:
        val = 2_000_000 + int(700_000 * out_cubic(prog(t, 14.42, 0.7)))
    slam = 1 + 0.35 * (1 - out_cubic(prog(t, 15.14, 0.2))) if t >= 15.14 else 1
    put(L, panel(820, 230, 50, INK, 240, border=RED, border_a=230), W / 2, 320, scale=k * slam, alpha=1 - e)
    put(L, text("ورودی این کانال:", "Bold", 40, (255, 190, 190)), W / 2 + 330, 248, scale=k, alpha=1 - e, anchor="r")
    put(L, text(fa_num(val) + " تومان", "Black", 92, RED, glow=(255, 60, 60)), W / 2, 345,
        scale=k * slam, alpha=1 - e)
    put(L, icon("tag", 70, RED, INK), W / 2 - 340, 250, scale=k, alpha=1 - e, rot=-15)


def scene_wall(t, L):
    s = S["WALL"]
    t0 = 19.40  # "دیوار"
    if not (t0 - 0.05 <= t < s["out_out"]):
        return
    p = prog(t, t0, 0.18)
    y = -200 + (360 + 200) * out_cubic(p)
    put(L, icon("bricks", 320, (178, 84, 60), (120, 56, 40)), W / 2, y, alpha=1 - prog(t, s["out_out"] - 0.15, 0.15))
    if p >= 1:  # crack
        c = Image_crack(prog(t, t0 + 0.18, 0.12))
        put(L, c, W / 2, 360)


_cracks = {}


def Image_crack(p):
    q = round(p * 10) / 10
    if q not in _cracks:
        from PIL import Image, ImageDraw
        im = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rays = [(-0.9, 120), (-0.2, 140), (0.5, 110), (1.3, 130), (2.1, 120), (2.9, 100)]
        for ang, ln in rays:
            x, y = 160, 160
            for st in range(4):
                nx = x + math.cos(ang + 0.3 * math.sin(st * 2.1)) * ln * q / 4
                ny = y + math.sin(ang + 0.3 * math.sin(st * 2.1)) * ln * q / 4
                d.line([(x, y), (nx, ny)], fill=(30, 18, 12, 255), width=6)
                x, y = nx, ny
        _cracks[q] = im
    return _cracks[q]


def scene_trans(t, L):
    if not (20.62 <= t < S["TRANS_C"]["out_out"]):
        return
    if t < S["TRANS_B"]["out_in"]:
        e = prog(t, S["TRANS_B"]["out_in"] - 0.2, 0.2)
        k = out_back(prog(t, 20.62, 0.35), 1.6)
        card(L, W / 2, 300, 560, 110, k, 1 - e, border=GLASS, fill=(30, 60, 90), alpha=150)
        put(L, text("شفاف‌سازی", "Black", 60, WHITE), W / 2, 303, scale=k, alpha=1 - e)
        shine(L, t, 20.8, W / 2, 300, 560, 110)
        if t >= 21.74:
            k2 = out_back(prog(t, 21.74, 0.35), 1.6)
            card(L, W / 2, 430, 460, 100, k2, 1 - e, border=WHITE, fill=WHITE, alpha=245)
            put(L, text("سفید کار", "Black", 52, INK), W / 2 - 30, 433, scale=k2, alpha=1 - e)
            put(L, icon("disc", 56, GREEN), W / 2 + 160 * k2, 430, scale=k2, alpha=1 - e)
            put(L, G.partial_check(56, out_cubic(prog(t, 21.9, 0.3)), WHITE, 13), W / 2 + 160 * k2, 430,
                scale=k2, alpha=1 - e)
        return
    s = S["TRANS_C"]
    if t < s["out_in"]:
        return
    e = prog(t, s["out_out"] - 0.15, 0.15)
    for t0, lab, x in [(24.96, "پیج ما", W / 2 + 200), (25.94, "سایت ما", W / 2 - 200)]:
        if t >= t0:
            k = out_back(prog(t, t0, 0.35), 1.8)
            card(L, x, 300, 340, 110, k, 1 - e, border=GLASS, fill=(30, 60, 90), alpha=160)
            put(L, text(lab, "Black", 52, WHITE), x - 30 * k, 303, scale=k, alpha=1 - e)
            put(L, icon("disc", 54, GREEN), x + 120 * k, 300, scale=k, alpha=1 - e)
            put(L, G.partial_check(54, out_cubic(prog(t, t0 + 0.1, 0.3)), WHITE, 13), x + 120 * k, 300,
                scale=k, alpha=1 - e)
    if t >= 27.80:
        kb = out_back(prog(t, 27.80, 0.35), 1.6)
        pill(L, W / 2, 445, "شفاف‌ترین در کامیونیتی فارسی", "crown", INK, k=kb, a=1 - e, size=42,
             ic_col=INK, ic_bg=GOLD)


def browser(L, t, cx, cy, k, a, rows_t=None, profit_t=None, tp_t=None, url_t=None):
    w, h = 860, 340
    put(L, panel(w, h, 30, WHITE, 250), cx, cy, scale=k, alpha=a)
    top = cy - h / 2 * k
    put(L, panel(w, 64, 30, (232, 236, 242), 255, shadow=False), cx, top + 32 * k, scale=k, alpha=a)
    for j, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        put(L, icon("disc", 18, col), cx + (w / 2 - 34 - j * 28) * k, top + 32 * k, scale=k, alpha=a)
    if url_t is not None and t >= url_t:  # address bar lights up when the site is named
        p = prog(t, url_t, 0.6)
        put(L, panel(540, 52, 26, GOLD, int(255 * (1 - 0.6 * p)), shadow=False), cx - 60 * k, top + 32 * k,
            scale=k * (1 + 0.06 * (1 - out_cubic(p))), alpha=a)
    put(L, panel(520, 40, 20, WHITE, 255, shadow=False), cx - 60 * k, top + 32 * k, scale=k, alpha=a)
    put(L, G.padlock(26, 0.0, GREEN, WHITE), cx - 290 * k, top + 32 * k, scale=k, alpha=a)
    put(L, text("coinepro.com", "Black", 30, INK), cx - 60 * k, top + 33 * k, scale=k, alpha=a)
    if rows_t is None:
        return
    for j in range(4):
        tj = rows_t + j * 0.12
        if t < tj:
            continue
        kr = out_cubic(prog(t, tj, 0.3))
        y = top + (100 + j * 62) * k
        put(L, icon("disc", 38, GOLD), cx + (w / 2 - 50) * k, y, scale=k, alpha=a * kr)
        put(L, panel(int(300 * kr) + 4, 16, 8, (214, 218, 226), 255, shadow=False),
            cx + (w / 2 - 90 - 150 * kr) * k, y, scale=k, alpha=a)
        if profit_t is not None and t >= profit_t + j * 0.1:
            kp = out_back(prog(t, profit_t + j * 0.1, 0.3), 2)
            put(L, panel(120, 40, 20, GREEN, 255, shadow=False), cx - 120 * k, y, scale=k * kp, alpha=a)
            put(L, text("سود", "Black", 26, WHITE), cx - 120 * k, y + 1, scale=k * kp, alpha=a)
        if tp_t is not None and t >= tp_t + j * 0.1:
            kt = out_back(prog(t, tp_t + j * 0.1, 0.3), 2)
            put(L, panel(110, 40, 20, INK, 255, shadow=False), cx - 300 * k, y, scale=k * kt, alpha=a)
            put(L, text(f"TP{j % 3 + 1}", "Black", 26, GOLD), cx - 300 * k, y + 1, scale=k * kt, alpha=a)


def scene_site(t, L):
    a_, b_ = S["SITE_A"], S["SITE_B"]
    if not (a_["out_in"] <= t < b_["out_out"]):
        return
    k = out_back(prog(t, a_["out_in"] + 0.05, 0.4), 1.3)
    e = prog(t, b_["out_out"] - 0.2, 0.2)
    browser(L, t, W / 2, 335, k, 1 - e, rows_t=31.54, profit_t=33.68, tp_t=34.74, url_t=29.82)


def scene_ours(t, L):
    a_, c_ = S["OURS_A"], S["OURS_C"]
    if not (a_["out_in"] <= t < c_["out_out"]):
        return
    e = prog(t, c_["out_out"] - 0.2, 0.2)
    k = out_back(prog(t, a_["out_in"] + 0.05, 0.35), 1.4)
    # theirs (left) vs ours (right, RTL reads first)
    xL, xR, y = W / 2 - 235, W / 2 + 235, 345
    card(L, xL, y, 430, 270, k, 1 - e, border=RED)
    put(L, text("اونا", "Black", 44, (255, 160, 160)), xL, y - 90, scale=k, alpha=1 - e)
    put(L, text("۲٬۷۰۰٬۰۰۰ ت", "Black", 54, RED), xL, y - 15, scale=k, alpha=1 - e)
    put(L, text("حق عضویت", "Bold", 34, GRAY), xL, y + 50, scale=k, alpha=1 - e)
    card(L, xR, y, 430, 270, k, 1 - e, border=GREEN)
    put(L, text("ما", "Black", 44, (160, 255, 200)), xR, y - 90, scale=k, alpha=1 - e)
    if t >= 36.12:
        kn = out_back(prog(t, 36.12, 0.3), 2)
        put(L, text("۵۰ تتر", "Black", 64, GREEN, glow=(30, 200, 120)), xR, y - 15, scale=k * kn, alpha=1 - e)
        put(L, text("کف ورود", "Bold", 34, GRAY), xR, y + 50, scale=k * kn, alpha=1 - e)
    put(L, icon("disc", 84, GOLD), W / 2, y, scale=k, alpha=1 - e)
    put(L, text("VS", "Black", 36, INK), W / 2, y + 2, scale=k, alpha=1 - e)
    if t >= 39.38:  # "حساب خودتو شارژ می‌کنی"
        kw = out_back(prog(t, 39.38, 0.35), 1.8)
        pill(L, xR, y + 200, "شارژ حساب خودت", "wallet", INK, k=kw * 0.85, a=1 - e, size=38,
             ic_col=INK, ic_bg=GOLD)
    if t >= 44.0:  # "ورودیمون رایگانه" -> stamp on our card
        ks = 1 + 0.8 * (1 - out_cubic(prog(t, 44.0, 0.22)))
        put(L, panel(300, 90, 20, GREEN, 255, border=WHITE, border_a=255), xR, y + 90, scale=ks,
            alpha=(1 - e) * prog(t, 44.0, 0.05), rot=-7)
        put(L, text("عضویت رایگان", "Black", 42, WHITE), xR, y + 92, scale=ks,
            alpha=(1 - e) * prog(t, 44.0, 0.05), rot=-7)
    elif t >= 42.36:  # "به ما پولی نمی‌دی"
        put(L, text("پرداخت به ما: ۰", "Black", 38, WHITE), xR, y + 100, alpha=(1 - e) * prog(t, 42.36, 0.15))


def chat_panel(L, cx, cy, w, h, k, a):
    put(L, panel(w, h, 34, (24, 26, 32), 240, border=WHITE, border_a=40), cx, cy, scale=k, alpha=a)
    top = cy - h / 2 * k
    put(L, icon("spark", 40, (120, 220, 190)), cx + (w / 2 - 44) * k, top + 40 * k, scale=k, alpha=a)
    put(L, text("ChatGPT", "Black", 36, WHITE), cx + (w / 2 - 80) * k, top + 42 * k, scale=k, alpha=a, anchor="r")
    return top


def bubble(L, t, t0, s, x, y, col=(52, 120, 246), txt=WHITE, a=1.0, right=True):
    if t < t0:
        return
    k = out_back(prog(t, t0, 0.3), 1.8)
    w = text_w(s, "Black", 36) + 56
    put(L, panel(int(w), 70, 35, col, 255, shadow=False), x - (w / 2 if right else -w / 2), y, scale=k, alpha=a)
    put(L, text(s, "Black", 36, txt), x - (w / 2 if right else -w / 2), y + 1, scale=k, alpha=a)


def scene_gpt(t, L):
    if not (S["GPT_A"]["out_in"] <= t < S["GPT_G"]["out_out"]):
        return
    e = prog(t, S["GPT_G"]["out_in"] - 0.2, 0.2)
    if t >= S["GPT_G"]["out_in"]:
        kin = S["GPT_G"]
        kinetic(L, t, 66.80, "بالاتر از این", 270, 64, WHITE, exit_t=kin["out_out"] - 0.25)
        kinetic(L, t, 67.80, "شفافیت؟", 400, 120, GLASS, exit_t=kin["out_out"] - 0.25, glow=(120, 200, 255))
        shine(L, t, 68.1, W / 2, 400, 520, 140, dur=0.7)
        return
    k = out_back(prog(t, S["GPT_A"]["out_in"] + 0.05, 0.4), 1.3)
    a = 1 - e
    tight = S["GPT_D"]["out_in"] <= t < S["GPT_D"]["out_out"]
    cy, h = (320, 300) if not tight else (300, 250)
    top = chat_panel(L, W / 2, cy, 880, h, k, a)
    rx = W / 2 + 400  # right edge for RTL content
    if t < S["GPT_B"]["out_in"]:
        # search box typing the bot's name
        put(L, panel(800, 76, 38, (44, 48, 58), 255, shadow=False), W / 2, top + 130 * k, scale=k, alpha=a)
        typed = typed_text("ربات تریدیار", t, 47.22, per=0.09)
        put(L, text(typed or "جستجو…", "Black" if typed else "Medium", 38, WHITE if typed else GRAY),
            rx - 30, top + 132 * k, alpha=a, anchor="r")
        put(L, icon("spark", 34, GOLD), W / 2 - 360, top + 130 * k, alpha=a)
        return
    if t < S["GPT_E"]["out_in"]:
        # which VIP-signal communities show up? three anonymous rows + ours
        for j in range(3):
            y = top + (115 + j * 62) * k
            ours = j == 0
            hl = ours and t >= 55.54
            dim = 0.35 if (t >= 55.54 and not ours) else 1
            col = GOLD if hl else (52, 56, 66)
            put(L, panel(800, 52, 26, col, 255, shadow=False), W / 2, y, scale=k, alpha=a * dim)
            if hl:
                put(L, text("ربات تریدیار", "Black", 34, INK), rx - 40, y + 1, alpha=a, anchor="r")
                put(L, icon("disc", 40, GREEN), W / 2 - 360, y, alpha=a)
                put(L, G.partial_check(40, out_cubic(prog(t, 55.6, 0.3)), WHITE, 13), W / 2 - 360, y, alpha=a)
            else:
                put(L, panel(260, 14, 7, (90, 96, 110), 255, shadow=False), rx - 170, y, alpha=a * dim)
                if t >= 54.48 and not ours:
                    put(L, text("؟", "Black", 40, (160, 166, 178)), W / 2 - 360, y, alpha=a * dim)
        return
    if t < S["GPT_F"]["out_in"]:
        bubble(L, t, 57.84, "ربات تریدیار", rx, top + 115 * k, a=a)
        bubble(L, t, 60.00, "سودشون چجوریه؟", rx, top + 185 * k, a=a)
        bubble(L, t, 61.02, "واقعیتشون چجوریه؟", rx, top + 255 * k, a=a)
        return
    # GPT_F: ask anything about the bot
    put(L, panel(800, 76, 38, (44, 48, 58), 255, shadow=False), W / 2, top + 150 * k, scale=k, alpha=a)
    put(L, text("هر سؤالی درباره‌ی ربات داری بپرس…", "Medium", 34, (200, 204, 214)), rx - 30, top + 152 * k,
        alpha=a, anchor="r")
    ph = (t * 1.4) % 1
    put(L, icon("ring", 100, GOLD), W / 2 - 350, top + 150 * k, scale=0.7 + 0.5 * ph, alpha=a * (1 - ph))
    put(L, icon("disc", 64, GOLD), W / 2 - 350, top + 150 * k, alpha=a)
    put(L, icon("send", 30, INK, GOLD), W / 2 - 352, top + 150 * k, alpha=a, rot=180)


def scene_res(t, L):
    s = S["RES"]
    if not (s["out_in"] <= t < s["out_out"]):
        return
    e = prog(t, s["out_out"] - 0.2, 0.2)
    if t < 72.50:
        pill(L, W / 2, 320, "کانال VIP ما", "crown", INK, k=out_back(prog(t, s["out_in"] + 0.05, 0.35), 1.8),
             a=1 - e, size=50, ic_col=INK, ic_bg=GOLD)
        return
    states = [(72.70 + j * 0.06, "green") for j in range(10)]
    tiles(L, t, W / 2, 310, 72.50, states, a=1 - e)
    label(L, t, 73.18, "روزی ۱۰ تی‌پی", 500, GREEN, exit_t=s["out_out"] - 0.2)


def scene_lang(t, L):
    s = S["LANG"]
    if not (s["out_in"] <= t < s["out_out"]):
        return
    e = prog(t, s["out_out"] - 0.2, 0.2)
    words = [("شفاف", W / 2, 360, 96, GLASS), ("TRANSPARENT", W / 2 - 200, 230, 46, WHITE),
             ("ŞEFFAF", W / 2 + 280, 250, 46, WHITE), ("TRANSPARENTE", W / 2 + 180, 500, 40, WHITE),
             ("TRANSPARENT", W / 2 - 260, 490, 36, GRAY)]
    for j, (w_, x, y, sz, col) in enumerate(words):
        tj = 75.30 + j * 0.12
        if t < tj:
            continue
        k = out_back(prog(t, tj, 0.3), 2)
        put(L, text(w_, "Black", sz, col, stroke=5, stroke_fill=INK, shadow=6), x, y, scale=k, alpha=1 - e,
            rot=(-6, 4, -3, 5, -4)[j])


def scene_trade(t, L):
    a_, b_ = S["TRADE_A"], S["TRADE_B"]
    if not (a_["out_in"] <= t < b_["out_out"]):
        return
    e = prog(t, b_["out_out"] - 0.2, 0.2)
    if t < b_["out_in"]:
        kinetic(L, t, 77.34, "ترید", 280, 84, WHITE, exit_t=b_["out_in"] - 0.15)
        kinetic(L, t, 78.10, "بدون دغدغه", 420, 110, GREEN, exit_t=b_["out_in"] - 0.15, glow=(30, 200, 120))
        return
    if t >= 81.46:
        pill(L, W / 2, 330, "بیا توی کانال ما", "crown", INK, k=out_back(prog(t, 81.46, 0.35), 1.8),
             a=1 - e, size=52, ic_col=INK, ic_bg=GOLD)


STEPS = [("کامنت «کانال»", 83.45, 84.98), ("چک دایرکت", 85.98, 86.70), ("سایت، کانال، ربات", 87.42, 91.18)]


def scene_cta(t, L):
    stepper(L, t, STEPS, S["CTA_A"]["out_in"], S["CTA_D"]["out_out"])
    a_ = S["CTA_A"]
    al, ki, ke = life(t, a_["out_in"], a_["out_out"], 0.3, 0.15)
    if al:
        a = min(1, ki * 2) * (1 - ke)
        cy = 1385 + (1 - out_back(ki)) * 160
        sent = 84.98
        typed = "" if t >= sent + 0.25 else typed_text("کانال", t, 84.14)
        comment_box(L, t, cy, typed, sent, a)
        if t < sent + 0.25:
            bob = 14 * math.sin((t - a_["out_in"]) * 12)
            put(L, icon("arrow_down", 88, GOLD), W / 2 - 330, cy - 120 + bob,
                scale=out_back(prog(t, a_["out_in"] + 0.1, 0.3), 2), alpha=a)
    notification(L, t, 85.98, S["CTA_B"]["out_out"], 470, "دایرکت جدید", "سایت + کانال + ربات",
                 hl_t=86.50, accent=PINK)
    c_, d_ = S["CTA_C"], S["CTA_D"]
    if c_["out_in"] <= t < d_["out_out"]:
        e = prog(t, d_["out_out"] - 0.15, 0.15)
        items = [(87.42, "سایت", "globe", W / 2 + 290), (88.68, "کانال", "plane", W / 2), (90.16, "ربات", "robot", W / 2 - 290)]
        for t0, lab, ic, x in items:
            if t < t0:
                continue
            k = out_back(prog(t, t0, 0.35), 1.8)
            card(L, x, 470, 260, 190, k, 1 - e, border=GLASS, fill=(30, 60, 90), alpha=170)
            put(L, icon("disc", 84, TG_BLUE if ic != "globe" else GOLD), x, 440, scale=k, alpha=1 - e)
            put(L, icon(ic, 50, WHITE, TG_BLUE), x, 440, scale=k, alpha=1 - e)
            if ic == "globe":
                put(L, text(lab, "Black", 40, WHITE), x, 505, scale=k, alpha=1 - e)
                put(L, text("coinepro.com", "Black", 26, GOLD), x, 545, scale=k, alpha=1 - e)
            else:
                put(L, text(lab, "Black", 44, WHITE), x, 520, scale=k, alpha=1 - e)
            if t >= 91.18:
                kc = out_back(prog(t, 91.18 + (x < W / 2) * 0.1, 0.3), 2.4)
                put(L, icon("disc", 50, GREEN), x + 100, 390, scale=kc, alpha=1 - e)
                put(L, G.partial_check(50, out_cubic(prog(t, 91.25, 0.3)), WHITE, 13), x + 100, 390, scale=kc, alpha=1 - e)
            for ts in (92.26, 93.20):  # "شفاف شفاف"
                shine(L, t, ts + (W / 2 - x) / 2000, x, 470, 260, 190, dur=0.5)


def scene_outro(t, L):
    t0 = S["SIGNOFF"]["out_in"] + 0.15  # L-cut: end card arrives under "موفق باشین"
    if t < t0:
        return
    lt = t - t0
    bd = backdrop(out_cubic(prog(lt, 0, 0.5)))
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
    chips = [(1.1, "wallet", "کف ورود ۵۰ تتر  •  عضویت رایگان", GREEN),
             (1.25, "globe", "همه‌ی سیگنال‌ها در coinepro.com", GOLD),
             (1.4, "plane", "سایت، کانال و ربات در دایرکت", PINK),
             (1.55, "spark", "از ChatGPT بپرس: ربات تریدیار", (120, 220, 190))]
    for j, (td, ic, lab, col) in enumerate(chips):
        if lt < td:
            continue
        k = out_cubic(prog(lt, td, 0.35))
        y = 1180 + j * 96
        put(L, panel(820, 86, 43, INK, 225, border=col, border_a=160), W / 2 + (1 - k) * 120, y, alpha=k)
        put(L, icon(ic, 52, col, INK), W / 2 + 350 + (1 - k) * 120, y, alpha=k)
        put(L, text(lab, "Bold", 38, WHITE), W / 2 + 300 + (1 - k) * 120, y + 2, alpha=k, anchor="r")
    if lt >= 1.8:
        put(L, text("معامله در بازار رمزارز با ریسک همراه است؛ سود گذشته تضمین سود آینده نیست",
                    "Medium", 28, (200, 200, 206)), W / 2, 1560, alpha=prog(lt, 1.8, 0.3) * 0.9)


_backdrops = {}


def backdrop(k):
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
BUMP = {"HOOK_B", "HYPE", "PRICE_B", "TRANS_B", "SITE_A", "OURS_A", "OURS_C", "GPT_B", "GPT_D",
        "GPT_F", "RES", "TRADE_B", "CTA_B", "CTA_D"}


def camera_fx(s, lt):
    """Per-shot camera moves -> (zoom mult, blur samples[, shake x, shake y])."""
    mult, nblur, ox, oy = 1.0, 1, 0.0, 0.0
    tag, t = s["tag"], s["out_in"] + lt
    if tag == "HOOK_A":
        k = prog(lt, 0, 0.36)
        mult *= 1 + 0.18 * (1 - out_cubic(k))
        nblur = 5 if k < 1 else 1
    if tag in BUMP:  # cut-on-beat: land the punch-in with a small settle
        mult *= 1 + 0.045 * (1 - out_cubic(prog(lt, 0, 0.18)))
    if tag == "PRICE_B" and t >= 15.14:  # slam on "تومنه"
        mult *= 1 + 0.05 * (1 - out_cubic(prog(t, 15.14, 0.3)))
    if tag == "WALL" and t >= 19.58:  # head meets wall: short decaying shake
        d = 1 - prog(t, 19.58, 0.32)
        ox = 18 * d * math.sin(t * 95)
        oy = 12 * d * math.cos(t * 77)
        mult *= 1 + 0.04 * d
    if tag == "OURS_C" and t >= 44.0:  # "رایگانه"
        mult *= 1 + 0.04 * (1 - out_cubic(prog(t, 44.0, 0.3)))
    return mult, nblur, ox, oy


def scrim_windows():
    return [(0.0, BODY_DUR)]


def caption_y(tag):
    return 1190 if tag == "CTA_A" else 1380


def draw_behind(t, L, B):
    pass


def draw_front(t, L):
    scene_hook(t, L)
    scene_hype(t, L)
    scene_price(t, L)
    scene_wall(t, L)
    scene_trans(t, L)
    scene_site(t, L)
    scene_ours(t, L)
    scene_gpt(t, L)
    scene_res(t, L)
    scene_lang(t, L)
    scene_trade(t, L)
    scene_cta(t, L)


def draw_top(t, L):
    scene_outro(t, L)


# ====================================================================== sound
def cues(A):
    c = []
    add = lambda t, fx, g=1.0, pan=0.0: c.append((t, fx, g, pan))
    add(0.0, A.sfx_whoosh(0.35), 0.5)
    add(0.06, A.sfx_pop(), 0.6)
    for j in range(10):  # ten tiles
        add(2.16 + j * 0.045, A.sfx_tick(), 0.6, (j % 5 - 2) * 0.2)
    for j in range(9):  # nine stops
        add(4.80 + j * 0.10, A.sfx_strike(), 0.30, (j % 5 - 2) * 0.2)
    add(5.50, A.sfx_soft_hit(), 0.6)
    add(6.94, A.sfx_coin(), 0.45)
    add(8.42, A.sfx_pop(), 0.6)
    add(8.45, A.sfx_whoosh(0.4), 0.45, 0.4)
    add(9.52, A.sfx_pop(), 0.5)
    for j in range(5):
        add(11.5 + j * 0.08, A.bell(2093 + j * 200, 0.3, 9.0) * 0.12, 1.0, (j - 2) * 0.3)
    add(S["PRICE_B"]["out_in"], A.sfx_whoosh(0.3), 0.5)
    for j in range(8):
        add(14.42 + j * 0.08, A.sfx_tick(), 0.5)
    add(15.14, A.sfx_impact(), 0.75)
    add(19.36, A.sfx_whoosh(0.25, up=False), 0.6)
    add(19.58, A.sfx_impact(), 1.0)
    add(19.60, A.sfx_soft_hit(), 0.9)
    add(20.62, A.sfx_pop(), 0.5)
    add(20.80, A.sfx_whoosh(0.4), 0.3, 0.3)
    add(21.74, A.sfx_check(), 0.7)
    add(24.96, A.sfx_check(), 0.7, 0.3)
    add(25.94, A.sfx_check(), 0.7, -0.3)
    add(27.80, A.sfx_success(), 0.5)
    add(S["SITE_A"]["out_in"], A.sfx_whoosh(0.35), 0.5)
    for j in range(4):
        add(31.54 + j * 0.12, A.sfx_tick(), 0.5)
    add(33.68, A.sfx_coin(), 0.35)
    for j in range(4):
        add(34.74 + j * 0.1, A.sfx_pop(), 0.35)
    add(S["OURS_A"]["out_in"], A.sfx_whoosh(0.35), 0.5)
    add(36.12, A.sfx_soft_hit(), 0.7)
    add(36.14, A.sfx_coin(), 0.4)
    add(39.38, A.sfx_pop(), 0.5)
    add(42.36, A.sfx_tick(), 0.6)
    add(44.0, A.sfx_soft_hit(), 0.9)
    add(44.02, A.sfx_success(), 0.55)
    add(S["GPT_A"]["out_in"], A.sfx_whoosh(0.35), 0.5)
    for j in range(len("ربات تریدیار")):
        add(47.22 + j * 0.09, A.sfx_type(), 0.6)
    add(S["GPT_B"]["out_in"], A.sfx_pop(), 0.4)
    add(55.54, A.sfx_success(), 0.6)
    for t0 in (57.84, 60.00, 61.02):
        add(t0, A.sfx_pop(), 0.5)
    add(62.62, A.sfx_notify(), 0.35)
    add(67.80, A.sfx_soft_hit(), 0.7)
    add(68.10, A.sfx_whoosh(0.45), 0.4)
    add(S["RES"]["out_in"] + 0.05, A.sfx_pop(), 0.5)
    for j in range(10):
        add(72.70 + j * 0.06, A.sfx_check(), 0.35, (j % 5 - 2) * 0.2)
    add(73.20, A.sfx_coin(), 0.4)
    for j in range(5):
        add(75.30 + j * 0.12, A.sfx_pop(), 0.4, (j - 2) * 0.3)
    add(77.34, A.sfx_whoosh(0.3), 0.4)
    add(78.10, A.sfx_soft_hit(), 0.6)
    add(81.46, A.sfx_pop(), 0.5)
    add(S["CTA_A"]["out_in"], A.sfx_pop(), 0.6)
    for k in range(5):
        add(84.14 + k * 0.075, A.sfx_type(), 0.8)
    add(84.98, A.sfx_whoosh(0.25), 0.45, 0.4)
    add(85.00, A.sfx_tap(), 0.8)
    add(85.98, A.sfx_notify(), 0.85)
    for t0, pan in ((87.42, 0.4), (88.68, 0.0), (90.16, -0.4)):
        add(t0, A.sfx_pop(), 0.55, pan)
    add(91.18, A.sfx_success(), 0.6)
    add(92.26, A.sfx_whoosh(0.4), 0.3)
    add(93.20, A.sfx_whoosh(0.4), 0.3)
    add(BODY_DUR - 1.0, A.sfx_riser(1.0), 0.5)
    add(BODY_DUR, A.sfx_impact(), 0.8)
    for k in range(5):
        add(S["SIGNOFF"]["out_in"] + 0.15 + 0.85 + k * 0.075, A.sfx_type(), 0.6)
    add(S["SIGNOFF"]["out_in"] + 0.15 + 1.3, A.sfx_notify(), 0.5)
    return c
