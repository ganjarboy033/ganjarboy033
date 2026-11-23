#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNZX-01 "Kruzen Bot" — numpy SDF raymarch renderer (original for KRUZENLAB).

Spins the droid a full, smooth 360 degrees and exports a looping GIF:
    python3 render.py 0 36        # render frames 0..35, assemble GIF

Palette: matte charcoal shell · cyan-neon visor · emerald core · indigo pods.
Environment overrides:
    W, H, N, SS (supersample), OUT (frames dir)
Output frames:  OUT/fNNN.png        final animation: ../assets/kruzen_bot.gif
"""

import os
import sys

import numpy as np
from PIL import Image

SS = int(os.environ.get("SS", 1))
W0, H0 = int(os.environ.get("W", 420)), int(os.environ.get("H", 300))
W, H = W0 * SS, H0 * SS
N = int(os.environ.get("N", 28))
OUT = os.environ.get("OUT", "frames")
os.makedirs(OUT, exist_ok=True)

BG = np.array([10.0, 15.0, 30.0]) / 255.0          # deep indigo night sky

# materials (0..3) + ground sentinel (20)
SHELL = np.array([0.17, 0.22, 0.31])                # matte charcoal-blue hull
POD   = np.array([0.34, 0.36, 0.82])                # indigo pods / fins / hands
VISOR = np.array([0.10, 0.83, 0.94])                # cyan neon visor
CORE  = np.array([0.22, 0.84, 0.58])                # emerald chest core


def sd_rbox(p, c, b, r):
    q = np.abs(p - c) - (np.array(b) - r)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) \
        + np.minimum(q.max(-1), 0) - r


def rot_y(p, a):
    c, s = np.cos(a), np.sin(a)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([c * x + s * z, y, -s * x + c * z], -1)


def scene(p, t):
    """Return (signed distance, material index) for world-space points p."""
    ph = 2 * np.pi * t
    yaw = ph                                  # one smooth full turn per loop
    bob = 0.045 * np.abs(np.sin(ph))
    q = rot_y(p, -yaw)
    q = q - np.array([0.0, bob, 0.0])

    sway = 0.10 * np.sin(2 * ph)              # gentle arm sway
    parts = [
        # (distance, material)
        (sd_rbox(q, np.array([0.0, 1.62, 0.08]), [0.55, 0.40, 0.44], 0.07), 0),  # helmet
        (sd_rbox(q, np.array([0.0, 1.18, 0.05]), [0.16, 0.10, 0.16], 0.04), 0),  # neck
        (sd_rbox(q, np.array([0.0, 0.86, 0.00]), [0.50, 0.40, 0.34], 0.06), 0),  # torso
        (sd_rbox(q, np.array([0.0, 2.16, 0.08]), [0.035, 0.14, 0.035], 0.02), 0),  # antenna stem
        (sd_rbox(q, np.array([0.0, 2.38, 0.08]), [0.075, 0.075, 0.075], 0.035), 1),  # beacon tip
        (sd_rbox(q, np.array([-0.68, 1.60, 0.08]), [0.10, 0.17, 0.17], 0.05), 2),  # ear L
        (sd_rbox(q, np.array([ 0.68, 1.60, 0.08]), [0.10, 0.17, 0.17], 0.05), 2),  # ear R
        (sd_rbox(q, np.array([-0.70, 0.94 + sway, 0.02]), [0.13, 0.24, 0.13], 0.05), 0),  # arm L
        (sd_rbox(q, np.array([ 0.70, 0.94 - sway, 0.02]), [0.13, 0.24, 0.13], 0.05), 0),  # arm R
        (sd_rbox(q, np.array([-0.70, 0.60 + sway, 0.06]), [0.11, 0.09, 0.11], 0.04), 2),  # gripper L
        (sd_rbox(q, np.array([ 0.70, 0.60 - sway, 0.06]), [0.11, 0.09, 0.11], 0.04), 2),  # gripper R
        (sd_rbox(q, np.array([-0.56, 1.24, -0.28]), [0.05, 0.22, 0.10], 0.03), 2),  # fin L
        (sd_rbox(q, np.array([ 0.56, 1.24, -0.28]), [0.05, 0.22, 0.10], 0.03), 2),  # fin R
        (sd_rbox(q, np.array([-0.26, 0.34, 0.00]), [0.13, 0.26, 0.13], 0.04), 0),  # leg L
        (sd_rbox(q, np.array([ 0.26, 0.34, 0.00]), [0.13, 0.26, 0.13], 0.04), 0),  # leg R
        (sd_rbox(q, np.array([-0.26, 0.06, 0.05]), [0.17, 0.06, 0.19], 0.04), 2),  # thruster L
        (sd_rbox(q, np.array([ 0.26, 0.06, 0.05]), [0.17, 0.06, 0.19], 0.04), 2),  # thruster R
        (sd_rbox(q, np.array([0.0, 1.66, 0.50]), [0.40, 0.10, 0.05], 0.03), 1),   # visor band
        (sd_rbox(q, np.array([0.0, 0.92, 0.35]), [0.15, 0.15, 0.035], 0.02), 3),  # chest core
    ]

    d = parts[0][0]
    m = np.full(d.shape, parts[0][1], dtype=np.int64)
    for dd, mm in parts[1:]:
        take = dd < d
        d = np.where(take, dd, d)
        m = np.where(take, mm, m)

    ground = p[..., 1]                        # world floor y = 0
    hit_ground = ground < d
    m = np.where(hit_ground, 20, m)
    return np.minimum(d, ground), m


def normal(p, t):
    e = 0.002
    ex = np.array([e, 0, 0]); ey = np.array([0, e, 0]); ez = np.array([0, 0, e])
    n = np.stack([
        scene(p + ex, t)[0] - scene(p - ex, t)[0],
        scene(p + ey, t)[0] - scene(p - ey, t)[0],
        scene(p + ez, t)[0] - scene(p - ez, t)[0]], -1)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)


def march(ro, rd, t, steps=80, tmax=18):
    dist = np.zeros(ro.shape[0])
    hit = np.zeros(ro.shape[0], bool)
    alive = np.ones(ro.shape[0], bool)
    for _ in range(steps):
        idx = np.where(alive)[0]
        if idx.size == 0:
            break
        d, _ = scene(ro[idx] + rd[idx] * dist[idx, None], t)
        dist[idx] += d
        h = d < 0.001
        hit[idx[h]] = True
        alive[idx[h | (dist[idx] > tmax)]] = False
    return dist, hit


def shadow(ro, rd, t, k=12):
    res = np.ones(ro.shape[0])
    s = np.full(ro.shape[0], 0.03)
    for _ in range(36):
        d, _ = scene(ro + rd * s[:, None], t)
        res = np.minimum(res, k * np.maximum(d, 0) / s)
        s += np.clip(d, 0.02, 0.3)
    return np.clip(res, 0, 1)


def ao(p, n, t):
    o = np.zeros(p.shape[0])
    for i in range(1, 5):
        h = 0.06 * i
        d, _ = scene(p + n * h, t)
        o += (h - d) / (2 ** i)
    return np.clip(1 - 1.6 * o, 0.35, 1)


def render(fi):
    t = fi / N
    ph = 2 * np.pi * t
    cam = np.array([0.0, 1.85, 4.05])
    look = np.array([0.0, 1.12, 0.0])
    f = look - cam
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)

    ys, xs = np.mgrid[0:H, 0:W]
    px = (2 * (xs + 0.5) - W) / H
    py = -(2 * (ys + 0.5) - H) / H
    rd = (px[..., None] * r + py[..., None] * u + 1.9 * f).reshape(-1, 3)
    rd /= np.linalg.norm(rd, axis=-1, keepdims=True)
    ro = np.broadcast_to(cam, rd.shape).copy()

    col = np.broadcast_to(BG, (H * W, 3)).copy()
    dist, hit = march(ro, rd, t)
    idx = np.where(hit)[0]
    p = ro[idx] + rd[idx] * dist[idx, None]
    _, m = scene(p, t)
    n = normal(p, t)

    L = np.array([-0.55, 0.85, 0.55]); L /= np.linalg.norm(L)
    dif = np.clip((n * L).sum(-1), 0, 1)
    sh = shadow(p + n * 0.01, np.broadcast_to(L, p.shape), t)
    a = ao(p, n, t)
    hv = L - rd[idx]; hv /= np.linalg.norm(hv, axis=-1, keepdims=True)
    spec = np.clip((n * hv).sum(-1), 0, 1) ** 28
    rim = np.clip(1 + (n * rd[idx]).sum(-1), 0, 1) ** 3

    # opaque body colors
    base = np.where(m[:, None] == 0, SHELL,
           np.where(m[:, None] == 2, POD,
           np.where(m[:, None] == 1, VISOR, CORE)))

    sky = 0.5 + 0.5 * n[:, 1]
    fill = np.clip((n * np.array([0.45, 0.35, 0.85])).sum(-1), 0, 1)
    diffuse = base * (1.05 * dif * sh + 0.34 * sky * a + 0.42 * fill * a)[:, None]
    specular = (0.30 * spec * sh)[:, None] * np.where(m[:, None] == 0, 1.0, 0.5)
    rim_light = (0.45 * rim * a)[:, None] * np.array([0.25, 0.75, 0.95])

    # neon glow: visor / beacon pulse, core steady emerald hum
    pulse = 0.82 + 0.18 * np.sin(3 * ph)
    emissive = np.zeros_like(base)
    vis = (m == 1)
    cor = (m == 3)
    emissive[vis] = VISOR * pulse
    emissive[cor] = CORE * (0.9 + 0.1 * np.sin(2 * ph + 1.3))

    c = diffuse + specular + rim_light + emissive * 0.9

    # floor: identical to background where unshadowed, darkened by AO/shadow
    gi = m == 20
    fl = np.exp(-0.10 * (p[gi, 0] ** 2 + p[gi, 2] ** 2))
    floor = BG * (0.06 + 0.94 * sh[gi] * a[gi])[:, None]
    c[gi] = col[idx[gi]] * (1 - fl[:, None]) + floor * fl[:, None]

    col[idx] = np.clip(c, 0, 1)
    img = (col.reshape(H, W, 3) * 255).astype(np.uint8)
    Image.fromarray(img).resize((W0, H0), Image.LANCZOS).save(f"{OUT}/f{fi:03d}.png")


def assemble_gif():
    os.makedirs("../assets", exist_ok=True)
    frames = [Image.open(f"{OUT}/f{i:03d}.png").convert("RGB") for i in range(N)]
    frames[0].save(
        "../assets/kruzen_bot.gif",
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / (N / 4.0)) if N else 70,
        loop=0,
        optimize=True,
    )
    print("[kruzen_bot] gif -> ../assets/kruzen_bot.gif (%d frames)" % N)


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for i in range(a, b):
        render(i)
        print("frame", i, flush=True)
    if a == 0 and b >= N:
        assemble_gif()
