"""Draws every texture in this mod. Run from the repo root:

    python3 Source/Art/draw_sprites.py

Each machine is laid out ONCE in its own coordinates (`a` across its front, `f` from front to
back, in cells) and `View` places that layout for north, east, south and west. Drawing is always
upright, so the light stays at the top of the screen in every view. See stb_draw.py for the rules.

Every machine has ONE input and no output: a single intake port, centred on the edge it faces,
marked with an in-pointing chevron in VFE Factory's input green. CompHopperFeed reads fuel from
the cells just outside that edge; verify_art.py checks the chevron lands there in all four views.
"""
import math
import random

from PIL import Image, ImageDraw

from stb_draw import CELL, LIFT, SEAM, SS, Canvas, View, mix, shade

OUT = "Textures"
ROTS = ("north", "east", "south", "west")
MARGIN_2X2 = 0.5   # 2x2 machines draw at (3,3)
MARGIN_1X1 = 0.25  # the hopper draws at (1.5,1.5)

INTAKE_GREEN = (91, 175, 94)   # VFE Factory's input rail colour
STEEL = (134, 131, 128)        # VFE chassis face (138,134,132)->(119,115,113)
DECK = (96, 94, 92)
RUST = (126, 98, 82)           # desaturated: rust as a tone, not a colour
OLIVE = (112, 116, 102)
FIRE_HOT, FIRE_DEEP = (255, 200, 110), (214, 92, 36)
TEAL = (92, 156, 150)          # subdued, as in the mending repair centre
HOT = (190, 98, 68)            # pressurised hot water: the pipe network's one accent
INTAKE_Z, INTAKE_H = 0.07, 0.12  # the port stands on the skid; verify_art.py allows for its lift


def intake(c, width, depth, z0, body):
    """The single intake port, centred on the front edge: a dark throat under a lit lip, with
    a flat chevron pointing IN. Chevrons follow the material, not the edge they sit on."""
    W = c.v.W
    a0, a1 = W / 2 - width / 2, W / 2 + width / 2

    def top(box, lift):
        x0, y0, x1, y1 = box
        d = c.d
        inset = c.px(0.035)
        throat = [x0 + inset, y0 + inset, x1 - inset, y1 - inset]
        c.ramp(throat, (40, 40, 40), (58, 58, 58), c.px(0.02))
        # Rails either side of the throat, in the input green, like a VFE input bay.
        horiz = c.v.along_a()
        rail = c.px(0.03)
        if horiz:
            d.rectangle([throat[0], throat[1], throat[0] + rail, throat[3]], fill=INTAKE_GREEN + (255,))
            d.rectangle([throat[2] - rail, throat[1], throat[2], throat[3]], fill=INTAKE_GREEN + (255,))
        else:
            d.rectangle([throat[0], throat[1], throat[2], throat[1] + rail], fill=INTAKE_GREEN + (255,))
            d.rectangle([throat[0], throat[3] - rail, throat[2], throat[3]], fill=INTAKE_GREEN + (255,))
        # Chevron: a flat triangle pointing from the front edge towards the back.
        fx, fy = c.v.pt(W / 2, 0)
        bx, by = c.v.pt(W / 2, depth)
        cx, cy = (fx + bx) / 2, (fy + by) / 2 - lift
        ux, uy = bx - fx, by - fy
        n = math.hypot(ux, uy)
        ux, uy = ux / n, uy / n
        s = min(width, depth) * 0.28
        tip = (cx + ux * s * 0.6, cy + uy * s * 0.6)
        l = (cx - ux * s * 0.4 - uy * s * 0.8, cy - uy * s * 0.4 + ux * s * 0.8)
        r = (cx - ux * s * 0.4 + uy * s * 0.8, cy - uy * s * 0.4 - ux * s * 0.8)
        d.polygon([(c.px(p[0]), c.px(p[1])) for p in (tip, l, r)], fill=INTAKE_GREEN + (255,))

    c.slab(a0, 0.02, a1, depth, z0, INTAKE_H, shade(body, 0.95), top_fn=top, radius=0.03)


def skid(c, col, chamfer):
    W, D = c.v.W, c.v.D

    def top(box, lift):
        # Bolt pads round the edge: greebles, a tone step off the deck.
        x0, y0, x1, y1 = box
        inset = c.px(0.09)
        for t in (0.2, 0.4, 0.6, 0.8):
            for (px, py) in ((x0 + inset, y0 + (y1 - y0) * t), (x1 - inset, y0 + (y1 - y0) * t),
                             (x0 + (x1 - x0) * t, y1 - inset)):
                c.dots([(px / (CELL * SS), py / (CELL * SS))], 0.018, shade(col, 1.18))

    c.slab(0.05, 0.05, W - 0.05, D - 0.05, 0, 0.07, col, chamfer=chamfer, radius=0, top_fn=top)


# ------------------------------------------------------------------ jerry-rigging
WOOD = (122, 94, 66)           # timber chocks: the one thing on these that isn't metal


def patchwork_skid(c, rnd, plates):
    """A deck of mismatched scrap plates instead of one clean skid: a dark base, then plates of
    different tones overlapping it, weld beads down one edge of each, bolts in their corners."""
    W, D = c.v.W, c.v.D
    c.slab(0.05, 0.05, W - 0.05, D - 0.05, 0, 0.07, shade(DECK, 0.7), chamfer=0.2, radius=0)
    tones = [shade(DECK, 1.28), shade(RUST, 0.72), shade(OLIVE, 0.92), shade(STEEL, 1.02), shade(RUST, 0.56)]
    for i, (a0, f0, a1, f1) in enumerate(plates):
        col = tones[i % len(tones)]

        def top(box, lift, col=col, a0=a0, f0=f0, a1=a1, f1=f1):
            n = max(3, int((f1 - f0) / 0.08))
            bead = [c.v.pt(a0 + 0.02, f0 + 0.03 + (f1 - f0 - 0.06) * k / (n - 1)) for k in range(n)]
            c.dots([(x, y - lift) for x, y in bead], 0.009, shade(col, 1.3))
            corners = [c.v.pt(a, f) for a in (a0 + 0.05, a1 - 0.05) for f in (f0 + 0.05, f1 - 0.05)]
            c.dots([(x, y - lift) for x, y in corners], 0.012, shade(col, 1.35))
        # Just under the deck's own height in the draw order, so nothing standing on the deck -
        # the intake port included - is ever painted over by a plate.
        c.slab(a0, f0, a1, f1, 0.066, 0.018, col, top_fn=top, shadow=False, radius=0.01)


def scrapes(c, rnd, a0, f0, a1, f1, lift, col, n=4):
    """Bare metal where the paint has worn: short bright marks. Tone, not outline."""
    for _ in range(n):
        a = rnd.uniform(a0, a1)
        f = rnd.uniform(f0, f1)
        (x0, y0), (x1, y1) = c.v.pt(a, f), c.v.pt(a + rnd.uniform(-0.04, 0.04), f + rnd.uniform(0.03, 0.08))
        c.d.line([(c.px(x0), c.px(y0 - lift)), (c.px(x1), c.px(y1 - lift))],
                 fill=shade(col, 1.45) + (255,), width=max(2, c.px(0.01)))


def chock(c, a0, f0, a1, f1):
    """A timber block shimming something up, grain as two seams along it."""
    def top(box, lift):
        x0, y0, x1, y1 = box
        horiz = (x1 - x0) > (y1 - y0)
        for t in (0.35, 0.68):
            if horiz:
                c.seam((x0 + c.px(0.02), y0 + (y1 - y0) * t), (x1 - c.px(0.02), y0 + (y1 - y0) * t),
                       width=2 / 192, tone=shade(WOOD, 0.74))
            else:
                c.seam((x0 + (x1 - x0) * t, y0 + c.px(0.02)), (x0 + (x1 - x0) * t, y1 - c.px(0.02)),
                       width=2 / 192, tone=shade(WOOD, 0.74))
    c.slab(a0, f0, a1, f1, 0.07, 0.09, WOOD, top_fn=top, radius=0.01)


def gauge(c, a, f, z):
    """A salvaged pressure gauge: a pale dial and a dark needle, on a stalk."""
    def face(X, Y, R):
        r = int(R * 0.74)
        c.d.ellipse([X - r, Y - r - R // 10, X + r, Y + r - R // 10], fill=(214, 208, 190, 255))
        c.d.line([(X, Y - R // 10), (X + r * 0.6, Y - r * 0.5 - R // 10)], fill=(50, 46, 42, 255),
                 width=max(2, c.px(0.008)))
    c.cylinder(a, f, 0.05, z, 0.04, (150, 144, 132), cap_fn=face)


def radiator(c, a0, f0, a1, f1, col):
    """A salvaged radiator bolted on the side: a flat block with a rack of fins."""
    def top(box, lift):
        x0, y0, x1, y1 = box
        tall = (y1 - y0) > (x1 - x0)
        n = 8
        for k in range(1, n):
            t = k / n
            if tall:
                y = y0 + (y1 - y0) * t
                c.seam((x0 + c.px(0.025), y), (x1 - c.px(0.025), y), width=3 / 192, tone=shade(col, 0.66))
            else:
                x = x0 + (x1 - x0) * t
                c.seam((x, y0 + c.px(0.025)), (x, y1 - c.px(0.025)), width=3 / 192, tone=shade(col, 0.66))
    c.slab(a0, f0, a1, f1, 0.07, 0.2, col, top_fn=top, radius=0.02)


TAPE = (176, 166, 128)         # duct tape
BATTERY = (58, 60, 62)


def tape(c, a0, f0, a1, f1, z):
    """A wrap of duct tape: a pale band, flat, no shadow."""
    c.slab(a0, f0, a1, f1, z, 0.015, TAPE, shadow=False, radius=0.008)


def battery(c, a0, f0, a1, f1):
    """A car battery wired into the machine: a dark block, two terminal posts."""
    def top(box, lift):
        pts = [c.v.pt(a0 + (a1 - a0) * t, (f0 + f1) / 2) for t in (0.22, 0.78)]
        c.dots([(x, y - lift) for x, y in pts], 0.018, (150, 146, 138))
    c.slab(a0, f0, a1, f1, 0.07, 0.14, BATTERY, top_fn=top, radius=0.015)


def bucket(c, a, f):
    """A galvanised bucket catching drips, dark water in it."""
    def inside(X, Y, R):
        r = int(R * 0.78)
        c.d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12], fill=(52, 58, 60, 255))
    c.cylinder(a, f, 0.09, 0.07, 0.12, (156, 158, 154), rings=1, cap_fn=inside)


def loose_nuts(c, pts, lift=0.07 * LIFT):
    """Loose nuts and washers that have walked off across the deck."""
    c.add(0, lambda: c.dots([(c.v.pt(a, f)[0], c.v.pt(a, f)[1] - lift) for a, f in pts], 0.016,
                            (150, 146, 138)), 0.07)


def save_loose(layer, name, rot):
    """A loose-part layer: the same canvas as the building, only the parts that rattle on it.
    CompLooseParts draws it over the building and shakes it while the machine runs."""
    layer.flush()
    layer.save(f"{OUT}/Things/Building/Power/{name}_{rot}.png", silhouette_px=4)


# ------------------------------------------------------------------ tier 1: cobbled pellet stove
def cobbled_stove(rot):
    """Salvage: three mismatched plates welded into a firebox, a scavenged generator drum, a
    flue stack, home-brewed together with a car battery, tape and a drip bucket. The fire is its
    one accent and the only saturated colour on it. The parts that rattle - a dangling cable, a
    patch held on by one bolt, a pipe end hanging off a clamp, the gauges, loose nuts - are in two
    separate layers that CompLooseParts shakes while it burns."""
    v = View(rot, 2, 2, MARGIN_2X2)
    c = Canvas(v)
    la, lb = Canvas(v), Canvas(v)
    rnd = random.Random(11)
    patchwork_skid(c, rnd, [(0.1, 0.1, 0.56, 0.62), (1.44, 0.12, 1.9, 0.5), (0.12, 1.1, 0.7, 1.9),
                            (1.3, 1.24, 1.9, 1.9), (0.8, 1.35, 1.2, 1.9)])
    intake(c, 0.62, 0.34, INTAKE_Z, STEEL)

    # Firebox: three plates of different scrap side by side, welded. Each is its own slab, so
    # in the side views the nearest plate's face hides the others' walls by itself.
    plates = [(0.36, 0.72, RUST), (0.72, 1.08, STEEL), (1.08, 1.46, OLIVE)]
    FB0, FB1 = 0.5, 1.3   # firebox front and back, clear of the intake
    for i, (a0, a1, col) in enumerate(plates):
        def top(box, lift, col=col, i=i, a0=a0, a1=a1):
            x0, y0, x1, y1 = box
            # Weld beads along the seam with the next plate: a row of dots two steps lighter.
            if i < 2:
                sx, sy0 = v.pt(a1, FB0)
                ex, ey = v.pt(a1, FB1)
                n = 9
                pts = [(sx + (ex - sx) * k / n, sy0 + (ey - sy0) * k / n - lift) for k in range(n + 1)]
                c.dots(pts, 0.012, shade(col, 1.25))
            scrapes(c, rnd, a0 + 0.05, FB0 + 0.05, a1 - 0.05, FB1 - 0.2, lift, col, n=2)
            # Streaks and scuffs, faint tone marks.
            for _ in range(4):
                px = rnd.uniform(x0 + (x1 - x0) * 0.15, x1 - (x1 - x0) * 0.15)
                py = rnd.uniform(y0 + (y1 - y0) * 0.15, y1 - (y1 - y0) * 0.3)
                c.d.line([(px, py), (px, py + c.px(0.06))], fill=shade(col, 0.86) + (255,),
                         width=c.px(0.012))
        c.slab(a0, FB0, a1, FB1, 0.07, 0.34, col, top_fn=top, radius=0.02)
    # A patch bolted over the rust plate.
    def patch_top(box, lift):
        x0, y0, x1, y1 = box
        m = c.px(0.02)
        pts = [(x0 + m, y0 + m), (x1 - m, y0 + m), (x0 + m, y1 - m), (x1 - m, y1 - m)]
        c.dots([(x / (CELL * SS), y / (CELL * SS)) for x, y in pts], 0.012, shade(STEEL, 1.2))
    # Held on by one bolt: it rattles.
    la.slab(0.42, 0.98, 0.64, 1.2, 0.41, 0.02, shade(STEEL, 1.1), top_fn=patch_top, shadow=False, radius=0.01)

    # Fire window on top of the firebox: the one accent. A grate of bars over a hot ramp.
    def fire_top(box, lift):
        x0, y0, x1, y1 = box
        c.glow([x0 - c.px(0.06), y0 - c.px(0.06), x1 + c.px(0.06), y1 + c.px(0.06)], FIRE_DEEP, c.px(0.05), 90)
        c.ramp([x0 + c.px(0.02), y0 + c.px(0.02), x1 - c.px(0.02), y1 - c.px(0.02)], FIRE_HOT, FIRE_DEEP)
        bars = 5
        if v.along_a():
            for k in range(1, bars):
                x = x0 + (x1 - x0) * k / bars
                c.seam((x, y0), (x, y1), width=4 / 192, tone=(62, 50, 44))
        else:
            for k in range(1, bars):
                y = y0 + (y1 - y0) * k / bars
                c.seam((x0, y), (x1, y), width=4 / 192, tone=(62, 50, 44))
    c.slab(0.78, 0.62, 1.3, 0.98, 0.41, 0.015, (70, 64, 60), top_fn=fire_top, shadow=False, radius=0.02)

    # Flue stack at the back left: the round form. Soot inside, banded wall.
    def flue_cap(X, Y, R):
        d = c.d
        r = int(R * 0.62)
        d.ellipse([X - r, Y - r - R // 10, X + r, Y + r - R // 10], fill=(34, 32, 30, 255))
        r2 = int(R * 0.45)
        d.ellipse([X - r2, Y - r2 - R // 14, X + r2, Y + r2 - R // 14], fill=(24, 22, 20, 255))
    c.cylinder(0.62, 1.62, 0.24, 0.07, 0.62, shade(STEEL, 1.02), rings=3, cap_fn=flue_cap)

    # Generator drum at the back right, lying along `a`, cooling fins across it.
    def drum_top(box, lift):
        x0, y0, x1, y1 = box
        fins = 7
        if v.along_a():
            for k in range(1, fins):
                x = x0 + (x1 - x0) * k / fins
                c.seam((x, y0 + c.px(0.02)), (x, y1 - c.px(0.02)), width=3 / 192, tone=shade(OLIVE, 0.72))
        else:
            for k in range(1, fins):
                y = y0 + (y1 - y0) * k / fins
                c.seam((x0 + c.px(0.02), y), (x1 - c.px(0.02), y), width=3 / 192, tone=shade(OLIVE, 0.72))
    chock(c, 1.1, 1.4, 1.22, 1.9)
    chock(c, 1.7, 1.4, 1.82, 1.9)
    c.slab(1.06, 1.42, 1.86, 1.86, 0.11, 0.3, shade(OLIVE, 1.05), top_fn=drum_top, radius=0.1)
    c.slab(1.18, 1.3, 1.36, 1.42, 0.14, 0.14, shade(STEEL, 0.9), radius=0.02)   # coupling

    # Junction box on the right flank, and salvaged pipes up the left: straight runs only.
    def jbox_top(box, lift):
        x0, y0, x1, y1 = box
        horiz = v.along_a()
        for k in range(3):
            t = 0.3 + 0.2 * k
            if horiz:
                c.seam((x0 + c.px(0.03), y0 + (y1 - y0) * t), (x1 - c.px(0.03), y0 + (y1 - y0) * t),
                       tone=shade(STEEL, 0.78))
            else:
                c.seam((x0 + (x1 - x0) * t, y0 + c.px(0.03)), (x0 + (x1 - x0) * t, y1 - c.px(0.03)),
                       tone=shade(STEEL, 0.78))
    c.slab(1.56, 0.56, 1.88, 1.16, 0.07, 0.2, shade(STEEL, 0.92), top_fn=jbox_top, radius=0.02)
    c.pipe(0.14, 0.44, 0.14, 1.84, 0.07, 0.085, (104, 116, 120))
    c.pipe(0.26, 0.5, 0.26, 1.3, 0.07, 0.065, shade(RUST, 1.05))
    tape(c, 0.1, 1.02, 0.18, 1.1, 0.12)
    tape(c, 0.22, 0.86, 0.3, 0.92, 0.11)
    # Home-brew: a car battery wired to the junction box, and a bucket under the pipe ends.
    battery(c, 1.5, 0.14, 1.86, 0.4)
    c.cable(1.62, 0.4, 0.2, 1.66, 0.58, 0.27, 0.04, 0.035, (70, 70, 72))
    bucket(c, 0.2, 1.86)

    # Loose layer A: a cable dangling from the junction box to the drum, a pipe end on one clamp.
    la.cable(1.72, 1.12, 0.27, 1.44, 1.48, 0.41, 0.14, 0.04, (66, 64, 62))
    la.cable(1.84, 1.12, 0.27, 1.84, 1.5, 0.3, 0.1, 0.03, shade(RUST, 0.9))
    la.pipe(0.26, 1.34, 0.26, 1.62, 0.09, 0.065, shade(RUST, 1.0))
    # Loose layer B: the gauges on their stalks, a cable from the battery, nuts on the deck.
    gauge(lb, 1.4, 0.56, 0.41)
    gauge(lb, 0.48, 0.58, 0.41)
    lb.cable(1.78, 0.4, 0.2, 1.46, 0.64, 0.41, 0.08, 0.03, (80, 76, 72))
    loose_nuts(lb, [(0.9, 1.9), (1.0, 1.84), (0.34, 1.62), (1.5, 1.22)])
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_CobbledPelletStove_{rot}.png")
    save_loose(la, "STB_CobbledPelletStove_LooseA", rot)
    save_loose(lb, "STB_CobbledPelletStove_LooseB", rot)


# ------------------------------------------------------------------ tier 2: gasifier
def gasifier(rot):
    """The same job done properly: one housing, a sealed chamber, a filter bank, a turbine.
    Teal marks what is powered - the chamber seal, the status panel and the pilot lamp."""
    v = View(rot, 2, 2, MARGIN_2X2)
    c = Canvas(v)
    body = (138, 140, 142)
    skid(c, shade(body, 0.62), chamfer=0.26)
    intake(c, 0.62, 0.34, INTAKE_Z, body)

    def housing_top(box, lift):
        x0, y0, x1, y1 = box
        # Vent slats in the corners the chamber doesn't cover: a rack of short marks.
        for (fa0, ff0, fa1, ff1) in ((1.3, 0.5, 1.76, 0.72),):
            vx0, vy0, vx1, vy1 = v.rect(fa0, ff0, fa1, ff1)
            n = 6
            for k in range(n):
                if v.along_a():
                    x = vx0 + (vx1 - vx0) * (k + 0.5) / n
                    c.seam((c.px(x), c.px(vy0 - lift / 1)), (c.px(x), c.px(vy1 - lift)), width=5 / 192,
                           tone=shade(body, 0.78))
                else:
                    y = vy0 + (vy1 - vy0) * (k + 0.5) / n
                    c.seam((c.px(vx0), c.px(y - lift)), (c.px(vx1), c.px(y - lift)), width=5 / 192,
                           tone=shade(body, 0.78))

    c.slab(0.16, 0.44, 1.84, 1.5, 0.07, 0.32, body, top_fn=lambda b, l: housing_top(b, l), radius=0.08,
           chamfer=0.1)

    # Status panel on the housing, near the front right: a dark screen with a teal trace.
    def panel_top(box, lift):
        x0, y0, x1, y1 = box
        c.glow(box, TEAL, c.px(0.02), 70)
        m = c.px(0.025)
        c.ramp([x0 + m, y0 + m, x1 - m, y1 - m], (34, 44, 46), (28, 36, 38), c.px(0.01))
        if v.along_a():
            pts = [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * (0.5 + 0.25 * math.sin(t * 9))) for t in
                   [0.15 + 0.07 * k for k in range(11)]]
        else:
            pts = [(x0 + (x1 - x0) * (0.5 + 0.25 * math.sin(t * 9)), y0 + (y1 - y0) * t) for t in
                   [0.15 + 0.07 * k for k in range(11)]]
        c.d.line(pts, fill=TEAL + (255,), width=c.px(0.012))
    c.slab(1.28, 0.8, 1.74, 1.08, 0.39, 0.03, (70, 74, 78), top_fn=panel_top, shadow=False, radius=0.02)
    # Pilot lamp beside it.
    lx, ly = v.pt(1.51, 1.26)
    c.add(ly, lambda: c.dots([(lx, ly - 0.42 * LIFT)], 0.03, (120, 214, 170)), 0.42)

    # Gasifier chamber: the round form, a teal seal ring and a bolt circle.
    def chamber_cap(X, Y, R):
        d = c.d
        w = max(2, c.px(5 / 192))
        r = int(R * 0.8)
        d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12], outline=TEAL + (255,), width=w)
        for k in range(10):
            ang = k * math.pi / 5
            bx, by = X + math.cos(ang) * R * 0.9, Y - R // 20 + math.sin(ang) * R * 0.9
            rr = c.px(0.013)
            d.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=shade(body, 1.22) + (255,))
        r2 = int(R * 0.25)
        d.ellipse([X - r2, Y - r2 - R // 10, X + r2, Y + r2 - R // 10], fill=shade(body, 0.82) + (255,))
    c.cylinder(0.72, 1.0, 0.38, 0.39, 0.14, shade(body, 1.05), rings=1, cap_fn=chamber_cap)

    # Filter bank across the back: three identical canisters, the repeated mark.
    for a in (1.12, 1.4, 1.68):
        c.cylinder(a, 1.34, 0.12, 0.39, 0.2, (176, 180, 184), rings=1)

    # Turbine exhaust at the back left, and a straight manifold along the back edge.
    c.cylinder(0.36, 1.7, 0.15, 0.07, 0.5, shade(body, 1.0), rings=2,
               cap_fn=lambda X, Y, R: c.d.ellipse([X - int(R * .55), Y - int(R * .55) - R // 10,
                                                   X + int(R * .55), Y + int(R * .55) - R // 10],
                                                  fill=(40, 42, 44, 255)))
    c.pipe(0.6, 1.66, 1.86, 1.66, 0.07, 0.09, (150, 156, 164))
    c.pipe(0.6, 1.82, 1.86, 1.82, 0.07, 0.07, shade(TEAL, 0.9))
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_TrashbrickGasifier_{rot}.png")


# ------------------------------------------------------------------ large cobbled stove (3x4)
def large_cobbled_stove(rot):
    """3x4, the cobbled stove grown by accretion rather than design: four mismatched plates welded
    into one long firebox under a single wide fire window, a scrapped boiler drum lying behind it on
    timber chocks, two flues that don't match, a salvaged generator housing (no engine in it any
    more - the heat goes out on the pipe), a radiator bolted on the flank, battery, tape and a drip
    bucket. The fire is still the one accent. Loose parts in two layers, as on the small one."""
    v = View(rot, 3, 4, MARGIN_2X2)
    c = Canvas(v)
    la, lb = Canvas(v), Canvas(v)
    rnd = random.Random(31)
    patchwork_skid(c, rnd, [(0.1, 0.1, 0.9, 0.5), (2.1, 0.12, 2.9, 0.62), (0.12, 1.9, 0.9, 3.0),
                            (2.2, 2.0, 2.9, 3.1), (1.0, 3.2, 2.0, 3.9), (0.2, 3.3, 0.8, 3.9)])
    intake(c, 0.9, 0.34, INTAKE_Z, STEEL)

    plates = [(0.3, 0.9, RUST), (0.9, 1.45, STEEL), (1.45, 2.1, OLIVE), (2.1, 2.7, shade(RUST, 1.12))]
    FB0, FB1 = 0.5, 1.75
    for i, (a0, a1, col) in enumerate(plates):
        def top(box, lift, col=col, i=i, a0=a0, a1=a1):
            x0, y0, x1, y1 = box
            if i < len(plates) - 1:
                sx, sy0 = v.pt(a1, FB0)
                ex, ey = v.pt(a1, FB1)
                n = 12
                pts = [(sx + (ex - sx) * k / n, sy0 + (ey - sy0) * k / n - lift) for k in range(n + 1)]
                c.dots(pts, 0.012, shade(col, 1.25))
            scrapes(c, rnd, a0 + 0.05, FB0 + 0.05, a1 - 0.05, FB1 - 0.2, lift, col, n=3)
            for _ in range(4):
                px = rnd.uniform(x0 + (x1 - x0) * 0.15, x1 - (x1 - x0) * 0.15)
                py = rnd.uniform(y0 + (y1 - y0) * 0.15, y1 - (y1 - y0) * 0.3)
                c.d.line([(px, py), (px, py + c.px(0.06))], fill=shade(col, 0.86) + (255,),
                         width=c.px(0.012))
        # One plate stands a little proud of the others: they were never cut to match.
        c.slab(a0, FB0, a1, FB1, 0.07, 0.38 if i != 2 else 0.42, col, top_fn=top, radius=0.02)

    def fire_top(box, lift):
        x0, y0, x1, y1 = box
        c.glow([x0 - c.px(0.08), y0 - c.px(0.08), x1 + c.px(0.08), y1 + c.px(0.08)], FIRE_DEEP, c.px(0.06), 90)
        c.ramp([x0 + c.px(0.02), y0 + c.px(0.02), x1 - c.px(0.02), y1 - c.px(0.02)], FIRE_HOT, FIRE_DEEP)
        bars = 9
        for k in range(1, bars):
            if v.along_a():
                x = x0 + (x1 - x0) * k / bars
                c.seam((x, y0), (x, y1), width=4 / 192, tone=(62, 50, 44))
            else:
                y = y0 + (y1 - y0) * k / bars
                c.seam((x0, y), (x1, y), width=4 / 192, tone=(62, 50, 44))
    c.slab(0.75, 0.8, 2.25, 1.2, 0.45, 0.015, (70, 64, 60), top_fn=fire_top, shadow=False, radius=0.02)

    # Scrapped boiler drum lying along f behind the firebox, rivet rows round it, on chocks.
    def rivets(box, lift):
        for f in (2.1, 2.6, 3.1):
            c.dots([(v.pt(a, f)[0], v.pt(a, f)[1] - lift) for a in (0.5, 0.7, 0.9, 1.1)], 0.012,
                   shade(RUST, 1.3))
    chock(c, 0.35, 2.05, 1.25, 2.18)
    chock(c, 0.35, 3.1, 1.25, 3.23)
    c.drum(0.3, 1.9, 1.3, 3.4, 0.14, 0.4, shade(RUST, 1.08), axis="f", radius=0.14, top_fn=rivets)
    c.pipe(0.8, 1.75, 0.8, 1.9, 0.3, 0.1, shade(STEEL, 0.95))          # firebox to boiler

    # Two flues that don't match: a tall banded one, a short fat one with a rain cap.
    def soot(X, Y, R):
        r = int(R * 0.62)
        c.d.ellipse([X - r, Y - r - R // 10, X + r, Y + r - R // 10], fill=(34, 32, 30, 255))
        r2 = int(R * 0.45)
        c.d.ellipse([X - r2, Y - r2 - R // 14, X + r2, Y + r2 - R // 14], fill=(24, 22, 20, 255))
    c.cylinder(1.6, 2.4, 0.22, 0.07, 0.87, shade(STEEL, 1.02), rings=4, cap_fn=soot)
    c.cylinder(2.45, 2.2, 0.3, 0.07, 0.5, shade(OLIVE, 1.0), rings=2, cap_fn=soot)
    c.slab(2.2, 2.1, 2.7, 2.3, 0.6, 0.02, shade(RUST, 0.95), radius=0.02)   # rain cap on stilts

    # Salvaged generator housing at the back right, fins across it, on chocks. Gutted: it's a
    # manifold box now, and the hot water pipe leaves from it.
    def fins(box, lift):
        x0, y0, x1, y1 = box
        n = 8
        for k in range(1, n):
            if v.along_a():
                x = x0 + (x1 - x0) * k / n
                c.seam((x, y0 + c.px(0.02)), (x, y1 - c.px(0.02)), width=3 / 192, tone=shade(OLIVE, 0.72))
            else:
                y = y0 + (y1 - y0) * k / n
                c.seam((x0 + c.px(0.02), y), (x1 - c.px(0.02), y), width=3 / 192, tone=shade(OLIVE, 0.72))
    chock(c, 1.55, 3.0, 1.7, 3.7)
    chock(c, 2.55, 3.0, 2.7, 3.7)
    c.slab(1.5, 3.05, 2.8, 3.66, 0.11, 0.3, shade(OLIVE, 1.05), top_fn=fins, radius=0.1)
    c.pipe(1.3, 3.3, 1.5, 3.3, 0.25, 0.09, HOT)                        # boiler to manifold
    c.pipe(2.15, 3.66, 2.15, 3.92, 0.07, 0.1, HOT)                     # out to the network

    # Radiator bolted on the right flank, junction box, pipes up the left: straight runs only.
    radiator(c, 2.72, 0.62, 2.94, 1.62, shade(STEEL, 0.95))
    def jbox_top(box, lift):
        x0, y0, x1, y1 = box
        for k in range(3):
            t = 0.3 + 0.2 * k
            if v.along_a():
                c.seam((x0 + c.px(0.03), y0 + (y1 - y0) * t), (x1 - c.px(0.03), y0 + (y1 - y0) * t),
                       tone=shade(STEEL, 0.78))
            else:
                c.seam((x0 + (x1 - x0) * t, y0 + c.px(0.03)), (x0 + (x1 - x0) * t, y1 - c.px(0.03)),
                       tone=shade(STEEL, 0.78))
    c.slab(1.95, 1.85, 2.3, 2.3, 0.07, 0.22, shade(STEEL, 0.92), top_fn=jbox_top, radius=0.02)
    c.pipe(0.14, 0.44, 0.14, 3.2, 0.07, 0.085, (104, 116, 120))
    c.pipe(0.26, 0.5, 0.26, 1.8, 0.07, 0.065, shade(RUST, 1.05))
    tape(c, 0.1, 1.2, 0.18, 1.28, 0.12)
    tape(c, 0.1, 2.5, 0.18, 2.58, 0.12)
    tape(c, 0.22, 0.9, 0.3, 0.96, 0.11)
    battery(c, 2.3, 0.16, 2.8, 0.44)
    c.cable(2.45, 0.44, 0.2, 2.1, 1.85, 0.29, 0.06, 0.035, (70, 70, 72))
    bucket(c, 0.55, 3.6)
    bucket(c, 2.9, 3.85)

    # Loose layer A: cables off the junction box, a pipe end hanging off one clamp, a patch.
    la.cable(2.25, 2.3, 0.29, 2.0, 3.05, 0.41, 0.16, 0.04, (66, 64, 62))
    la.cable(2.05, 2.3, 0.29, 1.62, 2.62, 0.5, 0.12, 0.03, shade(RUST, 0.9))
    la.pipe(0.26, 1.84, 0.26, 2.2, 0.09, 0.065, shade(RUST, 1.0))
    def patch_top(box, lift):
        x0, y0, x1, y1 = box
        m = c.px(0.02)
        pts = [(x0 + m, y0 + m), (x1 - m, y0 + m), (x0 + m, y1 - m), (x1 - m, y1 - m)]
        la.dots([(x / (CELL * SS), y / (CELL * SS)) for x, y in pts], 0.012, shade(STEEL, 1.2))
    la.slab(0.4, 1.3, 0.72, 1.62, 0.45, 0.02, shade(STEEL, 1.1), top_fn=patch_top, shadow=False, radius=0.01)
    # Loose layer B: gauges on stalks, a cable from the battery, nuts on the deck.
    gauge(lb, 0.55, 0.62, 0.45)
    gauge(lb, 2.45, 0.62, 0.45)
    gauge(lb, 0.8, 2.0, 0.54)
    lb.cable(2.62, 0.44, 0.2, 2.62, 0.7, 0.45, 0.08, 0.03, (80, 76, 72))
    loose_nuts(lb, [(1.2, 3.9), (1.35, 3.84), (0.4, 1.86), (2.6, 1.8), (1.9, 0.44)])
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_LargeCobbledStove_{rot}.png")
    save_loose(la, "STB_LargeCobbledStove_LooseA", rot)
    save_loose(lb, "STB_LargeCobbledStove_LooseB", rot)


# ------------------------------------------------------------------ large gasifier (3x4)
def _chamber_cap(c, body):
    def cap(X, Y, R):
        d = c.d
        w = max(2, c.px(5 / 192))
        r = int(R * 0.8)
        d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12], outline=TEAL + (255,), width=w)
        for k in range(12):
            ang = k * math.pi / 6
            bx, by = X + math.cos(ang) * R * 0.9, Y - R // 20 + math.sin(ang) * R * 0.9
            rr = c.px(0.014)
            d.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=shade(body, 1.22) + (255,))
        r2 = int(R * 0.25)
        d.ellipse([X - r2, Y - r2 - R // 10, X + r2, Y + r2 - R // 10], fill=shade(body, 0.82) + (255,))
    return cap


def _status_panel(c, v, a0, f0, a1, f1, z):
    def panel_top(box, lift):
        x0, y0, x1, y1 = box
        c.glow(box, TEAL, c.px(0.02), 70)
        m = c.px(0.025)
        c.ramp([x0 + m, y0 + m, x1 - m, y1 - m], (34, 44, 46), (28, 36, 38), c.px(0.01))
        if v.along_a():
            pts = [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * (0.5 + 0.25 * math.sin(t * 9))) for t in
                   [0.15 + 0.07 * k for k in range(11)]]
        else:
            pts = [(x0 + (x1 - x0) * (0.5 + 0.25 * math.sin(t * 9)), y0 + (y1 - y0) * t) for t in
                   [0.15 + 0.07 * k for k in range(11)]]
        c.d.line(pts, fill=TEAL + (255,), width=c.px(0.012))
    c.slab(a0, f0, a1, f1, z, 0.03, (70, 74, 78), top_fn=panel_top, shadow=False, radius=0.02)


def _vents(c, v, body, rects):
    def fn(box, lift):
        for (fa0, ff0, fa1, ff1) in rects:
            vx0, vy0, vx1, vy1 = v.rect(fa0, ff0, fa1, ff1)
            n = 6
            for k in range(n):
                if v.along_a():
                    x = vx0 + (vx1 - vx0) * (k + 0.5) / n
                    c.seam((c.px(x), c.px(vy0 - lift)), (c.px(x), c.px(vy1 - lift)), width=5 / 192,
                           tone=shade(body, 0.78))
                else:
                    y = vy0 + (vy1 - vy0) * (k + 0.5) / n
                    c.seam((c.px(vx0), c.px(y - lift)), (c.px(vx1), c.px(y - lift)), width=5 / 192,
                           tone=shade(body, 0.78))
    return fn


def _stack(c, a, f, r, h, body):
    c.cylinder(a, f, r, 0.07, h, shade(body, 1.0), rings=2,
               cap_fn=lambda X, Y, R: c.d.ellipse([X - int(R * .55), Y - int(R * .55) - R // 10,
                                                   X + int(R * .55), Y + int(R * .55) - R // 10],
                                                  fill=(40, 42, 44, 255)))


def large_gasifier(rot):
    """3x4. The gasifier scaled up and laid out along its length: one big sealed chamber in the
    housing, a status panel, a row of five filter canisters, then a heat exchanger drum where the
    small one had its engine - the hot water leaves from here - and the exhaust stack. Teal still
    marks what is powered; the hot-water orange appears only at the outlet."""
    v = View(rot, 3, 4, MARGIN_2X2)
    c = Canvas(v)
    body = (138, 140, 142)
    skid(c, shade(body, 0.62), chamfer=0.3)
    intake(c, 0.9, 0.34, INTAKE_Z, body)
    c.slab(0.2, 0.44, 2.8, 2.5, 0.07, 0.34, body, top_fn=_vents(c, v, body, [(1.9, 0.55, 2.6, 0.8)]),
           radius=0.08, chamfer=0.12)
    _status_panel(c, v, 1.95, 0.95, 2.6, 1.3, 0.41)
    lx, ly = v.pt(2.28, 1.5)
    c.add(ly, lambda: c.dots([(lx, ly - 0.44 * LIFT)], 0.03, (120, 214, 170)), 0.44)
    c.cylinder(1.0, 1.4, 0.56, 0.41, 0.16, shade(body, 1.05), rings=1, cap_fn=_chamber_cap(c, body))
    for a in (0.5, 0.95, 1.4, 1.85, 2.3):
        c.cylinder(a, 2.22, 0.13, 0.41, 0.22, (176, 180, 184), rings=1)
    # Heat exchanger: a drum lying across the back, ribbed, fed from the housing.
    c.drum(0.9, 2.72, 2.7, 3.5, 0.07, 0.4, (120, 126, 132), axis="a", radius=0.12, ribs=7)
    c.pipe(1.8, 2.5, 1.8, 2.72, 0.2, 0.1, (150, 156, 164))
    _stack(c, 0.45, 3.0, 0.2, 0.62, body)
    c.pipe(0.9, 3.72, 2.86, 3.72, 0.07, 0.09, (150, 156, 164))
    c.pipe(0.9, 3.87, 2.86, 3.87, 0.07, 0.07, shade(TEAL, 0.9))
    c.pipe(2.2, 3.5, 2.2, 3.66, 0.07, 0.1, HOT)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_LargeGasifier_{rot}.png")


# ------------------------------------------------------------------ industrial gasifier (3x6)
def industrial_gasifier(rot):
    """3x6. Plant scale on one long skid: a walkway grating at the intake, two sealed chambers in
    series inside a long housing, a control column, a double row of filter canisters, then the
    big heat exchanger with its end cap, twin exhaust stacks and a straight manifold back along
    each side. Rows of identical marks carry the detail; teal for what's powered, orange only at
    the hot-water outlet."""
    v = View(rot, 3, 6, MARGIN_2X2)
    c = Canvas(v)
    body = (136, 139, 142)
    skid(c, shade(body, 0.6), chamfer=0.3)

    def grating(box, lift):
        for k in range(16):
            a = 0.3 + k * 0.15
            p0, p1 = v.pt(a, 0.44), v.pt(a, 0.58)
            c.seam((c.px(p0[0]), c.px(p0[1] - lift)), (c.px(p1[0]), c.px(p1[1] - lift)), width=3 / 192,
                   tone=shade(body, 0.5))
    c.slab(0.24, 0.42, 2.76, 0.6, 0.07, 0.015, shade(body, 0.72), top_fn=grating, shadow=False, radius=0.01)
    intake(c, 1.0, 0.36, INTAKE_Z, body)

    c.slab(0.2, 0.7, 2.8, 3.5, 0.07, 0.36, body,
           top_fn=_vents(c, v, body, [(1.95, 3.0, 2.65, 3.3), (0.35, 3.0, 1.05, 3.3)]), radius=0.08, chamfer=0.12)
    for f in (1.35, 2.45):
        c.cylinder(1.0, f, 0.5, 0.43, 0.16, shade(body, 1.05), rings=1, cap_fn=_chamber_cap(c, body))
    c.pipe(1.0, 1.85, 1.0, 1.95, 0.59, 0.12, shade(body, 1.1))           # chamber to chamber
    _status_panel(c, v, 1.95, 0.85, 2.62, 1.2, 0.43)
    _status_panel(c, v, 1.95, 1.3, 2.62, 1.55, 0.43)
    for f in (0.95, 1.12):
        x, y = v.pt(2.7, f)
        c.add(y, lambda x=x, y=y: c.dots([(x, y - 0.46 * LIFT)], 0.026, (120, 214, 170)), 0.46)
    for a in (2.0, 2.4):
        for f in (1.9, 2.25, 2.6, 2.95):
            c.cylinder(a, f, 0.12, 0.43, 0.2, (176, 180, 184), rings=1)

    # Heat exchanger: a long ribbed drum down the middle, an end cap, the outlet at the back.
    c.drum(0.55, 3.75, 2.05, 5.35, 0.07, 0.46, (120, 126, 132), axis="f", radius=0.14, ribs=9)
    c.drum(0.8, 5.35, 1.8, 5.7, 0.07, 0.32, shade((120, 126, 132), 0.95), axis="f", radius=0.08)
    c.pipe(1.3, 3.5, 1.3, 3.75, 0.24, 0.12, (150, 156, 164))
    c.pipe(1.3, 5.7, 1.3, 5.92, 0.07, 0.11, HOT)
    # Twin stacks on the right, a straight manifold down each side.
    _stack(c, 2.5, 3.9, 0.2, 0.8, body)
    _stack(c, 2.5, 4.6, 0.2, 0.8, body)
    c.pipe(0.18, 0.72, 0.18, 5.8, 0.07, 0.08, (150, 156, 164))
    c.pipe(2.84, 5.0, 2.84, 5.8, 0.07, 0.07, shade(TEAL, 0.9))
    def tbox(box, lift):
        x0, y0, x1, y1 = box
        for k in range(4):
            t = 0.25 + 0.17 * k
            if v.along_a():
                y = y0 + (y1 - y0) * t
                c.seam((x0 + c.px(0.03), y), (x1 - c.px(0.03), y), tone=shade(body, 0.66))
            else:
                x = x0 + (x1 - x0) * t
                c.seam((x, y0 + c.px(0.03)), (x, y1 - c.px(0.03)), tone=shade(body, 0.66))
    c.slab(2.2, 5.1, 2.72, 5.7, 0.07, 0.24, shade(body, 0.92), top_fn=tbox, radius=0.02)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_IndustrialGasifier_{rot}.png")


# ------------------------------------------------------------------ fuel hopper
def fuel_hopper(rot):
    """1x1. A steel box round a funnel, with its spout on the edge it faces: point it at a
    stove's intake. Patched like the cobbled stove."""
    v = View(rot, 1, 1, MARGIN_1X1)
    c = Canvas(v)

    def top(box, lift):
        x0, y0, x1, y1 = box
        # Funnel: nested tone steps getting darker toward a throat set toward the spout.
        tx, ty = v.pt(0.5, 0.36)
        tx, ty = c.px(tx), c.px(ty - lift)
        for k, f in enumerate((0.9, 0.8, 0.7, 0.6, 0.5, 0.4)):
            t = k / 6
            bx0 = x0 + (tx - x0) * t + c.px(0.06) * (1 - t)
            by0 = y0 + (ty - y0) * t + c.px(0.06) * (1 - t)
            bx1 = x1 + (tx - x1) * t - c.px(0.06) * (1 - t)
            by1 = y1 + (ty - y1) * t - c.px(0.06) * (1 - t)
            c.d.rounded_rectangle([bx0, by0, bx1, by1], radius=c.px(0.02), fill=shade(STEEL, f) + (255,))
        r = c.px(0.07)
        c.d.rounded_rectangle([tx - r, ty - r, tx + r, ty + r], radius=c.px(0.015), fill=(30, 30, 30, 255))
        c.dots([(p[0], p[1] - lift) for p in (v.pt(0.12, 0.12), v.pt(0.88, 0.12), v.pt(0.12, 0.88),
                                              v.pt(0.88, 0.88))], 0.022, shade(STEEL, 1.2))

    # Spout toward the facing edge, then the box over it.
    c.slab(0.36, 0.02, 0.64, 0.2, 0.0, 0.14, shade(STEEL, 0.85), radius=0.02)
    c.slab(0.08, 0.14, 0.92, 0.92, 0.0, 0.24, STEEL, chamfer=0.1, radius=0, top_fn=top)
    # A rust patch on the back rim.
    c.slab(0.5, 0.8, 0.8, 0.9, 0.24, 0.01, RUST, shadow=False, radius=0.01)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_FuelHopper_{rot}.png")


# ------------------------------------------------------------------ steam turbine
def steam_turbine(rot):
    """2x3. A real steam turbine set, laid out along the machine: steam chest and stop valve at the
    front, a rotor casing stepping WIDER from the high to the low pressure end with a bolted flange
    ring between each stage, bearing pedestals, a coupling, then the generator and its exciter.

    Rules as everywhere here: the casing and generator are round forms lying down (`drum`, shaded
    across their axis), detail is rows of identical marks - the casing's split-line bolts, flange
    bolts, generator ribs, walkway grating - and the hot-water orange appears ONLY where the pipe
    network comes in: the inlet line and the steam chest's ring.
    """
    v = View(rot, 2, 3, MARGIN_2X2)
    c = Canvas(v)
    steel = (132, 132, 130)
    casing = (140, 138, 134)
    gen = (120, 126, 132)          # generator: a cool step off the casing, not a colour
    skid(c, shade(steel, 0.6), chamfer=0.24)

    def pt_px(a, f, lift):
        x, y = v.pt(a, f)
        return x, y - lift

    # Walkway grating across the front of the skid: a rack of identical short marks.
    def grating(box, lift):
        for k in range(12):
            a = 0.3 + k * 0.12
            p0, p1 = pt_px(a, 0.1, lift), pt_px(a, 0.24, lift)
            c.seam((c.px(p0[0]), c.px(p0[1])), (c.px(p1[0]), c.px(p1[1])), width=3 / 192,
                   tone=shade(steel, 0.5))
    c.slab(0.24, 0.08, 1.76, 0.26, 0.07, 0.015, shade(steel, 0.72), top_fn=grating, shadow=False, radius=0.01)

    # Steam inlet: the network comes in at the front and runs straight to the steam chest.
    c.pipe(0.38, 0.1, 0.38, 0.54, 0.07, 0.11, HOT)

    def chest_cap(X, Y, R):
        w = max(2, c.px(6 / 192))
        r = int(R * 0.74)
        c.d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12], outline=HOT + (255,), width=w)
        rr = int(R * 0.3)
        c.d.ellipse([X - rr, Y - rr - R // 10, X + rr, Y + rr - R // 10], fill=shade(steel, 0.85) + (255,))
    c.cylinder(0.38, 0.74, 0.2, 0.07, 0.36, shade(steel, 1.05), rings=2, cap_fn=chest_cap)
    c.pipe(0.58, 0.74, 0.68, 0.74, 0.28, 0.08, shade(steel, 0.95))      # chest to casing

    # Front bearing pedestal.
    c.slab(0.8, 0.3, 1.2, 0.48, 0.07, 0.2, shade(steel, 0.9), radius=0.03)

    def split_line(a0, a1, f0, f1):
        """The casing's horizontal joint: a seam down the middle and a row of bolts either side."""
        def fn(box, lift):
            p0, p1 = pt_px(1.0, f0 + 0.04, lift), pt_px(1.0, f1 - 0.04, lift)
            c.seam((c.px(p0[0]), c.px(p0[1])), (c.px(p1[0]), c.px(p1[1])), width=4 / 192,
                   tone=shade(casing, 0.62))
            n = max(2, int((f1 - f0) / 0.1))
            pts = []
            for k in range(n):
                f = f0 + 0.07 + (f1 - f0 - 0.14) * k / max(1, n - 1)
                for da in (-0.07, 0.07):
                    pts.append(pt_px(1.0 + da, f, lift))
            c.dots(pts, 0.014, shade(casing, 1.22))
        return fn

    def flange_bolts(a0, a1, f):
        def fn(box, lift):
            n = 7
            c.dots([pt_px(a0 + 0.06 + (a1 - a0 - 0.12) * k / (n - 1), f, lift) for k in range(n)],
                   0.013, shade(casing, 1.25))
        return fn

    # Low pressure exhaust hood: the boxy base the widest stage sits on.
    c.slab(0.34, 1.54, 1.66, 1.98, 0.07, 0.16, shade(steel, 0.8), radius=0.03, chamfer=0.06)
    # Rotor casing, high to low pressure, stepping wider, with a flange ring at each step.
    stages = [(0.66, 1.34, 0.48, 1.0, 0.26), (0.56, 1.44, 1.04, 1.46, 0.3), (0.44, 1.56, 1.5, 1.96, 0.36)]
    for a0, a1, f0, f1, h in stages:
        c.drum(a0, f0, a1, f1, 0.07 if h < 0.36 else 0.23, h if h < 0.36 else 0.22, casing, axis="f",
               radius=0.08, top_fn=split_line(a0, a1, f0, f1))
    for a0, a1, f, h in ((0.62, 1.38, 1.02, 0.3), (0.52, 1.48, 1.48, 0.36)):
        c.drum(a0, f - 0.03, a1, f + 0.03, 0.07, h + 0.02, shade(casing, 1.1), axis="f", radius=0.02,
               shadow=False, top_fn=flange_bolts(a0, a1, f))

    # Rear bearing, coupling, generator with its cooling ribs, and the exciter behind it.
    c.slab(0.8, 1.96, 1.2, 2.12, 0.07, 0.24, shade(steel, 0.9), radius=0.03)
    c.drum(0.9, 1.98, 1.1, 2.14, 0.2, 0.1, shade(steel, 1.1), axis="f", radius=0.02, shadow=False)
    c.drum(0.5, 2.14, 1.5, 2.72, 0.07, 0.38, gen, axis="f", radius=0.1, ribs=7)
    c.drum(0.72, 2.72, 1.28, 2.9, 0.07, 0.26, shade(gen, 0.95), axis="f", radius=0.06)

    # Lube oil: an upright tank on the far side, a straight feed line along the bearings.
    c.cylinder(1.72, 0.56, 0.15, 0.07, 0.3, shade(steel, 1.0), rings=1)
    c.pipe(1.72, 0.72, 1.72, 2.26, 0.07, 0.06, shade(steel, 0.85))
    # Generator terminal box, a rack of slats on it.
    def tbox(box, lift):
        x0, y0, x1, y1 = box
        for k in range(4):
            t = 0.25 + 0.17 * k
            if v.along_a():
                y = y0 + (y1 - y0) * t
                c.seam((x0 + c.px(0.03), y), (x1 - c.px(0.03), y), tone=shade(steel, 0.66))
            else:
                x = x0 + (x1 - x0) * t
                c.seam((x, y0 + c.px(0.03)), (x, y1 - c.px(0.03)), tone=shade(steel, 0.66))
    c.slab(1.6, 2.28, 1.9, 2.7, 0.07, 0.22, shade(steel, 0.92), top_fn=tbox, radius=0.02)
    # Condensate line back from the exhaust hood, straight down the near side.
    c.pipe(0.16, 1.6, 0.16, 2.86, 0.07, 0.08, shade(steel, 0.9))
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_SteamTurbine_{rot}.png")


# ------------------------------------------------------------------ cobbled steam turbine
def cobbled_turbine(rot):
    """2x3, the low-tech turbine, jerry-rigged. Same anatomy as the steam turbine - steam chest at
    the front, casing stepping wider towards the exhaust, bearings, coupling, generator - so it still
    reads as a turbine, but nothing about it was made to go together: each casing stage is a
    different scrap and sits a little off the line of the last, straps and weld beads hold the
    joints, timber chocks shim the drums up, a salvaged radiator and a spare tank are bolted on the
    side, a bypass pipe is lifted over the top, and gauges are stuck on where there was room. It
    stands on a patchwork of scrap plates. The only saturated colour is still the hot-water inlet."""
    v = View(rot, 2, 3, MARGIN_2X2)
    c = Canvas(v)
    la, lb = Canvas(v), Canvas(v)
    rnd = random.Random(23)
    patchwork_skid(c, rnd, [(0.1, 0.1, 0.84, 0.44), (1.06, 0.1, 1.9, 0.62), (0.1, 1.2, 0.5, 2.3),
                            (1.5, 1.7, 1.9, 2.9), (0.3, 2.5, 1.2, 2.9), (0.6, 0.5, 1.4, 1.1)])

    def pt_px(a, f, lift):
        x, y = v.pt(a, f)
        return x, y - lift

    # Steam inlet, and a squat steam chest made from an old tank, a gauge on a stalk beside it.
    c.pipe(0.38, 0.1, 0.38, 0.56, 0.07, 0.11, HOT)

    def chest_cap(X, Y, R):
        w = max(2, c.px(6 / 192))
        r = int(R * 0.72)
        c.d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12], outline=HOT + (255,), width=w)
        rr = int(R * 0.34)
        c.d.ellipse([X - rr, Y - rr - R // 10, X + rr, Y + rr - R // 10], fill=shade(RUST, 0.72) + (255,))
    c.cylinder(0.38, 0.74, 0.2, 0.07, 0.3, shade(RUST, 1.05), rings=3, cap_fn=chest_cap)
    gauge(lb, 0.18, 0.58, 0.14)
    c.pipe(0.58, 0.74, 0.7, 0.74, 0.25, 0.08, shade(STEEL, 0.9))

    # Front bearing: a block of plate shimmed up on timber.
    chock(c, 0.76, 0.28, 1.24, 0.36)
    c.slab(0.8, 0.32, 1.2, 0.5, 0.1, 0.16, shade(STEEL, 0.82), radius=0.02)

    def welded(col, a_mid, f0, f1, patch=None):
        """A casing stage: weld beads down its own split line, scrapes, maybe a bolted patch."""
        def fn(box, lift):
            n = max(4, int((f1 - f0) / 0.05))
            c.dots([pt_px(a_mid, f0 + 0.05 + (f1 - f0 - 0.1) * k / (n - 1), lift) for k in range(n)],
                   0.011, shade(col, 1.28))
            scrapes(c, rnd, a_mid - 0.25, f0 + 0.06, a_mid + 0.25, f1 - 0.12, lift, col, n=3)
            if patch:
                pa0, pf0, pa1, pf1 = patch
                b = v.rect(pa0, pf0, pa1, pf1)
                x0, y0, x1, y1 = c.box_px(b[0], b[1] - lift, b[2], b[3] - lift)
                c.d.rounded_rectangle([x0, y0, x1, y1], radius=c.px(0.01), fill=shade(STEEL, 1.12) + (255,))
                c.dots([pt_px(a, f, lift) for a in (pa0 + 0.03, pa1 - 0.03) for f in (pf0 + 0.03, pf1 - 0.03)],
                       0.01, shade(STEEL, 1.3))
        return fn

    def strap(a0, a1, f):
        def fn(box, lift):
            c.dots([pt_px(a0 + 0.05, f, lift), pt_px(a1 - 0.05, f, lift)], 0.014, shade(STEEL, 1.25))
        return fn

    # Exhaust end on a plain box; chocks under the middle stage where the casing sags.
    c.slab(0.38, 1.56, 1.62, 1.98, 0.07, 0.12, shade(STEEL, 0.66), radius=0.02)
    chock(c, 0.5, 1.12, 0.62, 1.4)
    chock(c, 1.38, 1.12, 1.5, 1.4)
    # Three stages of three scraps, each a little off the line of the last.
    stages = [(0.69, 1.37, 0.48, 1.0, 0.07, 0.26, RUST, (0.8, 0.6, 0.96, 0.78)),
              (0.54, 1.42, 1.04, 1.46, 0.1, 0.28, STEEL, None),
              (0.42, 1.54, 1.5, 1.96, 0.19, 0.22, OLIVE, (1.18, 1.62, 1.42, 1.84))]
    for a0, a1, f0, f1, z0, h, col, patch in stages:
        c.drum(a0, f0, a1, f1, z0, h, col, axis="f", radius=0.06,
               top_fn=welded(col, (a0 + a1) / 2, f0, f1, patch))
    for a0, a1, f, h in ((0.64, 1.38, 1.02, 0.3), (0.5, 1.46, 1.48, 0.36)):
        c.drum(a0, f - 0.025, a1, f + 0.025, 0.07, h + 0.02, shade(STEEL, 0.74), axis="f", radius=0.01,
               shadow=False, top_fn=strap(a0, a1, f))

    # Rear bearing, a flywheel, and the salvaged generator on timber, a mismatched end cap.
    c.slab(0.8, 1.96, 1.2, 2.1, 0.07, 0.22, shade(STEEL, 0.82), radius=0.02)
    c.drum(0.3, 2.04, 1.7, 2.14, 0.07, 0.42, shade(STEEL, 0.95), axis="f", radius=0.05)
    chock(c, 0.44, 2.22, 1.56, 2.3)
    chock(c, 0.44, 2.6, 1.56, 2.68)
    c.drum(0.5, 2.18, 1.5, 2.72, 0.12, 0.34, shade(OLIVE, 1.05), axis="f", radius=0.1, ribs=6)
    c.drum(0.76, 2.72, 1.28, 2.88, 0.07, 0.22, shade(RUST, 0.9), axis="f", radius=0.05)

    # Bolted on down the far side: a salvaged radiator, a spare tank, a junction box.
    radiator(c, 1.62, 0.66, 1.92, 1.36, shade(STEEL, 0.9))
    c.cylinder(1.77, 1.62, 0.13, 0.07, 0.28, shade(OLIVE, 0.95), rings=1)
    def jbox(box, lift):
        x0, y0, x1, y1 = box
        c.seam((x0 + c.px(0.03), (y0 + y1) / 2), (x1 - c.px(0.03), (y0 + y1) / 2), tone=shade(OLIVE, 0.7))
    c.slab(1.62, 2.3, 1.9, 2.66, 0.07, 0.2, shade(OLIVE, 0.9), top_fn=jbox, radius=0.02)

    # Salvaged pipes up the near side, taped at the joints; a battery and a drip bucket.
    c.pipe(0.14, 0.9, 0.14, 2.86, 0.07, 0.085, (104, 116, 120))
    tape(c, 0.1, 1.9, 0.18, 2.0, 0.12)
    tape(c, 0.1, 1.2, 0.18, 1.27, 0.12)
    battery(c, 1.3, 0.12, 1.62, 0.34)
    bucket(c, 0.34, 2.76)
    c.cable(1.46, 0.34, 0.2, 1.72, 0.62, 0.27, 0.05, 0.035, (70, 70, 72))

    # Loose layer A: the bypass pipe lifted over the casing, hanging off its clamps, a cover plate
    # held by one bolt on the exhaust stage, and a cable looped from the junction box.
    la.pipe(0.3, 0.62, 0.3, 1.56, 0.36, 0.06, shade(RUST, 1.1))
    la.slab(0.62, 1.58, 0.9, 1.76, 0.43, 0.015, shade(STEEL, 1.12), shadow=False, radius=0.01)
    la.cable(1.72, 2.32, 0.27, 1.46, 2.36, 0.46, 0.12, 0.04, (66, 64, 62))
    la.cable(1.84, 2.3, 0.27, 1.8, 1.36, 0.27, 0.16, 0.03, shade(RUST, 0.9))
    # Loose layer B: gauges on wobbly stalks, a second cable, nuts walking across the deck.
    gauge(lb, 1.76, 2.2, 0.1)
    gauge(lb, 1.1, 0.24, 0.1)
    lb.cable(1.62, 0.24, 0.2, 1.24, 0.42, 0.26, 0.06, 0.03, (80, 76, 72))
    loose_nuts(lb, [(0.6, 2.9), (0.72, 2.84), (1.5, 1.2), (0.26, 0.4)])
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_CobbledTurbine_{rot}.png")
    save_loose(la, "STB_CobbledTurbine_LooseA", rot)
    save_loose(lb, "STB_CobbledTurbine_LooseB", rot)


# ------------------------------------------------------------------ hot water pipe
PIPE_TILE = 128


def _pipe_tile(links, blueprint=False, lag=(104, 100, 96), band=(150, 146, 140), stripe_col=HOT, width=0.26):
    """One 128px tile of the linked atlas. links = (north, east, south, west). Drawn at SS and
    reduced, tone only inside, the silhouette ring outside, like everything else here."""
    T = PIPE_TILE * SS
    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = int(T * width)         # lagged pipe: a little thicker than a chemfuel line
    cx = cy = T // 2
    n, e, s_, wst = links

    def run(horiz, a, b):
        """A straight run from a to b along one axis, through the tile centre."""
        if blueprint:
            box = [a, cy - w // 2, b, cy + w // 2] if horiz else [cx - w // 2, a, cx + w // 2, b]
            d.rectangle(box, fill=(150, 200, 240, 150))
            return
        L = abs(b - a)
        g = Image.new("RGBA", (L, w) if horiz else (w, L))
        gd = ImageDraw.Draw(g)
        for k in range(w):
            t = abs(k / (w - 1) - 0.35) / 0.65          # lit from above / the left
            col = shade(lag, 1.22 - 0.5 * t) + (255,)
            if horiz:
                gd.line([(0, k), (L, k)], fill=col)
            else:
                gd.line([(k, 0), (k, L)], fill=col)
        # The network's one accent: a thin stripe down the pipe's crown (hot water's orange).
        if stripe_col is not None:
            stripe = max(2, w // 7)
            off = int(w * 0.3)
            if horiz:
                gd.rectangle([0, off, L, off + stripe], fill=stripe_col + (255,))
            else:
                gd.rectangle([off, 0, off + stripe, L], fill=stripe_col + (255,))
        # Straps every quarter tile, a tone step lighter - greebles, not outlines.
        step = T // 4
        for p in range(step // 2, L, step):
            sw = max(2, T // 40)
            if horiz:
                gd.rectangle([p, 0, p + sw, w], fill=band + (255,))
            else:
                gd.rectangle([0, p, w, p + sw], fill=band + (255,))
        img.paste(g, (a, cy - w // 2) if horiz else (cx - w // 2, a))

    count = sum(links)
    if count == 0:
        run(True, int(T * 0.2), int(T * 0.8))
    if n:
        run(False, 0, cy + w // 2 if count > 1 else cy)
    if s_:
        run(False, cy - w // 2 if count > 1 else cy, T)
    if e:
        run(True, cx - w // 2 if count > 1 else cx, T)
    if wst:
        run(True, 0, cx + w // 2 if count > 1 else cx)
    # Joints and dead ends get a flange boss: a round form, a tone lighter.
    straight = count == 2 and ((n and s_) or (e and wst))
    if not straight:
        R = int(w * 0.72)
        if blueprint:
            d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(150, 200, 240, 150))
        else:
            d.ellipse([cx - R, cy - R + R // 6, cx + R, cy + R + R // 6], fill=shade(band, 0.7) + (255,))
            d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=band + (255,))
            r2 = int(R * 0.62)
            d.ellipse([cx - r2, cy - r2 - R // 10, cx + r2, cy + r2 - R // 10], fill=shade(band, 1.12) + (255,))
    if not blueprint:
        from stb_draw import SILHOUETTE
        from PIL import ImageFilter
        a = img.split()[3].point(lambda v: 255 if v > 150 else 0)
        ring = a.filter(ImageFilter.MaxFilter(2 * 2 * SS // 2 + 1))
        base = Image.new("RGBA", img.size, SILHOUETTE + (255,))
        base.putalpha(ring)
        base.alpha_composite(img)
        img = base
    return img.resize((PIPE_TILE, PIPE_TILE), Image.LANCZOS)


def hot_water_pipe():
    """Graphic_Linked atlas: 4x4 tiles, tile i for link bits N=1 E=2 S=4 W=8, placed at column
    i % 4 and row 3 - i // 4 from the top (the UV origin is bottom-left). Read off a working VE
    atlas rather than remembered; verify_art.py checks the straights land in the right tiles."""
    import os
    for name, bp in (("STB_HotWaterPipe_Atlas", False), ("STB_HotWaterPipe_Blueprint_Atlas", True)):
        atlas = Image.new("RGBA", (PIPE_TILE * 4, PIPE_TILE * 4), (0, 0, 0, 0))
        for i in range(16):
            links = (bool(i & 1), bool(i & 2), bool(i & 4), bool(i & 8))
            atlas.alpha_composite(_pipe_tile(links, bp), ((i % 4) * PIPE_TILE, (3 - i // 4) * PIPE_TILE))
        path = f"{OUT}/Things/Building/Linked/{name}.png"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        atlas.save(path)
        print("wrote", path, atlas.size)
    icon = _pipe_tile((False, True, False, True))
    icon.save(f"{OUT}/Things/Building/Linked/STB_HotWaterPipe_MenuIcon.png")
    print("wrote", f"{OUT}/Things/Building/Linked/STB_HotWaterPipe_MenuIcon.png")


def hot_water_valve():
    """1x1 at drawSize 1.5: a flange block across the line with a handwheel on top."""
    v = View("south", 1, 1, MARGIN_1X1)
    c = Canvas(v)
    c.pipe(0.0, 0.5, 1.0, 0.5, 0.0, 0.2, (104, 100, 96))
    c.slab(0.26, 0.28, 0.74, 0.72, 0.0, 0.2, (140, 136, 130), radius=0.04, chamfer=0.06)
    def wheel(X, Y, R):
        w = max(2, c.px(7 / 192))
        r = int(R * 1.0)
        c.d.ellipse([X - r, Y - r, X + r, Y + r], outline=HOT + (255,), width=w)
        for ang in (0, 60, 120):
            dx, dy = math.cos(math.radians(ang)) * r, math.sin(math.radians(ang)) * r
            c.d.line([(X - dx, Y - dy), (X + dx, Y + dy)], fill=HOT + (255,), width=max(2, w * 2 // 3))
        rr = int(R * 0.25)
        c.d.ellipse([X - rr, Y - rr, X + rr, Y + rr], fill=(170, 166, 160, 255))
    c.cylinder(0.5, 0.5, 0.2, 0.2, 0.12, (120, 116, 110), cap_fn=wheel)
    c.flush()
    c.save(f"{OUT}/Things/Building/Linked/STB_HotWaterValve.png")


# ------------------------------------------------------------------ radiator and heat accumulator
def hot_water_radiator():
    """1x1 at drawSize 1.5. A cast-iron column radiator from above: a row of identical columns -
    the repeated mark - on two feet, a hot-water inlet stub the only orange."""
    v = View("south", 1, 1, MARGIN_1X1)
    c = Canvas(v)
    iron = (118, 116, 112)
    c.pipe(0.08, 0.5, 0.22, 0.5, 0.0, 0.1, HOT)
    for k in range(7):
        a0 = 0.2 + k * 0.092
        c.drum(a0, 0.3, a0 + 0.078, 0.7, 0.0, 0.34, iron, axis="f", radius=0.035, shadow=(k == 6))
    # The top rail joining the columns, and a bleed valve.
    c.slab(0.2, 0.62, 0.84, 0.7, 0.34, 0.02, shade(iron, 1.08), shadow=False, radius=0.01)
    c.dots([(v.pt(0.86, 0.66)[0], v.pt(0.86, 0.66)[1] - 0.36 * LIFT)], 0.02, (170, 164, 150))
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_HotWaterRadiator.png")


def cobbled_radiator():
    """1x1 at drawSize 1.5, the low-tech radiator. A serpentine of salvaged pipe - three straight
    runs of three different scraps, joined by crude elbow blocks at alternate ends (the runs stay
    straight; the bends are blocks) - lashed with wire, one joint taped, sitting on timber chocks
    over a rust-stained plate. The hot-water inlet is still the only orange."""
    v = View("south", 1, 1, MARGIN_1X1)
    c = Canvas(v)
    rnd = random.Random(31)
    c.slab(0.12, 0.14, 0.88, 0.86, 0.0, 0.02, shade(RUST, 0.62), shadow=False, radius=0.02)
    chock(c, 0.14, 0.2, 0.86, 0.28)
    chock(c, 0.14, 0.72, 0.86, 0.8)
    runs = [(0.32, (104, 116, 120)), (0.5, shade(RUST, 1.05)), (0.68, shade(STEEL, 0.95))]
    for a, col in runs:
        c.pipe(a, 0.2, a, 0.8, 0.16, 0.13, col)
    # Elbow blocks at alternate ends: the serpentine's bends.
    c.slab(0.26, 0.74, 0.56, 0.86, 0.16, 0.12, shade(STEEL, 0.8), radius=0.02)
    c.slab(0.44, 0.14, 0.74, 0.26, 0.16, 0.12, shade(STEEL, 0.8), radius=0.02)
    # Wire lashing across the runs, a taped joint, the inlet.
    for f in (0.4, 0.62):
        p0, p1 = v.pt(0.24, f), v.pt(0.76, f)
        c.add(p1[1], lambda p0=p0, p1=p1: c.seam((c.px(p0[0]), c.px(p0[1] - 0.26 * LIFT)),
                                                 (c.px(p1[0]), c.px(p1[1] - 0.26 * LIFT)),
                                                 width=3 / 192, tone=(150, 144, 130)), 0.3)
    tape(c, 0.62, 0.46, 0.74, 0.54, 0.28)
    c.pipe(0.08, 0.8, 0.26, 0.8, 0.14, 0.1, HOT)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_CobbledRadiator.png")


def heat_accumulator():
    """2x2 at drawSize 3. A big lagged tank standing on a skid: the round form, lagging bands as
    its repeated marks, a manway and a gauge on the cap, a hot-water inlet the only orange."""
    v = View("south", 2, 2, MARGIN_2X2)
    c = Canvas(v)
    skid(c, shade(STEEL, 0.62), chamfer=0.22)
    c.pipe(0.12, 0.3, 0.12, 1.0, 0.07, 0.1, HOT)
    c.pipe(0.12, 1.0, 0.4, 1.0, 0.07, 0.1, HOT)

    def cap(X, Y, R):
        # Manway: a bolted round hatch, and a relief valve beside it.
        r = int(R * 0.34)
        oy = -R // 10
        c.d.ellipse([X - r, Y - r + oy, X + r, Y + r + oy], fill=shade(STEEL, 0.92) + (255,))
        for k in range(10):
            ang = k * math.pi / 5
            bx, by = X + math.cos(ang) * r * 0.82, Y + oy + math.sin(ang) * r * 0.82
            rr = max(2, c.px(0.012))
            c.d.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=shade(STEEL, 1.25) + (255,))
        vx, vy = X + int(R * 0.55), Y - int(R * 0.45)
        rv = max(3, c.px(0.05))
        c.d.ellipse([vx - rv, vy - rv, vx + rv, vy + rv], fill=shade(STEEL, 0.8) + (255,))
    c.cylinder(1.02, 0.98, 0.78, 0.07, 0.62, (150, 146, 138), rings=5, cap_fn=cap)
    gauge(c, 1.72, 0.3, 0.07)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_HeatAccumulator.png")


def exhaust_tank():
    """2x2 at drawSize 3. The exhaust expansion tank: the Overpressure Tank's round form, but
    sooty steel with a hazard band near the top, a soot-black exhaust inlet in place of the
    orange hot-water one, and a pressure gauge."""
    v = View("south", 2, 2, MARGIN_2X2)
    c = Canvas(v)
    skid(c, shade(STEEL, 0.55), chamfer=0.22)
    soot = (62, 60, 58)
    c.pipe(0.12, 0.3, 0.12, 1.0, 0.07, 0.1, soot)
    c.pipe(0.12, 1.0, 0.4, 1.0, 0.07, 0.1, soot)

    def cap(X, Y, R):
        # A domed cap: a hazard ring of yellow and black blocks round a dark relief valve.
        for k in range(16):
            a0 = k * 2 * math.pi / 16
            col = (214, 176, 52) if k % 2 == 0 else (40, 38, 36)
            pts = [(X, Y - R // 10)]
            for t in range(5):
                ang = a0 + t * (2 * math.pi / 16) / 4
                pts.append((X + math.cos(ang) * R * 0.78, Y - R // 10 + math.sin(ang) * R * 0.78))
            c.d.polygon(pts, fill=col + (255,))
        r = int(R * 0.58)
        c.d.ellipse([X - r, Y - r - R // 10, X + r, Y + r - R // 10], fill=(108, 104, 98, 255))
        rv = max(3, c.px(0.07))
        c.d.ellipse([X - rv, Y - rv - R // 10, X + rv, Y + rv - R // 10], fill=(46, 44, 42, 255))
    c.cylinder(1.02, 0.98, 0.78, 0.07, 0.62, (118, 114, 106), wall=(84, 80, 74), rings=3, cap_fn=cap)
    gauge(c, 1.72, 0.3, 0.07)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_ExhaustTank.png")


def fire_glow():
    """The firebox flicker's texture: a soft orange blob, no silhouette. CompMachineEffects draws it
    with the MoteGlow shader at a flickering strength."""
    import os
    px = 128
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    for y in range(px):
        for x in range(px):
            d = math.hypot(x - px / 2, y - px / 2) / (px / 2)
            a = max(0.0, 1 - d) ** 1.8
            img.putpixel((x, y), (255, int(150 + 60 * a), int(60 + 40 * a), int(255 * a)))
    path = f"{OUT}/Things/Building/Power/STB_FireGlow.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", path)


def pellets():
    """Graphic_StackCount: three piles, small to large. Items are 128px, one cell."""
    px = 128
    for name, n, seed in (("a", 5, 1), ("b", 11, 2), ("c", 20, 3)):
        img = Image.new("RGBA", (px * SS, px * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rnd = random.Random(seed)
        u = px * SS / 32
        spread = {5: 6, 11: 10, 20: 14}[n]
        pts = sorted(((16 + rnd.gauss(0, spread / 2), 17 + rnd.gauss(0, spread / 3)) for _ in range(n)),
                     key=lambda p: p[1])
        for x, y in pts:
            ang = rnd.uniform(0, math.pi)
            ln, r = 4.6, 2.0
            dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2 * 0.6
            base = (104 + rnd.randint(-10, 10), 80 + rnd.randint(-8, 8), 58 + rnd.randint(-6, 6))
            # Tone only: a darker body, a lit ridge offset up. No outlines between pellets.
            for off, f in ((0.5, 0.62), (0, 0.9), (-0.45, 1.12)):
                w = r * (1 if f < 1 else 0.55)
                d.line([((x - dx) * u, (y - dy + off) * u), ((x + dx) * u, (y + dy + off) * u)],
                       fill=shade(base, f) + (255,), width=int(2 * w * u))
                for ex, ey in ((x - dx, y - dy + off), (x + dx, y + dy + off)):
                    d.ellipse([(ex - w) * u, (ey - w) * u, (ex + w) * u, (ey + w) * u], fill=shade(base, f) + (255,))
        from stb_draw import SILHOUETTE
        from PIL import ImageFilter
        a = img.split()[3].point(lambda v: 255 if v > 40 else 0)
        ring = a.filter(ImageFilter.MaxFilter(2 * 3 * SS // 2 + 1))
        base_img = Image.new("RGBA", img.size, SILHOUETTE + (255,))
        base_img.putalpha(ring)
        base_img.alpha_composite(img)
        out = base_img.resize((px, px), Image.LANCZOS)
        path = f"{OUT}/Things/Item/Resource/STB_SludgePellets/STB_SludgePellets_{name}.png"
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.save(path)
        print("wrote", path, out.size)


# ------------------------------------------------------------------ turbine cooling fan (overlay)
def turbine_rotor():
    """The generator's cooling fan, drawn flat and spun by CompMachineEffects while the turbine
    makes power. Top-down: a dark hub, five blades as tone wedges, a guard ring. Round, so it
    reads the same at any angle; the blades are what shows it turning. Black only at the rim."""
    px = 128
    S = px * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    R = S * 0.46
    d.ellipse([c - R, c - R, c + R, c + R], fill=(14, 14, 14, 255))                  # silhouette
    r = R * 0.93
    d.ellipse([c - r, c - r, c + r, c + r], fill=shade(STEEL, 0.62) + (255,))       # guard ring
    r2 = R * 0.84
    d.ellipse([c - r2, c - r2, c + r2, c + r2], fill=(46, 46, 46, 255))              # the dark behind
    for k in range(5):
        a0 = k * 72 - 14
        d.pieslice([c - r2, c - r2, c + r2, c + r2], a0, a0 + 34, fill=shade(STEEL, 1.08) + (255,))
        d.pieslice([c - r2, c - r2, c + r2, c + r2], a0 + 24, a0 + 34, fill=shade(STEEL, 0.86) + (255,))
    rh = R * 0.26
    d.ellipse([c - rh, c - rh, c + rh, c + rh], fill=shade(STEEL, 0.74) + (255,))    # hub
    rb = R * 0.1
    d.ellipse([c - rb, c - rb, c + rb, c + rb], fill=shade(STEEL, 1.2) + (255,))     # spinner cap
    out = img.resize((px, px), Image.LANCZOS)
    path = f"{OUT}/Things/Building/Power/STB_TurbineRotor.png"
    out.save(path)
    print("wrote", path, out.size)


# ------------------------------------------------------------------ steam vent (in a wall)
def steam_vent(rot):
    """1x1, hung on a wall: the wall is on the front edge (f = 0, the side it faces, as vanilla's
    wall-attachment placeworker wants), and the def nudges the sprite onto the wall's face. A
    backing plate, a steel box standing off it with a rack of louvres on top, and the hot-water line
    coming up into it - the network's orange, its one accent. It blows away from the wall."""
    v = View(rot, 1, 1, 0.15)
    c = Canvas(v)
    body = (122, 122, 120)

    def plate_top(box, lift):
        c.dots([(p[0], p[1] - lift) for p in (v.pt(0.14, 0.05), v.pt(0.86, 0.05))], 0.02, shade(body, 1.2))
    c.slab(0.06, 0.0, 0.94, 0.12, 0.0, 0.55, shade(body, 0.88), radius=0.02, top_fn=plate_top)

    def louvres(box, lift):
        # Slots across the box, the repeated mark, angled away from the wall.
        for k in range(4):
            f0 = 0.2 + k * 0.1
            x0, y0, x1, y1 = v.rect(0.26, f0, 0.74, f0 + 0.05)
            c.d.rectangle(c.box_px(x0, y0 - lift, x1, y1 - lift), fill=(40, 40, 40, 255))
            lx0, ly0, lx1, ly1 = v.rect(0.26, f0 + 0.05, 0.74, f0 + 0.066)
            c.d.rectangle(c.box_px(lx0, ly0 - lift, lx1, ly1 - lift), fill=shade(body, 1.25) + (255,))
    c.slab(0.2, 0.1, 0.8, 0.66, 0.1, 0.34, body, radius=0.03, chamfer=0.04, top_fn=louvres)
    # The hot-water line up the wall into the box.
    c.pipe(0.5, 0.02, 0.5, 0.14, 0.02, 0.1, HOT)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_SteamVent_{rot}.png")


def steam_vent_ground():
    """1x1 at drawSize 1.5: a standpipe steam vent - the hot-water line turned up out of the
    ground, a banded riser, and a louvred mushroom cap. Not rotatable: one view."""
    v = View("south", 1, 1, MARGIN_1X1)
    c = Canvas(v)
    c.slab(0.14, 0.14, 0.86, 0.86, 0.0, 0.05, shade(DECK, 0.95), chamfer=0.12, radius=0)
    c.pipe(0.5, 0.86, 0.5, 1.0, 0.0, 0.12, HOT)              # the line coming in
    c.cylinder(0.5, 0.52, 0.16, 0.05, 0.45, shade(STEEL, 1.0), rings=2)

    def cap(X, Y, R):
        # Louvre rings round the cap: tone steps inward, dark gaps between.
        for k, f in enumerate((0.86, 0.66, 0.46)):
            r = int(R * f)
            c.d.ellipse([X - r, Y - r - R // 12, X + r, Y + r - R // 12],
                        fill=(shade(STEEL, 1.15 - 0.08 * k) if k % 2 == 0 else (46, 46, 46)) + (255,))
        rr = int(R * 0.22)
        c.d.ellipse([X - rr, Y - rr - R // 10, X + rr, Y + rr - R // 10], fill=shade(STEEL, 1.3) + (255,))
    c.cylinder(0.5, 0.52, 0.36, 0.5, 0.1, shade(STEEL, 1.05), rings=1, cap_fn=cap)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_SteamVentGround.png")


# ------------------------------------------------------------------ exhaust pipe and port
SOOT = (70, 68, 66)


def exhaust_pipe():
    """The exhaust network's linked atlas, laid out like the hot water pipe's: a narrower bare
    flue pipe, sooty, its bands a step lighter, and no accent - soot is its colour."""
    import os
    kw = dict(lag=(88, 85, 82), band=(112, 108, 104), stripe_col=None, width=0.2)
    for name, bp in (("STB_ExhaustPipe_Atlas", False), ("STB_ExhaustPipe_Blueprint_Atlas", True)):
        atlas = Image.new("RGBA", (PIPE_TILE * 4, PIPE_TILE * 4), (0, 0, 0, 0))
        for i in range(16):
            links = (bool(i & 1), bool(i & 2), bool(i & 4), bool(i & 8))
            atlas.alpha_composite(_pipe_tile(links, bp, **kw), ((i % 4) * PIPE_TILE, (3 - i // 4) * PIPE_TILE))
        path = f"{OUT}/Things/Building/Linked/{name}.png"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        atlas.save(path)
        print("wrote", path, atlas.size)
    icon = _pipe_tile((False, True, False, True), **kw)
    icon.save(f"{OUT}/Things/Building/Linked/STB_ExhaustPipe_MenuIcon.png")
    print("wrote", f"{OUT}/Things/Building/Linked/STB_ExhaustPipe_MenuIcon.png")


def exhaust_port():
    """1x1 at drawSize 1.5: a squat banded stack on a base plate, like the flues on the burners,
    with a soot-black mouth and soot run down from its lip. Not rotatable: one view."""
    v = View("south", 1, 1, MARGIN_1X1)
    c = Canvas(v)
    c.slab(0.1, 0.1, 0.9, 0.9, 0.0, 0.06, shade(DECK, 0.9), chamfer=0.12, radius=0)
    c.pipe(0.5, 0.9, 0.5, 1.0, 0.02, 0.12, (88, 85, 82))       # the flue coming in at the back

    def mouth(X, Y, R):
        r = int(R * 0.66)
        c.d.ellipse([X - r, Y - r - R // 10, X + r, Y + r - R // 10], fill=(30, 28, 26, 255))
        r2 = int(R * 0.46)
        c.d.ellipse([X - r2, Y - r2 - R // 14, X + r2, Y + r2 - R // 14], fill=(20, 19, 18, 255))
    c.cylinder(0.5, 0.56, 0.26, 0.06, 0.62, shade(STEEL, 1.0), wall=shade(STEEL, 0.72), rings=3, cap_fn=mouth)
    # Soot run down the stack from the lip: tone marks, not outlines.
    sx, sy = v.pt(0.5, 0.56)
    for dx, ln in ((-0.14, 0.12), (-0.05, 0.18), (0.08, 0.1)):
        c.add(sy + 0.3, lambda dx=dx, ln=ln: c.d.line([(c.px(sx + dx), c.px(sy - 0.09)), (c.px(sx + dx), c.px(sy - 0.09 + ln))],
                                                        fill=SOOT + (255,), width=c.px(0.035)), 0.7)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_ExhaustPort.png")


def exhaust_port_wall(rot):
    """1x1, hung on a wall: the wall is on the front edge (f = 0, the side it faces, as vanilla's
    wall-attachment placeworker wants), and the def nudges the sprite onto the wall's face. A
    backing plate bolted to the wall, a squat duct standing off it, and a soot-black hooded mouth
    blowing away from the wall. No accent - soot is the exhaust network's colour."""
    v = View(rot, 1, 1, 0.15)
    c = Canvas(v)
    plate = (104, 102, 100)
    duct = (118, 116, 112)

    def plate_top(box, lift):
        c.dots([(p[0], p[1] - lift) for p in (v.pt(0.14, 0.05), v.pt(0.86, 0.05))], 0.02, shade(plate, 1.25))
    c.slab(0.06, 0.0, 0.94, 0.12, 0.0, 0.55, plate, radius=0.02, top_fn=plate_top)

    def duct_top(box, lift):
        # Soot fanning from the mouth back over the top: tone steps, not outlines.
        x0, y0, x1, y1 = v.rect(0.3, 0.36, 0.7, 0.6)
        c.d.rectangle(c.box_px(x0, y0 - lift, x1, y1 - lift), fill=shade(duct, 0.8) + (255,))
    c.slab(0.24, 0.1, 0.76, 0.62, 0.12, 0.34, duct, radius=0.04, chamfer=0.03, top_fn=duct_top)
    # The hooded mouth on the far end of the duct: a dark slot under a lip.
    c.slab(0.28, 0.58, 0.72, 0.7, 0.14, 0.26, (30, 28, 26), wall=(22, 21, 20), radius=0.02)
    c.slab(0.22, 0.56, 0.78, 0.72, 0.4, 0.04, shade(duct, 1.1), radius=0.02)
    c.flush()
    c.save(f"{OUT}/Things/Building/Power/STB_ExhaustPortWall_{rot}.png")


# ------------------------------------------------------------------ turbine moving parts (animation frames)
MOTION_FRAMES = 8
BRASS = (160, 142, 104)        # governor weights: a warm metal tone, not a second accent


def _mpt(v, a, f, z):
    """Machine point to canvas cells, lifted by its height."""
    x, y = v.pt(a, f)
    return x, y - z * LIFT


def _mpoly(c, v, pts, col):
    c.d.polygon([(c.px(x), c.px(y)) for x, y in (_mpt(v, a, f, z) for a, f, z in pts)], fill=col + (255,))


def _mdisc(c, x, y, r, col, rim=None):
    R, X, Y = c.px(r), c.px(x), c.px(y)
    if rim:
        c.d.ellipse([X - R, Y - R, X + R, Y + R], fill=rim + (255,))
        R = int(R * 0.8)
    c.d.ellipse([X - R, Y - R, X + R, Y + R], fill=col + (255,))


def _governor(c, v, t, a, f, z):
    """Flyball governor on a spindle: two weights whirling round it. Seen from above, a spinning
    pair; the 8 frames turn it half a revolution, a full cycle for two identical weights."""
    s0 = _mpt(v, a, f, z)
    top = _mpt(v, a, f, z + 0.24)
    th = t * math.pi
    R = 0.13
    balls = [(top[0] + math.cos(th + k) * R, top[1] + math.sin(th + k) * R * 0.55, math.sin(th + k))
             for k in (0, math.pi)]
    balls.sort(key=lambda b: b[2])                      # the far ball first, then the spindle
    for i, (bx, by, depth) in enumerate(balls):
        if i == 1:
            c.d.line([(c.px(s0[0]), c.px(s0[1])), (c.px(top[0]), c.px(top[1]))],
                     fill=shade(STEEL, 0.85) + (255,), width=c.px(0.035))
        c.d.line([(c.px(top[0]), c.px(top[1])), (c.px(bx), c.px(by))], fill=shade(STEEL, 1.1) + (255,),
                 width=c.px(0.02))
        _mdisc(c, bx, by, 0.05, shade(BRASS, 1.0 + 0.15 * depth), rim=shade(BRASS, 0.6))
    _mdisc(c, top[0], top[1], 0.035, shade(STEEL, 1.25), rim=shade(STEEL, 0.7))


def _coupling(c, v, t, a0, a1, f0, f1, z):
    """The shaft coupling: a flange lying along the shaft, its bolt heads rolling across it. Six
    bolts; the 8 frames roll them one bolt spacing on, a seamless cycle."""
    c.drum(a0, f0, a1, f1, 0.07, z - 0.07, shade(STEEL, 1.02), axis="f", radius=0.03, shadow=False)
    c.flush()
    mid, half = (a0 + a1) / 2, (a1 - a0) / 2
    fm = (f0 + f1) / 2
    for k in range(6):
        th = (k + t) * 2 * math.pi / 6
        if math.cos(th) <= 0.05:
            continue                                    # round the back of the shaft
        x, y = _mpt(v, mid + math.sin(th) * half * 0.8, fm, z)
        _mdisc(c, x, y, 0.035 * (0.45 + 0.55 * math.cos(th)), shade(STEEL, 1.0 + 0.45 * math.cos(th)),
               rim=shade(STEEL, 0.55))


def _hatch(c, v, t, a0, a1, f0, f1, z):
    """An inspection hatch in the casing top: a bolted frame round a dark window, the rotor's
    blade rows streaming across it (across the shaft, which runs along f). The 8 frames move them
    one blade pitch."""
    rim = 0.04
    _mpoly(c, v, [(a0 - rim, f0 - rim, z), (a1 + rim, f0 - rim, z), (a1 + rim, f1 + rim, z), (a0 - rim, f1 + rim, z)],
           shade(STEEL, 0.9))
    _mpoly(c, v, [(a0, f0, z), (a1, f0, z), (a1, f1, z), (a0, f1, z)], (28, 28, 30))
    pitch = (a1 - a0) / 7
    rows = ((f0 + 0.02, (f0 + f1) / 2 - 0.015, 0.0), ((f0 + f1) / 2 + 0.015, f1 - 0.02, 0.5))
    for g0, g1, shift in rows:
        for k in range(-2, 10):
            b = a0 + (k + shift + t) * pitch
            quad = [(b, g0), (b + pitch * 0.42, g0), (b + pitch * 0.22, g1), (b - pitch * 0.2, g1)]
            quad = [(min(max(qa, a0), a1), qf) for qa, qf in quad]
            if max(q[0] for q in quad) - min(q[0] for q in quad) < 0.004:
                continue
            _mpoly(c, v, [(qa, qf, z) for qa, qf in quad], shade(STEEL, 1.18))
    for k in range(5):
        for ff in (f0 - rim / 2, f1 + rim / 2):
            x, y = _mpt(v, a0 + (a1 - a0) * k / 4, ff, z)
            _mdisc(c, x, y, 0.014, shade(STEEL, 1.3))


def _flywheel_rim(c, v, t, a0, a1, f0, f1, z):
    """The cobbled flywheel's rim, from above: three balance weights rolling across it (it turns
    about the shaft, along f), squashed as they go round the ends. The 8 frames: a third of a turn."""
    _mpoly(c, v, [(a0, f0, z), (a1, f0, z), (a1, f1, z), (a0, f1, z)], (64, 62, 60))
    g0, g1 = f0 + (f1 - f0) * 0.3, f0 + (f1 - f0) * 0.5
    _mpoly(c, v, [(a0 + 0.03, g0, z), (a1 - 0.03, g0, z), (a1 - 0.03, g1, z), (a0 + 0.03, g1, z)], shade(STEEL, 0.95))
    L = a1 - a0
    for k in range(3):
        centre = a0 + (((k + t) / 3) % 1.0) * L
        edge = min(centre - a0, a1 - centre) / (L / 2)
        w = 0.07 * (0.3 + 0.7 * min(1.0, edge * 2.2))
        lo, hi = max(a0, centre - w / 2), min(a1, centre + w / 2)
        if hi - lo < 0.005:
            continue
        _mpoly(c, v, [(lo, f0 + 0.01, z), (hi, f0 + 0.01, z), (hi, f1 - 0.01, z), (lo, f1 - 0.01, z)], (150, 112, 82))


def _belt(c, v, t, p1, p2, half):
    """A flat belt from a pulley on the flywheel's end to one on the salvaged dynamo: three laced
    splices running round it, both pulleys turning. p1, p2 = (a, f, z, radius)."""
    runs = []
    for side in (-1, 1):
        s = _mpt(v, p1[0] + side * half, p1[1], p1[2])
        e = _mpt(v, p2[0] + side * half * 0.8, p2[1], p2[2])
        runs.append((s, e) if side < 0 else (e, s))     # out along one run, back along the other
    for pa in (p1, p2):
        x, y = _mpt(v, pa[0], pa[1], pa[2])
        _mdisc(c, x, y, pa[3], shade(STEEL, 0.78), rim=shade(STEEL, 0.5))
    for s, e in runs:
        c.d.line([(c.px(s[0]), c.px(s[1])), (c.px(e[0]), c.px(e[1]))], fill=(74, 62, 52, 255), width=c.px(0.035))
    for k in range(3):
        u = ((k + t) / 3) % 1.0
        (s, e), w = (runs[0], u * 2) if u < 0.5 else (runs[1], (u - 0.5) * 2)
        _mdisc(c, s[0] + (e[0] - s[0]) * w, s[1] + (e[1] - s[1]) * w, 0.02, shade(BRASS, 0.95))
    for pa, turns in ((p1, 1.0), (p2, 2.0)):
        x, y = _mpt(v, pa[0], pa[1], pa[2])
        base = t * turns * 2 * math.pi / 3
        for k in range(3):
            th = base + k * 2 * math.pi / 3
            c.d.line([(c.px(x), c.px(y)), (c.px(x + math.cos(th) * pa[3] * 0.75), c.px(y + math.sin(th) * pa[3] * 0.75))],
                     fill=shade(STEEL, 1.2) + (255,), width=c.px(0.016))
        _mdisc(c, x, y, pa[3] * 0.28, shade(STEEL, 1.1))


def turbine_motion(rot):
    """Animation frames for the turbines' moving parts, drawn over the sprite by CompMachineEffects:
    the steam turbine's flyball governor, shaft coupling and blade hatch; the cobbled turbine's
    flywheel rim and belt drive to a salvaged dynamo. Same canvas as the building, in all views."""
    v = View(rot, 2, 3, MARGIN_2X2)
    for i in range(MOTION_FRAMES):
        t = i / MOTION_FRAMES
        c = Canvas(v)
        _hatch(c, v, t, 0.68, 1.32, 1.12, 1.38, 0.37)
        _coupling(c, v, t, 0.8, 1.2, 1.97, 2.15, 0.34)
        _governor(c, v, t, 0.38, 0.74, 0.43)
        c.flush()
        c.save(f"{OUT}/Things/Building/Power/STB_SteamTurbine_Motion{i}_{rot}.png", silhouette_px=3)
        c = Canvas(v)
        _flywheel_rim(c, v, t, 0.3, 1.7, 2.04, 2.14, 0.49)
        _belt(c, v, t, (1.8, 2.09, 0.3, 0.09), (1.77, 1.62, 0.38, 0.07), 0.07)
        c.flush()
        c.save(f"{OUT}/Things/Building/Power/STB_CobbledTurbine_Motion{i}_{rot}.png", silhouette_px=3)


if __name__ == "__main__":
    for r in ROTS:
        cobbled_stove(r)
        gasifier(r)
        large_cobbled_stove(r)
        large_gasifier(r)
        industrial_gasifier(r)
        fuel_hopper(r)
        steam_vent(r)
        exhaust_port_wall(r)
        steam_turbine(r)
        cobbled_turbine(r)
        turbine_motion(r)
    hot_water_pipe()
    exhaust_pipe()
    exhaust_port()
    steam_vent_ground()
    hot_water_valve()
    hot_water_radiator()
    cobbled_radiator()
    heat_accumulator()
    exhaust_tank()
    fire_glow()
    turbine_rotor()
    pellets()
