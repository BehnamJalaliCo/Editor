"""Edit decision list as code. All `src` times are seconds in the original
recording; all `out` times are seconds in the edited master."""

FPS = 30
W, H = 1080, 1920
SRC_W, SRC_H = 720, 1280

# Framing presets: (zoom, face anchor Y in output px). Face sits at src (345, 650).
WIDE = (1.04, 975)
MED = (1.18, 880)
CLOSE = (1.36, 820)
FACE_SRC = (345.0, 650.0)

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
    ("REQ_2",    33.26, 36.82,   CLOSE,   0.008, False),
    ("REQ_3",    37.08, 41.38,   MED,     0.006, False),
    ("PAYOFF",   41.38, 44.14,   CLOSE,   0.035, True),
]
# Outro: the last 0.52 s of the take, speed-ramped to 0.4x, then held.
OUTRO_SRC = (44.14, 44.66)
OUTRO_SPEED = 0.4
OUTRO_DUR = 2.70


def build():
    t = 0.0
    out = []
    for tag, a, b, fr, push, join in SHOTS:
        out.append(dict(tag=tag, src_in=a, src_out=b, framing=fr, push=push,
                        join=join, out_in=t, out_out=t + (b - a)))
        t += b - a
    return out, t


SHOT_LIST, BODY_DUR = build()
TOTAL_DUR = BODY_DUR + OUTRO_DUR
SHOT = {s["tag"]: s for s in SHOT_LIST}


def o(src_t, tag=None):
    """Map a source time to output time (inside the shot that contains it)."""
    for s in SHOT_LIST:
        if (tag is None or s["tag"] == tag) and s["src_in"] - 1e-6 <= src_t <= s["src_out"] + 1e-6:
            return s["out_in"] + src_t - s["src_in"]
    raise ValueError(f"src {src_t} not in edit ({tag})")


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
CHUNKS = []
_i = 0
for _n in CHUNK_SIZES:
    CHUNKS.append((_i, _i + _n))
    _i += _n
assert _i == len(WORDS), (_i, len(WORDS))

# Shots where the bottom captions are replaced by kinetic typography.
NO_CAPTION_SHOTS = {"HOOK", "CTA_1"}
