"""Motion-graphics primitives: brand palette, RTL type, panels, vector icons.

Everything is rasterised once into cached RGBA sprites (supersampled for
anti-aliasing); per-frame work is only transform + alpha + composite.
"""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = os.environ.get("FONT_DIR", os.path.join(os.path.dirname(__file__), "fonts"))

# ---------------------------------------------------------------- palette
INK = (13, 14, 18)
INK2 = (28, 30, 36)
WHITE = (255, 255, 255)
CREAM = (250, 244, 232)
GOLD = (255, 196, 54)
GOLD_HI = (255, 222, 120)
GOLD_LO = (214, 142, 18)
GREEN = (38, 194, 129)       # USDT / success
GREEN_LO = (20, 140, 92)
RED = (255, 84, 89)          # warnings / "without"
GRAY = (150, 154, 162)
BLUE = (64, 156, 255)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


# ---------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def prog(t, t0, d):
    return clamp01((t - t0) / d) if d > 0 else float(t >= t0)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def in_cubic(x):
    return x ** 3


def inout_cubic(x):
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.70158):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def out_elastic(x):
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def life(t, t_in, t_out, fin=0.18, fout=0.18):
    """(alive, enter_progress, exit_progress)"""
    if t < t_in or t > t_out:
        return False, 0.0, 1.0
    return True, prog(t, t_in, fin), prog(t, t_out - fout, fout)


# ---------------------------------------------------------------- type
@lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Vazirmatn-{weight}.ttf"), int(size),
                              layout_engine=ImageFont.Layout.RAQM)


def _dir(text):
    return "rtl" if any("؀" <= ch <= "ۿ" or ch in "«»" for ch in text) else "ltr"


@lru_cache(4096)
def text(s, weight="ExtraBold", size=64, fill=WHITE, stroke=0, stroke_fill=INK,
         shadow=0, glow=None, gradient=None):
    """RGBA sprite of a single line. gradient=(top_rgb, bottom_rgb)."""
    f = font(weight, size)
    d = _dir(s)
    l, t, r, b = f.getbbox(s, direction=d, stroke_width=stroke, anchor="ls")
    pad = stroke + shadow * 2 + (int(size * 0.35) if glow else 0) + 4
    w, h = r - l + 2 * pad, b - t + 2 * pad
    org = (pad - l, pad - t)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text(org, s, font=f, fill=255, direction=d, anchor="ls")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sm = Image.new("L", (w, h), 0)
        ImageDraw.Draw(sm).text((org[0], org[1] + shadow // 2), s, font=f, fill=150, direction=d,
                                anchor="ls", stroke_width=stroke)
        sm = sm.filter(ImageFilter.GaussianBlur(shadow))
        out = Image.composite(Image.new("RGBA", (w, h), rgba(INK, 255)), out, sm)
    if glow:
        gm = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(size * 0.12))
        gm = gm.point(lambda v: min(255, int(v * 1.6)))
        out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), rgba(glow, 200)),
                                                         Image.new("RGBA", (w, h), (0, 0, 0, 0)), gm))
    if stroke:
        st = Image.new("L", (w, h), 0)
        ImageDraw.Draw(st).text(org, s, font=f, fill=255, direction=d, anchor="ls",
                                stroke_width=stroke, stroke_fill=255)
        out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), rgba(stroke_fill)),
                                                         Image.new("RGBA", (w, h), (0, 0, 0, 0)), st))
    if gradient:
        g = vgrad(w, h, gradient[0], gradient[1], top=org[1] + t - 0, bottom=org[1] + b)
        fillimg = g
    else:
        fillimg = Image.new("RGBA", (w, h), rgba(fill))
    out = Image.alpha_composite(out, Image.composite(fillimg, Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask))
    return out


def vgrad(w, h, c0, c1, top=0, bottom=None):
    bottom = h if bottom is None else bottom
    col = Image.new("RGBA", (1, h))
    for y in range(h):
        k = clamp01((y - top) / max(1, bottom - top))
        col.putpixel((0, y), tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)) + (255,))
    return col.resize((w, h))


def text_w(s, weight, size):
    f = font(weight, size)
    l, _, r, _ = f.getbbox(s, direction=_dir(s), anchor="ls")
    return r - l


# ---------------------------------------------------------------- shapes
SS = 3  # supersampling factor


@lru_cache(512)
def panel(w, h, r, fill=INK, alpha=215, border=None, border_a=90, shadow=True, grad=None):
    pad = 40 if shadow else 0
    W, Hh = (w + 2 * pad) * SS, (h + 2 * pad) * SS
    big = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    box = [pad * SS, pad * SS, (pad + w) * SS - 1, (pad + h) * SS - 1]
    if grad:
        m = Image.new("L", (W, Hh), 0)
        ImageDraw.Draw(m).rounded_rectangle(box, r * SS, fill=alpha)
        big = vgrad(W, Hh, grad[0], grad[1], top=box[1], bottom=box[3])
        big.putalpha(m)
        d = ImageDraw.Draw(big)
    else:
        d.rounded_rectangle(box, r * SS, fill=rgba(fill, alpha))
    if border:
        d.rounded_rectangle(box, r * SS, outline=rgba(border, border_a), width=2 * SS)
    img = big.resize((W // SS, Hh // SS), Image.LANCZOS)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([pad, pad + 10, pad + w, pad + h + 10], r, fill=110)
        m = m.filter(ImageFilter.GaussianBlur(18))
        sh.putalpha(m)
        img = Image.alpha_composite(sh, img)
    return img


def _canvas(size):
    return Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))


def _done(big, size):
    return big.resize((size, size), Image.LANCZOS)


@lru_cache(None)
def icon(name, size, color=WHITE, color2=None):
    """Vector icons drawn at SSx, returned as size x size RGBA."""
    S = size * SS
    big = _canvas(size)
    d = ImageDraw.Draw(big)
    c = rgba(color)
    c2 = rgba(color2) if color2 else rgba(INK)
    u = S / 100.0  # 100-unit design grid

    def L(pts, w):
        d.line([(x * u, y * u) for x, y in pts], fill=c, width=int(w * u), joint="curve")
        for x, y in (pts[0], pts[-1]):
            d.ellipse([(x - w / 2) * u, (y - w / 2) * u, (x + w / 2) * u, (y + w / 2) * u], fill=c)

    if name == "coin":  # USDT-style coin: green disc, white T with ring
        d.ellipse([2 * u, 2 * u, 98 * u, 98 * u], fill=rgba(GREEN_LO))
        d.ellipse([6 * u, 4 * u, 96 * u, 94 * u], fill=rgba(GREEN))
        w = rgba(WHITE)
        d.rectangle([26 * u, 22 * u, 74 * u, 34 * u], fill=w)
        d.rectangle([43 * u, 22 * u, 57 * u, 78 * u], fill=w)
        d.ellipse([20 * u, 40 * u, 80 * u, 54 * u], outline=w, width=int(5 * u))
    elif name == "gift":
        d.rounded_rectangle([14 * u, 40 * u, 86 * u, 92 * u], 6 * u, fill=c)
        d.rounded_rectangle([8 * u, 28 * u, 92 * u, 44 * u], 5 * u, fill=c)
        d.rectangle([44 * u, 28 * u, 56 * u, 92 * u], fill=c2)
        d.rectangle([8 * u, 44 * u, 92 * u, 48 * u], fill=c2)
        d.ellipse([22 * u, 6 * u, 50 * u, 30 * u], outline=c, width=int(7 * u))
        d.ellipse([50 * u, 6 * u, 78 * u, 30 * u], outline=c, width=int(7 * u))
    elif name == "exchange":
        d.ellipse([0, 0, S - 1, S - 1], fill=rgba(color2 or GOLD))
        k = rgba(INK)
        d.line([(24 * u, 38 * u), (74 * u, 38 * u)], fill=k, width=int(9 * u))
        d.polygon([(70 * u, 24 * u), (86 * u, 38 * u), (70 * u, 52 * u)], fill=k)
        d.line([(26 * u, 64 * u), (76 * u, 64 * u)], fill=k, width=int(9 * u))
        d.polygon([(30 * u, 50 * u), (14 * u, 64 * u), (30 * u, 78 * u)], fill=k)
    elif name == "person":
        d.ellipse([32 * u, 6 * u, 68 * u, 42 * u], fill=c)
        d.rounded_rectangle([14 * u, 48 * u, 86 * u, 100 * u], 30 * u, fill=c)
    elif name == "stopwatch":
        d.ellipse([10 * u, 16 * u, 90 * u, 96 * u], outline=c, width=int(9 * u))
        d.rectangle([42 * u, 2 * u, 58 * u, 12 * u], fill=c)
        d.line([(78 * u, 18 * u), (88 * u, 10 * u)], fill=c, width=int(8 * u))
    elif name == "send":
        d.polygon([(10 * u, 14 * u), (92 * u, 50 * u), (10 * u, 86 * u), (24 * u, 50 * u)], fill=c)
        d.polygon([(24 * u, 50 * u), (60 * u, 50 * u), (10 * u, 86 * u)], fill=c2)
    elif name == "plane":
        d.polygon([(8 * u, 46 * u), (92 * u, 10 * u), (62 * u, 90 * u), (46 * u, 56 * u)], fill=c)
        d.line([(46 * u, 56 * u), (92 * u, 10 * u)], fill=c2, width=int(5 * u))
    elif name == "link":
        for (x0, y0) in ((10, 38), (46, 38)):
            d.rounded_rectangle([x0 * u, y0 * u, (x0 + 44) * u, (y0 + 26) * u], 13 * u,
                                outline=c, width=int(8 * u))
    elif name == "check":
        L([(22, 52), (42, 72), (78, 30)], 11)
    elif name == "cross":
        L([(26, 26), (74, 74)], 11); L([(74, 26), (26, 74)], 11)
    elif name == "alert":
        d.polygon([(50 * u, 6 * u), (96 * u, 90 * u), (4 * u, 90 * u)], fill=c)
        d.rounded_rectangle([45 * u, 34 * u, 55 * u, 66 * u], 4 * u, fill=c2)
        d.ellipse([44 * u, 72 * u, 56 * u, 84 * u], fill=c2)
    elif name == "globe":
        d.ellipse([6 * u, 6 * u, 94 * u, 94 * u], outline=c, width=int(7 * u))
        d.ellipse([30 * u, 6 * u, 70 * u, 94 * u], outline=c, width=int(6 * u))
        d.line([(8 * u, 50 * u), (92 * u, 50 * u)], fill=c, width=int(6 * u))
        d.line([(16 * u, 28 * u), (84 * u, 28 * u)], fill=c, width=int(5 * u))
        d.line([(16 * u, 72 * u), (84 * u, 72 * u)], fill=c, width=int(5 * u))
    elif name == "shield":
        d.polygon([(50 * u, 4 * u), (90 * u, 18 * u), (86 * u, 58 * u), (50 * u, 96 * u),
                   (14 * u, 58 * u), (10 * u, 18 * u)], fill=c)
    elif name == "mail":
        d.rounded_rectangle([6 * u, 20 * u, 94 * u, 80 * u], 8 * u, fill=c)
        d.line([(10 * u, 26 * u), (50 * u, 56 * u), (90 * u, 26 * u)], fill=c2, width=int(7 * u))
    elif name == "phone":
        d.rounded_rectangle([26 * u, 4 * u, 74 * u, 96 * u], 10 * u, fill=c)
        d.rounded_rectangle([32 * u, 14 * u, 68 * u, 80 * u], 3 * u, fill=c2)
        d.ellipse([45 * u, 84 * u, 55 * u, 92 * u], fill=c2)
    elif name == "arrow_down":
        L([(50, 8), (50, 84)], 12)
        L([(20, 56), (50, 88), (80, 56)], 12)
    elif name == "chat":
        d.rounded_rectangle([4 * u, 10 * u, 96 * u, 74 * u], 24 * u, fill=c)
        d.polygon([(22 * u, 66 * u), (16 * u, 94 * u), (46 * u, 72 * u)], fill=c)
    elif name == "heart":
        d.ellipse([8 * u, 14 * u, 52 * u, 58 * u], fill=c)
        d.ellipse([48 * u, 14 * u, 92 * u, 58 * u], fill=c)
        d.polygon([(10 * u, 44 * u), (90 * u, 44 * u), (50 * u, 90 * u)], fill=c)
    elif name == "ring":
        d.ellipse([4 * u, 4 * u, 96 * u, 96 * u], outline=c, width=int(5 * u))
    elif name == "disc":
        d.ellipse([0, 0, S - 1, S - 1], fill=c)
    else:
        raise KeyError(name)
    return _done(big, size)


def partial_check(size, p, color=WHITE, width=11):
    """Check mark drawn on (stroke animation), p in 0..1."""
    big = _canvas(size)
    d = ImageDraw.Draw(big)
    u = size * SS / 100
    pts = [(22, 52), (42, 72), (78, 30)]
    seg = [math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])]
    L = p * sum(seg)
    path = [pts[0]]
    if L <= seg[0]:
        k = L / seg[0]
        path.append((pts[0][0] + (pts[1][0] - pts[0][0]) * k, pts[0][1] + (pts[1][1] - pts[0][1]) * k))
    else:
        k = (L - seg[0]) / seg[1]
        path += [pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * k, pts[1][1] + (pts[2][1] - pts[1][1]) * k)]
    c = rgba(color)
    d.line([(x * u, y * u) for x, y in path], fill=c, width=int(width * u), joint="curve")
    for x, y in (path[0], path[-1]):
        r = width / 2
        d.ellipse([(x - r) * u, (y - r) * u, (x + r) * u, (y + r) * u], fill=c)
    return _done(big, size)


def arc_ring(size, p, color=WHITE, width=7):
    big = _canvas(size)
    d = ImageDraw.Draw(big)
    S = size * SS
    w = int(width * S / 100)
    d.arc([w, w, S - w, S - w], -90, -90 + 360 * p, fill=rgba(color), width=w)
    return _done(big, size)


# ---------------------------------------------------------------- compositing
def transform(sp, scale=1.0, alpha=1.0, rot=0.0, sx=None):
    if alpha <= 0.003 or scale <= 0.01:
        return None
    sx = scale if sx is None else sx
    if abs(sx - 1) > 1e-3 or abs(scale - 1) > 1e-3:
        sp = sp.resize((max(1, int(sp.width * sx)), max(1, int(sp.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        sp = sp.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.997:
        a = sp.getchannel("A").point(lambda v, k=alpha: int(v * k))
        sp = sp.copy(); sp.putalpha(a)
    return sp


def put(layer, sp, cx, cy, scale=1.0, alpha=1.0, rot=0.0, sx=None, anchor="c"):
    sp = transform(sp, scale, alpha, rot, sx)
    if sp is None:
        return
    if anchor == "c":
        x, y = int(round(cx - sp.width / 2)), int(round(cy - sp.height / 2))
    elif anchor == "r":  # cx is the right edge
        x, y = int(round(cx - sp.width)), int(round(cy - sp.height / 2))
    else:  # left edge
        x, y = int(round(cx)), int(round(cy - sp.height / 2))
    # clip to layer
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(layer.width, x + sp.width), min(layer.height, y + sp.height)
    if X1 <= X0 or Y1 <= Y0:
        return
    if (X0, Y0, X1, Y1) != (x, y, x + sp.width, y + sp.height):
        sp = sp.crop((X0 - x, Y0 - y, X1 - x, Y1 - y))
    layer.alpha_composite(sp, (X0, Y0))
