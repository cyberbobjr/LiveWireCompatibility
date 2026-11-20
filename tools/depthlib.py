"""B42 depth map of Artel Manufactory's machines (ADR-003). Local tool, not run in CI.

Artel ships DEPTH_Artel.png with texels for tiles 200-223 only: its machines fall back to the
engine's default depth, and the engine does not draw their highlight from the front. The engine
merges the depth maps of all mods tile by tile (TilesetDepthTexture.mergeTileset): this mod ships
its own DEPTH_Artel.png with the machine tiles only, every other tile left empty.

Each machine sprite is taken as the smallest box standing on the floor (rectangular footprint in
the tile, height) whose projection covers its pixels; every sprite pixel gets the depth of the
front-most point of the box on its view ray (engine projection and encoding, ADR-003 D02):
    screen   sx = 64 (wx - wy) + 64,   sy = 32 (wx + wy) + 192 - 192 wz   (128 x 256 cell, wz in levels)
    depth    1 - 0.25 (wx + wy) - 0.5 wz
    texel    floor(depth * 255) in R, G and B, alpha 255
A sprite pixel outside the box takes the farthest depth of its neighbours: no drawn pixel is left
without a texel (the engine does not draw a pixel whose depth texel is transparent).

Reads the Workshop copy of Artel in READ-ONLY mode.
Usage: python tools/build_artel_depth.py [--workshop DIR] [--forge DIR] [--out PNG]
Exit code: 0 written, every sprite pixel with a texel; 1 a pixel without texel; 2 Artel not found.
"""
import argparse
import io
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ARTEL_ID = "3794133594"
DEFAULT_WORKSHOP = r"D:\SteamLibrary\steamapps\workshop\content\108600"
DEFAULT_FORGE = r"E:\pz-tools\pz-sprite-forge"
OUT = os.path.join(ROOT, "Contents", "mods", "batman_LiveWireCompatibility", "common", "media", "depthmaps",
                   "DEPTH_Artel.png")
CELL_W, CELL_H, COLUMNS = 128, 256, 8
#: Footprint grid, in tile units.
STEP = 0.05
#: Share of the sprite pixels the box must cover; the rest takes a neighbour's depth.
COVERAGE = 0.995


def depth_at(s, wz):
    """Normalized depth of a point with wx + wy = s, wz in levels."""
    return 1.0 - 0.25 * s - 0.5 * wz


def s_interval(px, py, x0, x1, y0, y1):
    """Range of s = wx + wy on each pixel ray inside the footprint."""
    u = (px + 0.5 - 64.0) / 64.0
    lo = np.maximum(2 * x0 - u, 2 * y0 + u)
    hi = np.minimum(2 * x1 - u, 2 * y1 + u)
    return lo, hi


def wz_of(s, py):
    return (32.0 * s + 192.0 - (py + 0.5)) / 192.0


#: Half-width range of the square footprint, in tiles: up to 1.0 so that a piece of a multi-tile
#: furniture drawn over its neighbours is still covered.
HALF_MAX = 1.0


class _Best:
    """Smallest box covering COVERAGE of the pixels, and failing that the box covering the most."""

    def __init__(self):
        self.box, self.volume, self.fallback, self.share = None, None, None, -1.0

    def consider(self, px, py, x0, x1, y0, y1):
        lo, hi = s_interval(px, py, x0, x1, y0, y1)
        ok = (lo <= hi) & (wz_of(hi, py) >= 0.0)
        share = ok.mean()
        if share <= 0:
            return
        need = wz_of(lo[ok], py[ok])
        h = max(0.01, float(np.quantile(need, min(1.0, COVERAGE / share))))
        box = (float(x0), float(x1), float(y0), float(y1), h)
        if share >= COVERAGE:
            volume = (x1 - x0) * (y1 - y0) * h
            if self.volume is None or volume < self.volume:
                self.box, self.volume = box, volume
        elif share > self.share:
            self.fallback, self.share = box, share


def fit_box(px, py):
    """Smallest square floor box centred on the tile covering COVERAGE of the pixels:
    (x0, x1, y0, y1, h); failing that, the one covering the most.
    The silhouette of a box is ambiguous along the view axis (a thin slab far back can draw the same
    outline), so the shape is fixed: square, centred on its tile like most furniture. Only its
    half-width and height come from the sprite. A module against a wall gets a box a little in front
    of it: every pixel still has a depth, occlusion is approximate."""
    best = _Best()
    for half in np.round(np.arange(STEP / 2, HALF_MAX + 1e-9, STEP / 2), 4):
        best.consider(px, py, 0.5 - half, 0.5 + half, 0.5 - half, 0.5 + half)
    return best.box if best.box is not None else best.fallback


def box_depth(px, py, box):
    """Depth of the front-most point of the box on each pixel ray, NaN outside the box."""
    x0, x1, y0, y1, h = box
    lo, hi = s_interval(px, py, x0, x1, y0, y1)
    s_top = (192.0 * h - 192.0 + (py + 0.5)) / 32.0  # s where the ray reaches height h
    s_hit = np.minimum(hi, s_top)
    inside = (lo <= s_hit) & (wz_of(s_hit, py) >= -1e-9)
    d = depth_at(s_hit, wz_of(s_hit, py))
    return np.where(inside, d, np.nan)


def fill(depth, mask):
    """Sprite pixels without depth take the farthest (largest) neighbour depth; floor depth last."""
    for _ in range(64):
        missing = mask & np.isnan(depth)
        if not missing.any():
            return depth
        padded = np.pad(depth, 1, constant_values=np.nan)
        stack = [padded[1 + dy:1 + dy + depth.shape[0], 1 + dx:1 + dx + depth.shape[1]]
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
        stacked = np.stack(stack)
        around = np.where(np.isnan(stacked).all(axis=0), np.nan,
                          np.max(np.where(np.isnan(stacked), -np.inf, stacked), axis=0))
        depth = np.where(missing & ~np.isnan(around), around, depth)
    ys, xs = np.nonzero(mask & np.isnan(depth))
    floor_s = (ys + 0.5 - 192.0) / 32.0
    depth[ys, xs] = np.clip(depth_at(floor_s, 0.0), 0.5, 1.0)
    return depth


def tile_depth(alpha):
    """Depth grid (NaN where the sprite draws nothing), the box and the number of pixels left without depth."""
    mask = alpha > 0
    py, px = np.nonzero(mask)
    depth = np.full(alpha.shape, np.nan)
    box = fit_box(px.astype(float), py.astype(float))
    if box is not None:
        depth[py, px] = box_depth(px.astype(float), py.astype(float), box)
    depth = fill(depth, mask)
    depth[~mask] = np.nan
    left = int((mask & np.isnan(depth)).sum())
    return depth, box, left


def artel_sprites():
    """Indices of the Artel sprites billed by the profile."""
    import check_sprites
    for name, _workshop, sprites in check_sprites.profiles():
        if name == "Artel":
            return sorted(int(s.rsplit("_", 1)[1]) for s in sprites)
    return []


def sprite_alphas(pack_path, forge, indices):
    from PIL import Image
    sys.path.insert(0, forge)
    from pzforge.packfile import TexturePack
    wanted = {"Artel_%d" % i: i for i in indices}
    out = {}
    with open(pack_path, "rb") as f:
        pack = TexturePack.loads(f.read())
    for page in pack.pages:
        img = Image.open(io.BytesIO(page.png)).convert("RGBA")
        for e in page.entries:
            if e.name in wanted:
                cell = Image.new("RGBA", (e.ow, e.oh), (0, 0, 0, 0))
                cell.paste(img.crop((e.x, e.y, e.x + e.w, e.y + e.h)), (e.ox, e.oy))
                out[wanted[e.name]] = np.array(cell.getchannel("A"))
    return out


def main(argv=None):
    from PIL import Image
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workshop", default=DEFAULT_WORKSHOP)
    ap.add_argument("--forge", default=DEFAULT_FORGE)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    base = os.path.join(a.workshop, ARTEL_ID, "mods", "ArtelManufactory")
    pack = os.path.join(base, "42", "media", "texturepacks", "Artel.pack")
    theirs = os.path.join(base, "common", "media", "depthmaps", "DEPTH_Artel.png")
    if not (os.path.isfile(pack) and os.path.isfile(theirs)):
        print("Artel Manufactory not found under %s" % base)
        return 2
    size = Image.open(theirs).size  # same size as Artel's map: the merge keeps the smallest
    their_alpha = np.array(Image.open(theirs).convert("RGBA").getchannel("A"))
    indices = artel_sprites()
    alphas = sprite_alphas(pack, a.forge, indices)
    sheet = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    bad = 0
    for i in indices:
        if i not in alphas:
            print("Artel_%d: not in the pack, skipped" % i)
            bad += 1
            continue
        ox, oy = (i % COLUMNS) * CELL_W, (i // COLUMNS) * CELL_H
        if their_alpha[oy:oy + CELL_H, ox:ox + CELL_W].any():
            print("Artel_%d: Artel already has a depth for it, left to Artel" % i)
            continue
        depth, box, left = tile_depth(alphas[i])
        bad += left
        drawn = ~np.isnan(depth)
        value = np.floor(np.clip(np.nan_to_num(depth), 0.0, 1.0) * 255.0).astype(np.uint8)
        cell = sheet[oy:oy + CELL_H, ox:ox + CELL_W]
        for c in range(3):
            cell[..., c] = np.where(drawn, value, 0)
        cell[..., 3] = np.where(drawn, 255, 0)
        print("Artel_%d: %d px, box %s, without depth %d" % (
            i, int(drawn.sum()), "none" if box is None else
            "x %.2f-%.2f y %.2f-%.2f h %.2f" % box, left))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    Image.fromarray(sheet, "RGBA").save(a.out)
    print("wrote %s (%dx%d), %d sprites" % (a.out, size[0], size[1], len(indices)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
