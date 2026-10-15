"""Picture edit + motion graphics renderer.

usage:
  python3 render.py SOURCE.mp4 WORKDIR [--preview t1,t2,...]
Full render writes WORKDIR/picture.mp4 (no audio); preview writes PNGs.
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

import gfx as G
import timeline as T
from gfx import (GOLD, GOLD_HI, GOLD_LO, GREEN, INK, INK2, RED, WHITE, GRAY, BLUE,
                 icon, life, out_back, out_cubic, in_cubic, inout_cubic, prog, put, text, panel)

W, H, FPS = T.W, T.H, T.FPS
o = T.o
S = T.SHOT


# ====================================================================== source
class Source:
    def __init__(self, path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        self.frames = np.frombuffer(raw, np.uint8).reshape(-1, T.SRC_H, T.SRC_W, 3)
        self.n = len(self.frames)
        self._exposure()
        self._drift()
        self._cache = {}
        self._mcache = {}
        self._seg = None

    def _exposure(self):
        # Auto-exposure "breathing": measure the static wall/painting area and
        # pull each frame 75% of the way back to the take's median level.
        wall = self.frames[:, 0:400:8, ::8].mean((1, 2, 3))
        k = np.ones(7) / 7
        sm = np.convolve(np.pad(wall, 3, mode="edge"), k, "valid")
        tgt = np.median(sm)
        self.gain = (tgt / sm) ** 0.75

    def _drift(self):
        # Slow tripod drift: phase-correlate the wall region against frame 0,
        # every 6th frame, then interpolate and smooth.
        def g(i):
            return self.frames[i, 40:520:2, ::2].mean(2)
        ref = g(0)
        F0 = np.fft.fft2(ref - ref.mean())
        idx = list(range(0, self.n, 6))
        dx, dy = [], []
        for i in idx:
            a = g(i)
            R = np.fft.fft2(a - a.mean()) * np.conj(F0)
            R /= np.abs(R) + 1e-9
            c = np.fft.ifft2(R).real
            y, x = np.unravel_index(c.argmax(), c.shape)
            y = y - c.shape[0] if y > c.shape[0] // 2 else y
            x = x - c.shape[1] if x > c.shape[1] // 2 else x
            dx.append(x * 2.0); dy.append(y * 2.0)
        fx = np.interp(np.arange(self.n), idx, dx)
        fy = np.interp(np.arange(self.n), idx, dy)
        k = np.ones(31) / 31
        self.dx = np.convolve(np.pad(fx, 15, mode="edge"), k, "valid")
        self.dy = np.convolve(np.pad(fy, 15, mode="edge"), k, "valid")

    def idx(self, src_t):
        return int(min(self.n - 1, max(0, round(src_t * FPS))))

    def graded(self, i):
        if i in self._cache:
            return self._cache[i]
        x = self.frames[i].astype(np.float32) * self.gain[i] / 255.0
        x = np.clip(x, 0, 1)
        # filmic S-curve, lifted blacks, warm highlights / neutral-cool shadows
        y = x + (x - 0.5) * 0.08 * (1 - np.abs(2 * x - 1))
        y = 0.018 + y * 0.975
        hi = np.clip((x.mean(2, keepdims=True) - 0.45) / 0.55, 0, 1)
        y = y * (1 + np.array([0.035, 0.008, -0.04]) * hi) + np.array([-0.004, 0.0, 0.010]) * (1 - hi)
        img = Image.fromarray((np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8))
        img = ImageEnhance.Color(img).enhance(1.10)
        if len(self._cache) > 48:
            self._cache.pop(next(iter(self._cache)))
        self._cache[i] = img
        return img

    def person_mask(self, i):
        if i in self._mcache:
            return self._mcache[i]
        if self._seg is None:
            import mediapipe as mp
            from mediapipe.tasks import python as mpt
            from mediapipe.tasks.python import vision
            opt = vision.ImageSegmenterOptions(
                base_options=mpt.BaseOptions(model_asset_path=MODEL),
                running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True)
            self._seg = (vision.ImageSegmenter.create_from_options(opt), mp)
        seg, mp = self._seg
        arr = np.ascontiguousarray(np.asarray(self.graded(i)))
        r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=arr))
        m = np.array(r.confidence_masks[0].numpy_view())
        m = m[..., 0] if m.ndim == 3 else m
        m = np.clip((m - 0.25) / 0.5, 0, 1)
        m[880:] = 0  # only the head/torso may occlude typography
        img = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
        self._mcache[i] = img
        return img


# ====================================================================== camera
def shot_at(t):
    for s in T.SHOT_LIST:
        if s["out_in"] - 1e-9 <= t < s["out_out"]:
            return s
    return None


REQ2_FRAMING = (1.30, 880)


def camera(t):
    """-> (src_time, zoom, face_y_out, blur_samples, darken, blur_radius)"""
    s = shot_at(t)
    if s is None:  # outro: speed ramp into a held frame
        lt = t - T.BODY_DUR
        src = T.OUTRO_SRC[0] + min(lt * T.OUTRO_SPEED, T.OUTRO_SRC[1] - T.OUTRO_SRC[0] - 1 / FPS)
        z0 = T.SHOT["PAYOFF"]["framing"][0] * (1 + T.SHOT["PAYOFF"]["push"] * (T.BODY_DUR - S["PAYOFF"]["out_in"]))
        z = z0 * (1 + 0.025 * lt)
        k = out_cubic(prog(lt, 0.05, 0.55))
        return src, z, T.CLOSE[1], 1, 0.55 * k, 16 * k
    lt = t - s["out_in"]
    zoom, fy = REQ2_FRAMING if s["tag"] == "REQ_2" else s["framing"]
    z = zoom * (1 + s["push"] * lt)
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
    return s["src_in"] + lt, z * mult, fy, nblur, 0.0, 0.0


def crop_box(z, fy, i, src):
    z = max(1.0, z)
    s = 1.5 * z
    w, h = T.SRC_W / z, T.SRC_H / z
    x0 = T.FACE_SRC[0] - 540 / s + src.dx[i]
    y0 = T.FACE_SRC[1] - fy / s + src.dy[i]
    x0 = min(max(0, x0), T.SRC_W - w)
    y0 = min(max(0, y0), T.SRC_H - h)
    return (x0, y0, x0 + w, y0 + h)


def base_frame(t, src):
    st, z, fy, nb, dark, br = camera(t)
    i = src.idx(st)
    img = src.graded(i)
    if nb > 1:  # motion blur across the zoom move within this frame's shutter
        dt = 1 / FPS
        acc = None
        sh = shot_at(t)
        for k in range(nb):
            tk = t + (k / (nb - 1) - 0.5) * dt * 0.9
            if sh is not None:  # sub-samples never leave the current shot
                tk = min(max(tk, sh["out_in"]), sh["out_out"] - 1e-6)
            _, zk, fyk, *_ = camera(tk)
            b = img.resize((W, H), Image.BICUBIC, box=crop_box(zk, fyk, i, src))
            a = np.asarray(b, np.float32)
            acc = a if acc is None else acc + a
        frame = Image.fromarray((acc / nb).astype(np.uint8))
    else:
        frame = img.resize((W, H), Image.BICUBIC, box=crop_box(z, fy, i, src))
    if br > 0.5:
        frame = frame.filter(ImageFilter.GaussianBlur(br))
    if dark > 0:
        frame = Image.blend(frame, Image.new("RGB", (W, H), INK), dark)
    return frame, (z, fy, i)


def person_mask_out(src, cam):
    z, fy, i = cam
    return src.person_mask(i).resize((W, H), Image.BILINEAR, box=crop_box(z, fy, i, src))


# ====================================================================== overlays
def make_vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2)
    a = np.clip((r - 0.62) / 0.6, 0, 1) ** 1.6 * 120
    v = Image.new("RGBA", (W, H), INK + (0,))
    v.putalpha(Image.fromarray(a.astype(np.uint8)))
    return v


def make_scrim(h0=820, amax=150):
    col = np.clip(1 - np.arange(H) / h0, 0, 1) ** 1.5 * amax
    a = np.repeat(col[:, None], W, 1).astype(np.uint8)
    v = Image.new("RGBA", (W, H), INK + (0,))
    v.putalpha(Image.fromarray(a))
    return v


VIGNETTE = None
SCRIM = None


def scrim_alpha(t):
    """Top darkening only while top-zone graphics are on screen."""
    on = [(0.0, S["HOOK"]["out_out"]), (o(5.18), S["CTX_B"]["out_out"]),
          (S["CTA_1"]["out_in"], S["REQ_3"]["out_out"]), (o(41.88), T.BODY_DUR)]
    a = 0.0
    for t0, t1 in on:
        a = max(a, min(prog(t, t0 - 0.05, 0.25), 1 - prog(t, t1 - 0.2, 0.25)))
    return a


# ---------------------------------------------------------------- captions
CAP_SIZE = 66
CAP_COL = {"g": GOLD, "m": GREEN, "r": RED, "": WHITE}


def caption_y(t):
    s = shot_at(t)
    return 1190 if s and s["tag"] == "CTA_2" else 1350


def draw_captions(t, L):
    s = shot_at(t)
    if s is None or s["tag"] in T.NO_CAPTION_SHOTS:
        return
    for ci, (a, b) in enumerate(T.CHUNKS):
        ws = T.WORDS[a:b]
        c_in = o(ws[0][1]) - 0.06
        nxt = T.CHUNKS[ci + 1] if ci + 1 < len(T.CHUNKS) else None
        # hold until the next chunk starts, never past the shot's hard cut
        c_out = min(o(T.WORDS[nxt[0]][1]) - 0.06 if nxt else 1e9,
                    o(ws[-1][2]) + 0.5,
                    shot_at(o(ws[-1][2]) - 0.01)["out_out"])
        if not (c_in <= t < c_out):
            continue
        enter = out_cubic(prog(t, c_in, 0.14))
        y = caption_y(t) + (1 - enter) * 26
        sprites = []
        for j, (w, w0, w1, k) in enumerate(ws):
            end = o(ws[j + 1][1]) - 0.03 if j + 1 < len(ws) else o(w1) + 0.12
            active = o(w0) - 0.03 <= t < end
            spoken = t >= o(w0) - 0.03
            if active:
                sp = text(w, "Black", CAP_SIZE, INK)
            else:
                col = CAP_COL[k]
                sp = text(w, "Black", CAP_SIZE, col, stroke=7, stroke_fill=(10, 10, 12), shadow=6)
            sprites.append((w, w0, w1, k, sp, active, spoken))
        gap = 18
        widths = [sp.width - (0 if a_ else 26) for *_, sp, a_, _ in sprites]
        total = sum(widths) + gap * (len(sprites) - 1)
        x = W / 2 + total / 2  # RTL: start at the right
        for (w, w0, w1, k, sp, active, spoken), ww in zip(sprites, widths):
            cx = x - ww / 2
            if active:
                pk = prog(t, o(w0) - 0.03, 0.12)
                sc = 1 + 0.10 * (1 - out_cubic(pk))
                col = {"g": GOLD, "m": GREEN, "r": RED, "": GOLD}[k]
                bw, bh = sp.width + 24, int(CAP_SIZE * 1.42)
                put(L, panel(int(bw), bh, 18, col, 255, shadow=False), cx, y + 4, scale=sc, alpha=enter)
                put(L, sp, cx, y, scale=sc, alpha=enter)
            else:
                put(L, sp, cx, y, alpha=enter * (1.0 if spoken else 0.62))
            x -= ww + gap


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
            cw = G.text_w(typed, "Black", 50)
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


def clamp_(x):
    return min(1, max(0, x))


def scene_outro(t, L):
    t0 = T.BODY_DUR
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


# ====================================================================== frame
def render_frame(t, src):
    frame, cam = base_frame(t, src)
    fr = frame.convert("RGBA")
    fr.alpha_composite(VIGNETTE)
    sa = scrim_alpha(t)
    if sa > 0.01:
        fr.alpha_composite(G.transform(SCRIM, alpha=sa) if sa < 0.99 else SCRIM)
    # behind-subject typography
    B = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scene_hook(t, L, B)
    scene_payoff(t, L, B)
    if B.getbbox():
        m = person_mask_out(src, cam)
        inv = Image.eval(m, lambda v: 255 - v)
        B.putalpha(ImageChops.multiply(B.getchannel("A"), inv))
        fr.alpha_composite(B)
    scene_context(t, L)
    scene_cta1(t, L)
    scene_stepper(t, L)
    scene_cta2(t, L)
    scene_dm(t, L)
    scene_signup(t, L)
    scene_reqs(t, L)
    draw_captions(t, L)
    scene_outro(t, L)
    # fade from black at head / out at tail
    fr.alpha_composite(L)
    tail = prog(t, T.TOTAL_DUR - 0.25, 0.25)
    if tail > 0:
        fr = Image.blend(fr, Image.new("RGBA", (W, H), INK + (255,)), tail)
    return fr.convert("RGB")


MODEL = None


def main():
    global VIGNETTE, SCRIM, MODEL
    src_path, work = sys.argv[1], sys.argv[2]
    MODEL = __import__("os").environ.get("SEG_MODEL", f"{work}/../models/seg.tflite")
    VIGNETTE, SCRIM = make_vignette(), make_scrim()
    src = Source(src_path)
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        for t in ts:
            render_frame(t, src).save(f"{work}/prev_{t:06.2f}.png")
        return
    n = int(round(T.TOTAL_DUR * FPS))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-x264-params", "aq-mode=3", f"{work}/picture.mp4"], stdin=subprocess.PIPE)
    for f in range(n):
        enc.stdin.write(render_frame(f / FPS, src).tobytes())
        if f % 60 == 0:
            print(f"frame {f}/{n}", flush=True)
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
