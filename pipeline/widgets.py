"""Reusable motion-graphics widgets shared by projects."""
import math

from gfx import (BLUE, GOLD, GRAY, GREEN, INK, INK2, WHITE, icon, life, out_back, out_cubic,
                 panel, partial_check, prog, put, text, text_w)

W = 1080


def comment_box(L, t, cy, typed, sent_t=None, a=1.0, sc=1.0, pulse=False):
    w, h = 860, 112
    put(L, panel(w, h, 56, WHITE, 250), W / 2, cy, scale=sc, alpha=a)
    # avatar (right, RTL)
    put(L, icon("disc", 76, GOLD), W / 2 + (w / 2 - 62) * sc, cy, scale=sc, alpha=a)
    put(L, icon("person", 46, WHITE), W / 2 + (w / 2 - 62) * sc, cy + 4, scale=sc, alpha=a)
    tx = W / 2 + (w / 2 - 120) * sc
    if typed:
        put(L, text(typed, "Black", 50, INK), tx, cy + 2, scale=sc, alpha=a, anchor="r")
        # caret
        if int(t * 2.5) % 2 == 0:
            cw = text_w(typed, "Black", 50)
            put(L, panel(4, 54, 2, INK, 255, shadow=False), tx - cw * sc - 10, cy, alpha=a)
    else:
        put(L, text("یک کامنت بنویسید…", "Medium", 40, GRAY), tx, cy + 2, scale=sc, alpha=a, anchor="r")
    bx = W / 2 - (w / 2 - 62) * sc
    pk = 1.0
    if sent_t is not None and t >= sent_t:
        pk = 1 - 0.18 * math.sin(math.pi * prog(t, sent_t, 0.22))
    if pulse:
        ph = (t * 1.4) % 1
        put(L, icon("ring", 120, GOLD), bx, cy, scale=sc * (0.8 + 0.6 * ph), alpha=a * (1 - ph))
    put(L, icon("disc", 84, GOLD), bx, cy, scale=sc * pk, alpha=a)
    put(L, icon("send", 44, INK, GOLD), bx - 2, cy, scale=sc * pk, alpha=a, rot=180)


def typed_text(word, t, t0, per=0.075):
    n = int(max(0, (t - t0) / per)) + (1 if t >= t0 else 0)
    return word[:min(len(word), n)] if t >= t0 else ""


def clamp_(x):
    return min(1, max(0, x))


# ---------------------------------------------------------------- generic pieces


def stepper(L, t, steps, t_in, t_out, y=250):
    """3-node progress bar. steps = [(label, t_on, t_done)] in output seconds, RTL."""
    al, ki, ke = life(t, t_in, t_out, 0.3, 0.2)
    if not al:
        return
    a = min(1, ki * 2) * (1 - ke)
    yy = y - (1 - out_cubic(ki)) * 60
    put(L, panel(940, 170, 40, INK, 220, border=WHITE, border_a=40), W / 2, yy, alpha=a)
    xs = [W / 2 + 300, W / 2, W / 2 - 300]
    for j in range(2):
        put(L, panel(220, 6, 3, (70, 72, 80), 255, shadow=False), (xs[j] + xs[j + 1]) / 2, yy - 28, alpha=a)
        p = out_cubic(prog(t, steps[j][2], 0.35))
        if p > 0:
            ln = max(6, int(220 * p))
            put(L, panel(ln, 6, 3, GREEN, 255, shadow=False), xs[j] - 40 - ln / 2, yy - 28, alpha=a)
    for j, (lab, ton, tdone) in enumerate(steps):
        x = xs[j]
        on, dn = t >= ton, t >= tdone
        k = out_back(prog(t, ton, 0.35), 2.2) if on else 0
        col = GREEN if dn else GOLD if on else (70, 72, 80)
        sc = 1 + 0.18 * k * (0 if dn else 1)
        put(L, icon("disc", 64, col), x, yy - 28, scale=sc, alpha=a)
        if dn:
            put(L, partial_check(64, out_cubic(prog(t, tdone, 0.3)), WHITE, 12), x, yy - 28, scale=sc, alpha=a)
        else:
            put(L, text("۱۲۳"[j], "Black", 38, INK if on else WHITE), x, yy - 26, scale=sc, alpha=a)
        put(L, text(lab, "Bold", 34, WHITE if on else GRAY), x, yy + 42, alpha=a)


def notification(L, t, t0, t_exit, y, title, chip, hl_t=None, tap_t=None, accent=(233, 62, 120)):
    """Generic DM banner with a link chip; slides down from above."""
    al, ki, ke = life(t, t0 - 0.05, t_exit + 0.25, 0.4, 0.25)
    if not al:
        return
    k = out_back(ki, 1.1)
    a = min(1, ki * 2) * (1 - ke)
    y = y - (1 - k) * 200 - ke * 60
    put(L, panel(900, 170, 40, WHITE, 248), W / 2, y, alpha=a)
    ix = W / 2 + 360
    put(L, icon("disc", 104, accent), ix, y, alpha=a)
    put(L, icon("plane", 58, WHITE, accent), ix - 2, y + 2, alpha=a)
    put(L, text(title, "Black", 42, INK), ix - 80, y - 34, alpha=a, anchor="r")
    put(L, text("الان", "Medium", 30, GRAY), W / 2 - 400, y - 34, alpha=a, anchor="l")
    hl = out_cubic(prog(t, hl_t, 0.25)) if hl_t is not None else 0
    chip_col = tuple(int(c0 + (c1 - c0) * hl) for c0, c1 in zip((236, 240, 248), (222, 236, 255)))
    put(L, panel(520, 62, 31, chip_col, 255, shadow=False), ix - 80 - 260, y + 36, alpha=a)
    put(L, icon("link", 44, BLUE), ix - 80 - 40, y + 36, alpha=a)
    put(L, text(chip, "Bold", 34, BLUE if hl > 0.5 else INK2), ix - 80 - 80, y + 38, alpha=a, anchor="r")
    if hl > 0:
        ln = int(240 * hl)
        put(L, panel(max(4, ln), 4, 2, BLUE, 255, shadow=False), ix - 160 - ln / 2, y + 62, alpha=a)
    if tap_t is not None and t >= tap_t:
        p = prog(t, tap_t, 0.45)
        put(L, icon("ring", 110, BLUE), ix - 300, y + 36, scale=0.4 + 0.9 * p, alpha=a * (1 - p))


def pill(L, cx, cy, label, ic, col, k=1.0, a=1.0, size=46, ic_col=WHITE, ic_bg=None, txt=WHITE):
    """Rounded label with a leading (right-hand, RTL) icon."""
    tw = text_w(label, "Black", size)
    h = int(size * 2.0)
    w = int(tw + h + size * 1.2)
    put(L, panel(w, h, h // 2, col, 245), cx, cy, scale=k, alpha=a)
    ix = cx + (w / 2 - h / 2) * k
    if ic_bg:
        put(L, icon("disc", int(h * 0.78), ic_bg), ix, cy, scale=k, alpha=a)
    put(L, icon(ic, int(h * 0.5), ic_col, ic_bg or col), ix, cy, scale=k, alpha=a)
    put(L, text(label, "Black", size, txt), cx - (h / 2 - size * 0.1) * k, cy + 2, scale=k, alpha=a)
    return w


def kinetic(L, t, t0, s, y, size, col=WHITE, exit_t=None, glow=None, rot=0.0, x=W / 2):
    """A headline that pops in on its word and leaves on exit_t."""
    if t < t0:
        return
    k = out_back(prog(t, t0, 0.28), 2.0)
    a = prog(t, t0, 0.08)
    if exit_t is not None:
        e = prog(t, exit_t, 0.2)
        a *= 1 - e
        y -= 40 * out_cubic(e)
    put(L, text(s, "Black", size, col, stroke=7, stroke_fill=(16, 12, 4), shadow=10, glow=glow),
        x, y, scale=k, alpha=a, rot=rot)
