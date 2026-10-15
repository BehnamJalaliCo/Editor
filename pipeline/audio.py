"""Audio post: dialogue clean-up + edit, synthesized score, SFX, mix.

usage: python3 audio.py SOURCE.mp4 WORKDIR
writes WORKDIR/mix.wav (48 kHz stereo, pre-loudnorm) and WORKDIR/voice.wav
"""
import subprocess
import sys
import wave

import numpy as np

import timeline as T

SR = 48000
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- utilities
def read_wav(path):
    w = wave.open(path)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x.reshape(-1, w.getnchannels()).mean(1)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = x[:, None]
    w = wave.open(path, "wb")
    w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype(np.int16).tobytes())
    w.close()


def tvec(d):
    return np.arange(int(d * SR)) / SR


def fft_filter(x, f_lo=None, f_hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if f_lo:
        m *= 1 / (1 + (f_lo / np.maximum(f, 1)) ** 4)
    if f_hi:
        m *= 1 / (1 + (f / f_hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def swept_noise(d, f0, f1, q=1.2):
    """Noise through a band-pass whose centre glides f0 -> f1 (OLA blocks)."""
    n = int(d * SR); blk = 1024; hop = 512
    noise = rng.standard_normal(n + blk)
    out = np.zeros(n + blk)
    win = np.hanning(blk)
    freqs = np.fft.rfftfreq(blk, 1 / SR)
    for i, s in enumerate(range(0, n, hop)):
        c = f0 * (f1 / f0) ** (s / n)
        bw = c / q
        g = np.exp(-0.5 * ((freqs - c) / bw) ** 2)
        seg = np.fft.irfft(np.fft.rfft(noise[s:s + blk] * win) * g, blk)
        out[s:s + blk] += seg
    out = out[:n]
    return out / (np.abs(out).max() + 1e-9)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.where(t < a, t / max(a, 1e-4), np.exp(-(t - a) / d))


def reverb(x, dur=0.9, mix=0.18):
    ir = rng.standard_normal(int(dur * SR)) * np.exp(-np.arange(int(dur * SR)) / SR / (dur / 5))
    ir = fft_filter(ir, 200, 6000)
    ir /= np.sqrt((ir ** 2).sum())
    n = len(x) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x) + len(ir) - 1]
    y = np.zeros(len(wet)); y[: len(x)] = x
    return y * (1 - mix) + wet * mix * 3


# ---------------------------------------------------------------- SFX kit
def sfx_whoosh(d=0.5, up=True):
    n = int(d * SR)
    x = swept_noise(d, 350 if up else 3500, 3500 if up else 350, q=1.0)
    t = np.arange(n) / n
    e = np.sin(np.pi * t ** 0.7) ** 2
    return x * e * 0.55


def sfx_impact():
    t = tvec(1.4)
    f = 32 + 70 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    click = fft_filter(rng.standard_normal(len(t)), 80, 2500) * np.exp(-t * 40) * 0.5
    return reverb(body * 0.9 + click, 1.2, 0.12)[: len(t)] * 0.9


def sfx_soft_hit():
    t = tvec(0.6)
    f = 45 + 60 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.55


def bell(freq, d=0.7, decay=4.0, partials=((1, 1), (2.76, .35), (5.4, .12))):
    t = tvec(d)
    y = sum(a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t * decay * m ** 0.5) for m, a in partials)
    return y * np.minimum(1, t / 0.002)


def sfx_coin():  # "cha-ching"
    y = np.zeros(int(0.9 * SR))
    for i, (f, dt) in enumerate([(1975, 0.0), (2637, 0.07), (3136, 0.075)]):
        b = bell(f, 0.8, 6.0) * (0.35 if i else 0.4)
        s = int(dt * SR); y[s:s + len(b)] += b[: len(y) - s]
    shk = fft_filter(rng.standard_normal(int(0.12 * SR)), 4000, 12000) * env_ad(int(0.12 * SR), 0.003, 0.03) * 0.25
    y[: len(shk)] += shk
    return reverb(y, 0.8, 0.2)[: len(y)] * 0.8


def sfx_tick():
    n = int(0.03 * SR)
    return fft_filter(rng.standard_normal(n), 2500, 9000) * env_ad(n, 0.0005, 0.004) * 0.35


def sfx_pop():
    t = tvec(0.12)
    f = 380 + 700 * (t / 0.12) ** 0.5
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.03) * 0.45


def sfx_type():
    n = int(0.05 * SR)
    a = fft_filter(rng.standard_normal(n), 1800, 7000) * env_ad(n, 0.0005, 0.006) * 0.3
    b = np.sin(2 * np.pi * 180 * np.arange(n) / SR) * env_ad(n, 0.001, 0.01) * 0.15
    return a + b


def sfx_notify():
    y = np.zeros(int(0.9 * SR))
    for f, dt in [(1318.5, 0.0), (1975.5, 0.11)]:
        b = bell(f, 0.7, 5.0, ((1, 1), (2, .2), (3, .08))) * 0.35
        s = int(dt * SR); y[s:s + len(b)] += b[: len(y) - s]
    return reverb(y, 0.6, 0.15)[: len(y)]


def sfx_success():
    y = np.zeros(int(1.1 * SR))
    for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        b = bell(f, 0.7, 5.5, ((1, 1), (2, .15))) * 0.26
        s = int(i * 0.065 * SR); y[s:s + len(b)] += b[: len(y) - s]
    return reverb(y, 0.8, 0.2)[: len(y)]


def sfx_alert():
    t = tvec(0.7)
    y = (np.sin(2 * np.pi * 1174.7 * t) + 0.6 * np.sin(2 * np.pi * 1760 * t)) * np.exp(-t * 6)
    y *= 1 + 0.25 * np.sin(2 * np.pi * 14 * t)
    return reverb(y * 0.22, 0.6, 0.2)[: len(t)]


def sfx_check():
    t = tvec(0.25)
    f = 900 + 900 * (t / 0.25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.003, 0.05) * 0.25


def sfx_strike():
    return sfx_whoosh(0.22, up=False) * 0.7


def sfx_riser(d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    noise = swept_noise(d, 400, 7000, 1.5)
    tone = np.sin(2 * np.pi * np.cumsum(180 + 600 * (t / d) ** 2) / SR)
    e = (t / d) ** 2.2
    return (noise * 0.5 + tone * 0.12) * e


def sfx_tap():
    n = int(0.04 * SR)
    return fft_filter(rng.standard_normal(n), 600, 4000) * env_ad(n, 0.0005, 0.008) * 0.4


def sfx_clock():
    y = np.zeros(int(0.7 * SR))
    for i, f in enumerate([2400, 1900]):
        b = bell(f, 0.08, 60.0, ((1, 1),)) * 0.3
        s = int(i * 0.30 * SR); y[s:s + len(b)] += b
    return y


# ---------------------------------------------------------------- score
BEAT = 0.605           # 99.2 BPM so the outro hit lands on a downbeat
NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G


def score(dur):
    n = int(dur * SR)
    L = np.zeros(n); R = np.zeros(n)

    def add(sig, t0, pan=0.0, g=1.0):
        s = int(t0 * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        L[s:e] += sig[: e - s] * g * (1 - pan) ** 0.5
        R[s:e] += sig[: e - s] * g * (1 + pan) ** 0.5

    kick_t = tvec(0.45)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-kick_t * 30)) / SR) * np.exp(-kick_t * 9)
    hat_n = int(0.06 * SR)
    hat = lambda: fft_filter(rng.standard_normal(hat_n), 7000, 16000) * env_ad(hat_n, 0.0005, 0.012)
    clap_n = int(0.25 * SR)
    clap = lambda: fft_filter(rng.standard_normal(clap_n), 900, 5000) * env_ad(clap_n, 0.001, 0.05)

    beats = int(dur / BEAT) + 1
    end_body = T.BODY_DUR
    drop = (T.SHOT["REQ_1"]["out_in"] - 0.15, T.SHOT["REQ_1"]["out_in"] + 2 * BEAT)
    for b in range(beats):
        t0 = b * BEAT
        if t0 >= end_body - 0.02:
            break
        if drop[0] <= t0 < drop[1]:
            continue
        bar_pos = b % 4
        if bar_pos in (0, 2) or (bar_pos == 3 and b % 8 == 7):
            add(kick, t0, 0, 0.55)
        if bar_pos in (1, 3):
            add(clap(), t0, 0.1, 0.10)
        for k in range(2):
            add(hat(), t0 + k * BEAT / 2 + (0.03 if k else 0), -0.3, 0.05 if k else 0.035)

    # bass + pad + pluck, chord per bar (4 beats)
    bar = 4 * BEAT
    for i in range(int(dur / bar) + 1):
        t0 = i * bar
        if t0 >= end_body - 0.02:
            break
        root, *_ = ch = CHORDS[i % 4]
        tb = tvec(bar)
        bass = np.sin(2 * np.pi * NOTE(root - 24) * tb) * np.minimum(1, tb / 0.01) * np.exp(-((tb % BEAT) * 2.2)) * 0.30
        add(bass, t0, 0, 1.0)
        pad = sum(np.sin(2 * np.pi * NOTE(m) * tb * (1 + d)) for m in ch for d in (-0.003, 0.003))
        pad = pad * np.minimum(1, tb / 0.4) * np.minimum(1, (bar - tb) / 0.3) * 0.020
        add(pad, t0, -0.4, 1.0); add(pad, t0, 0.4, 1.0)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]
        for k in range(8):
            if drop[0] <= t0 + k * BEAT / 2 < drop[1]:
                continue
            pl = bell(NOTE(arp[k % 4]), 0.4, 9.0, ((1, 1), (2, .3), (3, .1))) * 0.035
            add(pl, t0 + k * BEAT / 2, 0.35 if k % 2 else -0.35, 1.0)

    # outro: sustained final chord + hit
    tb = tvec(T.OUTRO_DUR + 0.2)
    ch = CHORDS[0]
    pad = sum(np.sin(2 * np.pi * NOTE(m) * tb * (1 + d)) for m in ch + (ch[0] + 12,) for d in (-0.003, 0.003))
    pad *= np.minimum(1, tb / 0.05) * np.exp(-tb * 0.9) * 0.03
    add(pad, end_body, -0.3); add(pad, end_body, 0.3)
    add(np.sin(2 * np.pi * NOTE(33) * tb) * np.exp(-tb * 1.2) * 0.35, end_body)
    return np.stack([L, R], 1)


# ---------------------------------------------------------------- dialogue
def dialogue(src, work):
    raw = f"{work}/voice_clean_full.wav"
    chain = ("highpass=f=85,afftdn=nf=-42:nr=14:tn=1,"
             "equalizer=f=260:t=q:w=1.0:g=-2.5,equalizer=f=3400:t=q:w=1.2:g=2.5,"
             "highshelf=f=9000:g=1.5,deesser=i=0.35,"
             "acompressor=threshold=-22dB:ratio=3:attack=6:release=90:makeup=2")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", chain,
                    "-ac", "1", "-ar", str(SR), raw], check=True)
    v = read_wav(raw)
    out = np.zeros(int(T.TOTAL_DUR * SR) + SR)
    fade = int(0.012 * SR)
    for s in T.SHOT_LIST:
        a, b = int(s["src_in"] * SR), int(s["src_out"] * SR)
        seg = v[a:b].copy()
        if not s["join"]:
            seg[:fade] *= np.linspace(0, 1, fade)
        nxt = T.SHOT_LIST.index(s) + 1
        if nxt >= len(T.SHOT_LIST) or not T.SHOT_LIST[nxt]["join"]:
            seg[-fade:] *= np.linspace(1, 0, fade)
        o0 = int(s["out_in"] * SR)
        out[o0:o0 + len(seg)] += seg
    # outro tail: the take's last room tone, stretched quietly
    a, b = int(T.OUTRO_SRC[0] * SR), int(T.OUTRO_SRC[1] * SR)
    tail = v[a:b] * np.linspace(1, 0, b - a) * 0.5
    o0 = int(T.BODY_DUR * SR)
    out[o0:o0 + len(tail)] += tail
    return out[: int(T.TOTAL_DUR * SR)]


def duck_curve(voice):
    hop = 480
    e = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, "same"))[::hop]
    lvl = np.clip((20 * np.log10(e + 1e-6) + 45) / 25, 0, 1)
    sm = np.zeros_like(lvl); acc = 0
    for i, x in enumerate(lvl):  # fast attack, slow release
        acc = x if x > acc else acc * 0.93 + x * 0.07
        sm[i] = acc
    g = 1 - 0.62 * sm
    return np.interp(np.arange(len(voice)), np.arange(len(g)) * hop, g)


# ---------------------------------------------------------------- cues
def cues():
    o = T.o
    S = T.SHOT
    c = []
    add = lambda t, fx, g=1.0, pan=0.0: c.append((t, fx, g, pan))
    # HOOK
    add(0.0, sfx_impact(), 0.9)
    add(0.0, sfx_whoosh(0.35), 0.5)
    for k in range(10):
        add(0.05 + k * 0.05, sfx_tick(), 0.7, (-1) ** k * 0.2)
    add(0.58, sfx_coin(), 0.75)
    add(o(12.34), sfx_pop(), 0.8)
    add(o(13.80) - 0.08, sfx_whoosh(0.4), 0.55, 0.3)
    add(o(14.74), sfx_pop(), 0.8)
    add(o(14.74) + 0.03, sfx_coin(), 0.35)
    # transition hook -> context
    add(S["CTX_A"]["out_in"] - 0.28, sfx_whoosh(0.5), 0.75, -0.2)
    add(o(5.18), sfx_pop(), 0.6)
    add(S["CTX_B"]["out_in"], sfx_whoosh(0.3, up=False), 0.35)
    for k in range(8):
        add(o(8.05) + 0.1 + k * 0.045, sfx_tick(), 0.45)
    add(o(10.60), sfx_pop(), 0.6)
    add(o(10.62), sfx_coin(), 0.35)
    # CTA
    add(S["CTA_1"]["out_in"] - 0.15, sfx_whoosh(0.3), 0.5)
    add(o(18.16), sfx_whoosh(0.35), 0.5, 0.2)
    add(o(18.16) + 0.05, sfx_clock(), 0.8)
    add(S["CTA_2"]["out_in"], sfx_pop(), 0.6)
    t0 = o(20.68)
    for k in range(5):
        add(t0 + k * 0.075, sfx_type(), 0.8)
    add(o(21.52), sfx_pop(), 0.4)
    add(o(21.90), sfx_whoosh(0.25), 0.45, 0.4)
    add(o(21.90) + 0.02, sfx_tap(), 0.8)
    add(o(23.20), sfx_notify(), 0.85)
    add(o(26.38), sfx_tap(), 0.9)
    add(o(27.20), sfx_success(), 0.8)
    # REQ
    add(S["REQ_1"]["out_in"], sfx_alert(), 0.9)
    add(S["REQ_1"]["out_in"], sfx_soft_hit(), 0.8)
    add(o(30.30), sfx_pop(), 0.5)
    add(o(31.86) + 0.2, sfx_check(), 0.8)
    add(o(34.26), sfx_pop(), 0.5)
    add(o(34.84), sfx_strike(), 0.8)
    add(o(37.10), sfx_pop(), 0.5)
    add(o(39.66) + 0.2, sfx_check(), 0.8)
    # PAYOFF
    add(o(41.88), sfx_soft_hit(), 0.9)
    add(o(41.88) + 0.05, sfx_coin(), 0.6)
    for k in range(4):
        add(o(42.0) + 0.25 + k * 0.13, bell(2637 + k * 220, 0.4, 7.0) * 0.12, 1.0, (-1) ** k * 0.4)
    # OUTRO
    add(T.BODY_DUR - 1.1, sfx_riser(1.1), 0.5)
    add(T.BODY_DUR, sfx_impact(), 0.8)
    t0 = T.BODY_DUR + 0.75
    for k in range(5):
        add(t0 + k * 0.075, sfx_type(), 0.6)
    add(T.BODY_DUR + 1.35, sfx_notify(), 0.5)
    return c


def main(src, work):
    voice = dialogue(src, work)
    n = len(voice)
    write_wav(f"{work}/voice.wav", voice)
    # level-match dialogue to ~ -16 LUFS-ish by RMS of speech frames
    spk = voice[np.abs(voice) > 0.01]
    voice *= 0.12 / (np.sqrt((spk ** 2).mean()) + 1e-9)

    music = score(T.TOTAL_DUR)[:n]
    g = duck_curve(voice)
    music *= g[:, None] * 0.55

    fx = np.zeros((n, 2))
    for t, sig, gain, pan in cues():
        s = int(t * SR)
        if s < 0:
            sig = sig[-s:]; s = 0
        e = min(n, s + len(sig))
        fx[s:e, 0] += sig[: e - s] * gain * (1 - pan) ** 0.5 * 0.5
        fx[s:e, 1] += sig[: e - s] * gain * (1 + pan) ** 0.5 * 0.5

    mix = voice[:, None] + music + fx
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    write_wav(f"{work}/mix.wav", mix)
    write_wav(f"{work}/music_fx.wav", music + fx)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
