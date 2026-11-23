#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNZX-01 "Kruzen Bot" — KRUZENLAB original mascot, written as ASCII STL.

Design (100% original for KRUZENLAB // BAGJA DEV):
  A mini helmet-droid / cyber-core bot:
    - armored helmet with a raised visor relief band
    - beacon antenna (stem + glowing tip relief)
    - side ear pods, shoulder rear fins
    - compact torso with a raised chest-core plate
    - two arms with grippers, twin thruster feet

Single-color STL viewers ignore material, so emissive parts (visor, core,
beacon tip, pods) are modeled as slightly raised relief plates that read
as highlights on GitHub's 3D viewer. The colored raymarched animation lives
in render.py and produces assets/kruzen_bot.gif.

Output: ../assets/kruzen_bot.stl
Convention: modeled as (x, y-up, z-forward); the writer swaps to z-up STL
so the bot stands upright in the GitHub model viewer.
"""

import os

# each entry: (box tuple (x0,y0,z0,x1,y1,z1), tag)
boxes = []


def part(cx, cy, cz, hx, hy, hz, tag="shell"):
    boxes.append(((cx - hx, cy - hy, cz - hz,
                   cx + hx, cy + hy, cz + hz), tag))


# ---------------------------------------------------------------- chassis
part(0.00, 0.86,  0.00, 0.50, 0.40, 0.34, "shell")    # torso hull
part(0.00, 1.18,  0.05, 0.16, 0.10, 0.16, "shell")    # neck coupling
part(0.00, 1.62,  0.08, 0.55, 0.40, 0.44, "shell")    # helmet dome

# ---------------------------------------------------------------- antenna
part(0.00, 2.16,  0.08, 0.035, 0.14, 0.035, "shell")  # beacon stem
part(0.00, 2.38,  0.08, 0.075, 0.075, 0.075, "relief")# beacon tip

# ---------------------------------------------------------------- ear pods
part(-0.68, 1.60, 0.08, 0.10, 0.17, 0.17, "relief")   # left pod
part( 0.68, 1.60, 0.08, 0.10, 0.17, 0.17, "relief")   # right pod

# ---------------------------------------------------------------- arms
part(-0.70, 0.94, 0.02, 0.13, 0.24, 0.13, "shell")    # left upper arm
part( 0.70, 0.94, 0.02, 0.13, 0.24, 0.13, "shell")    # right upper arm
part(-0.70, 0.60, 0.06, 0.11, 0.09, 0.11, "relief")   # left gripper
part( 0.70, 0.60, 0.06, 0.11, 0.09, 0.11, "relief")   # right gripper

# ---------------------------------------------------------------- rear fins
part(-0.56, 1.24, -0.28, 0.05, 0.22, 0.10, "relief")  # left fin
part( 0.56, 1.24, -0.28, 0.05, 0.22, 0.10, "relief")  # right fin

# ---------------------------------------------------------------- legs + thrusters
part(-0.26, 0.34, 0.00, 0.13, 0.26, 0.13, "shell")    # left leg
part( 0.26, 0.34, 0.00, 0.13, 0.26, 0.13, "shell")    # right leg
part(-0.26, 0.06, 0.05, 0.17, 0.06, 0.19, "relief")   # left thruster foot
part( 0.26, 0.06, 0.05, 0.17, 0.06, 0.19, "relief")   # right thruster foot

# ---------------------------------------------------------------- relief plates
part(0.00, 1.66, 0.50, 0.40, 0.10, 0.05, "relief")    # visor band (front)
part(0.00, 0.92, 0.35, 0.15, 0.15, 0.035, "relief")   # chest core


def quads(b):
    """Six outward-facing quads for an axis-aligned box."""
    x0, y0, z0, x1, y1, z1 = b
    v = lambda i, j, k: ((x0, x1)[i], (y0, y1)[j], (z0, z1)[k])
    return [
        ((0, 0, -1), [v(0, 0, 0), v(0, 1, 0), v(1, 1, 0), v(1, 0, 0)]),
        ((0, 0,  1), [v(0, 0, 1), v(1, 0, 1), v(1, 1, 1), v(0, 1, 1)]),
        ((-1, 0, 0), [v(0, 0, 0), v(0, 0, 1), v(0, 1, 1), v(0, 1, 0)]),
        (( 1, 0, 0), [v(1, 0, 0), v(1, 1, 0), v(1, 1, 1), v(1, 0, 1)]),
        ((0, -1, 0), [v(0, 0, 0), v(1, 0, 0), v(1, 0, 1), v(0, 0, 1)]),
        ((0,  1, 0), [v(0, 1, 0), v(0, 1, 1), v(1, 1, 1), v(1, 1, 0)]),
    ]


out = ["solid kruzen_bot"]


def tri(n, a, b, c):
    # model (x, y-up, z-forward) -> STL (x, z-up, y-forward)
    sw = lambda p: (p[0], -p[2], p[1])
    n2 = sw(n)
    out.append(" facet normal %.4f %.4f %.4f" % n2)
    out.append("  outer loop")
    for p in (a, b, c):
        q = sw(p)
        out.append("   vertex %.4f %.4f %.4f" % q)
    out.append("  endloop")
    out.append(" endfacet")


facet_count = 0
for b, tag in boxes:
    for n, (a, bb, c, d) in quads(b):
        tri(n, a, bb, c)
        tri(n, a, c, d)
        facet_count += 2

out.append("endsolid kruzen_bot")

os.makedirs("../assets", exist_ok=True)
with open("../assets/kruzen_bot.stl", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")

print("[kruzen_bot] parts=%d facets=%d -> ../assets/kruzen_bot.stl"
      % (len(boxes), facet_count))
