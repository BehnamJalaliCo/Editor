"""Picture edit + motion graphics engine (project-agnostic).

usage:
  python3 engine.py PROJECT SOURCE.mp4 WORKDIR [--preview t1,t2,...]
PROJECT is a module in projects/ (e.g. usdt_voucher). Full render writes
WORKDIR/picture.mp4 (no audio); preview writes PNGs.

A project provides the timeline (see tlcore.setup) plus these hooks:
  camera_fx(shot, local_t) -> (zoom_mult, motion_blur_samples)
  scrim_windows() -> [(t_in, t_out), ...]
  caption_y(tag) -> y
  draw_behind(t, L, B) / draw_front(t, L) / draw_top(t, L)
"""
import importlib
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

import gfx as G
import tlcore
from gfx import GOLD, GREEN, INK, RED, WHITE, out_cubic, prog, put, text, panel

W, H, FPS = tlcore.W, tlcore.H, tlcore.FPS
T = None  # the project module, bound in main()


def o(src_t, tag=None):
    return T.o(src_t, tag)


# ====================================================================== source
class Source:
    def __init__(self, path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        self.frames = np.frombuffer(raw, np.uint8).reshape(-1, tlcore.SRC_H, tlcore.SRC_W, 3)
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
    return T.shot_at(t)


def camera(t):
    """-> (src_time, zoom, face_y_out, blur_samples, darken, blur_radius)"""
    s = shot_at(t)
    if s is None:  # outro: speed ramp into a held frame
        lt = t - T.BODY_DUR
        src = T.OUTRO_SRC[0] + min(lt * T.OUTRO_SPEED, T.OUTRO_SRC[1] - T.OUTRO_SRC[0] - 1 / FPS)
        last = T.SHOT_LIST[-1]  # continue the last shot's framing and push
        z0 = last["framing"][0] * (1 + last["push"] * (T.BODY_DUR - last["out_in"]))
        z = z0 * (1 + 0.025 * lt)
        k = out_cubic(prog(lt, 0.05, 0.55))
        return src, z, last["framing"][1], 1, 0.55 * k, 16 * k
    lt = t - s["out_in"]
    zoom, fy = s["framing"]
    z = zoom * (1 + s["push"] * lt)
    mult, nblur = T.camera_fx(s, lt)
    return s["src_in"] + lt, z * mult, fy, nblur, 0.0, 0.0


def crop_box(z, fy, i, src):
    z = max(1.0, z)
    s = 1.5 * z
    w, h = tlcore.SRC_W / z, tlcore.SRC_H / z
    x0 = T.FACE_SRC[0] - 540 / s + src.dx[i]
    y0 = T.FACE_SRC[1] - fy / s + src.dy[i]
    x0 = min(max(0, x0), tlcore.SRC_W - w)
    y0 = min(max(0, y0), tlcore.SRC_H - h)
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
    a = 0.0
    for t0, t1 in T.scrim_windows():
        a = max(a, min(prog(t, t0 - 0.05, 0.25), 1 - prog(t, t1 - 0.2, 0.25)))
    return a


# ---------------------------------------------------------------- captions
CAP_SIZE = 66
CAP_COL = {"g": GOLD, "m": GREEN, "r": RED, "": WHITE}


def caption_y(t):
    s = shot_at(t)
    return T.caption_y(s["tag"] if s else None)


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
    T.draw_behind(t, L, B)
    if B.getbbox():
        m = person_mask_out(src, cam)
        inv = Image.eval(m, lambda v: 255 - v)
        B.putalpha(ImageChops.multiply(B.getchannel("A"), inv))
        fr.alpha_composite(B)
    T.draw_front(t, L)
    draw_captions(t, L)
    T.draw_top(t, L)
    # fade from black at head / out at tail
    fr.alpha_composite(L)
    tail = prog(t, T.TOTAL_DUR - 0.25, 0.25)
    if tail > 0:
        fr = Image.blend(fr, Image.new("RGBA", (W, H), INK + (255,)), tail)
    return fr.convert("RGB")


MODEL = None


def main():
    global VIGNETTE, SCRIM, MODEL, T
    T = importlib.import_module("projects." + sys.argv[1])
    src_path, work = sys.argv[2], sys.argv[3]
    MODEL = os.environ.get("SEG_MODEL", os.path.join(os.path.dirname(__file__), "..", "models", "seg.tflite"))
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