"""Shared timeline machinery. A project module defines SHOTS, OUTRO_*, WORDS,
CHUNK_SIZES, ... and then calls `setup(globals())`, which adds SHOT_LIST,
SHOT/S, BODY_DUR, TOTAL_DUR, CHUNKS, o() and shot_at()."""

FPS = 30
W, H = 1080, 1920
SRC_W, SRC_H = 720, 1280

# Framing presets: (zoom, face anchor Y in output px).
WIDE = (1.04, 975)
MED = (1.18, 880)
CLOSE = (1.36, 820)


def setup(ns):
    t = 0.0
    shots = []
    for tag, a, b, fr, push, join in ns["SHOTS"]:
        shots.append(dict(tag=tag, src_in=a, src_out=b, framing=fr, push=push,
                          join=join, out_in=t, out_out=t + (b - a)))
        t += b - a
    ns["SHOT_LIST"] = shots
    ns["BODY_DUR"] = t
    ns["TOTAL_DUR"] = t + ns["OUTRO_DUR"]
    ns["SHOT"] = ns["S"] = {s["tag"]: s for s in shots}

    def o(src_t, tag=None):
        """Map a source time to output time (inside the shot that contains it)."""
        for s in shots:
            if (tag is None or s["tag"] == tag) and s["src_in"] - 1e-6 <= src_t <= s["src_out"] + 1e-6:
                return s["out_in"] + src_t - s["src_in"]
        raise ValueError(f"src {src_t} not in edit ({tag})")

    def shot_at(t):
        for s in shots:
            if s["out_in"] - 1e-9 <= t < s["out_out"]:
                return s
        return None

    ns["o"], ns["shot_at"] = o, shot_at
    chunks, i = [], 0
    for n in ns["CHUNK_SIZES"]:
        chunks.append((i, i + n))
        i += n
    assert i == len(ns["WORDS"]), (i, len(ns["WORDS"]))
    ns["CHUNKS"] = chunks
