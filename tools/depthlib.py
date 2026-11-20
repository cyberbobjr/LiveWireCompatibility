"""B42 tile depth: engine projection, box fit, depth sources and sprite masks (ADR-003).

Depth of a sprite pixel, engine projection and encoding (ADR-003 D02):
    screen   sx = 64 (wx - wy) + 64,   sy = 32 (wx + wy) + 192 - 192 wz   (128 x 256 cell, wz in levels)
    depth    1 - 0.25 (wx + wy) - 0.5 wz
    texel    floor(depth * 255) in R, G and B, alpha 255
Engine rules used by the sources (Build 42.22, confirmed statically):
- every mod and the game load common/media/depthmaps/DEPTH_<tileset>.png (with tileGeometry.txt); the
  maps are merged tile by tile, an empty cell taking the first non-empty one
  (TilesetDepthTexture.mergeTileset:196-206), the merged size being the smallest one;
- an assignment (tileDepthTextureAssignments.txt, <tile> = <other tile>) only applies to a sprite
  that has no depth of its own (TileDepthTextureAssignmentManager.initSprites:74);
- a sprite pixel whose depth texel is transparent is not drawn (TileDepthTexture.load:160).
Everything outside this project is read in READ-ONLY mode.
"""
import glob
import io
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WORKSHOP = r"D:\SteamLibrary\steamapps\workshop\content\108600"
DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\ProjectZomboid"
DEFAULT_FORGE = r"E:\pz-tools\pz-sprite-forge"
OWN_MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWireCompatibility", "common", "media")
CELL_W, CELL_H, COLUMNS = 128, 256, 8
#: Footprint grid, in tile units.
STEP = 0.05
#: Share of the sprite pixels the box must cover; the rest takes a neighbour's depth.
COVERAGE = 0.995
#: Half-width range of the square footprint, in tiles: up to 1.0 so that a piece of a multi-tile
#: furniture drawn over its neighbours is still covered.
HALF_MAX = 1.0


# ---------------------------------------------------------------------------- geometry

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


class _Best:
    """Smallest box covering COVERAGE of the pixels, and failing that the box covering the most."""

    def __init__(self):
        self.box, self.volume, self.fallback, self.share = None, None, None, -1.0

    def consider(self, px, py, x0, x1, y0, y1):
        lo, hi = s_interval(px, py, x0, x1, y0, y1)
        ok = (lo <= hi) & (wz_of(hi, py) >= 0.0)
        share = ok.mean() if ok.size else 0.0
        if not share > 0:
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
    if not mask.any():
        return depth, None, 0  # an empty sprite draws nothing: no depth needed
    box = fit_box(px.astype(float), py.astype(float))
    if box is not None:
        depth[py, px] = box_depth(px.astype(float), py.astype(float), box)
    depth = fill(depth, mask)
    depth[~mask] = np.nan
    left = int((mask & np.isnan(depth)).sum())
    return depth, box, left


def encode(depth):
    """RGBA cell of a depth grid (NaN = transparent)."""
    drawn = ~np.isnan(depth)
    value = np.floor(np.clip(np.nan_to_num(depth), 0.0, 1.0) * 255.0).astype(np.uint8)
    cell = np.zeros(depth.shape + (4,), dtype=np.uint8)
    for c in range(3):
        cell[..., c] = np.where(drawn, value, 0)
    cell[..., 3] = np.where(drawn, 255, 0)
    return cell


# ---------------------------------------------------------------------------- names and cells

def split(name):
    """('tileset', index) of a sprite name, or None."""
    m = re.match(r"^(.+)_(\d+)$", name)
    return (m.group(1), int(m.group(2))) if m else None


def cell_of(image_alpha, index):
    """Alpha cell of tile `index` in a depth map (columns from the map width), or None when outside."""
    cols = image_alpha.shape[1] // CELL_W
    x, y = (index % cols) * CELL_W, (index // cols) * CELL_H
    if y + CELL_H > image_alpha.shape[0] or x + CELL_W > image_alpha.shape[1]:
        return None
    return image_alpha[y:y + CELL_H, x:x + CELL_W]


# ---------------------------------------------------------------------------- depth sources

class DepthSources:
    """Depth maps and assignments of a set of media roots (game, mods), merged like the engine."""

    def __init__(self, roots):
        self.maps, self.assign, self._alpha = {}, {}, {}
        for root in roots:
            for f in sorted(glob.glob(os.path.join(root, "depthmaps", "DEPTH_*.png"))):
                self.maps.setdefault(os.path.basename(f)[6:-4], []).append(f)
            a = os.path.join(root, "tileDepthTextureAssignments.txt")
            if os.path.isfile(a):
                with open(a, encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        m = re.match(r"\s*(\S+_\d+)\s*=\s*(\S+_\d+)\s*,?\s*$", line)
                        if m:
                            self.assign.setdefault(m.group(1), m.group(2))

    def _alpha_of(self, path):
        if path not in self._alpha:
            from PIL import Image
            self._alpha[path] = np.array(Image.open(path).convert("RGBA").getchannel("A"))
        return self._alpha[path]

    def own_cell(self, name):
        """Alpha of the first non-empty cell of `name` among the maps, or None."""
        parts = split(name)
        if not parts:
            return None
        for path in self.maps.get(parts[0], []):
            cell = cell_of(self._alpha_of(path), parts[1])
            if cell is not None and cell.any():
                return cell
        return None

    def depth_values(self, name):
        """Depth grid (0..1, NaN where transparent) of the first non-empty cell of `name`, or None."""
        from PIL import Image
        parts = split(name)
        if not parts:
            return None
        for path in self.maps.get(parts[0], []):
            cell = cell_of(self._alpha_of(path), parts[1])
            if cell is not None and cell.any():
                rgba = np.array(Image.open(path).convert("RGBA"))
                cols = rgba.shape[1] // CELL_W
                x, y = (parts[1] % cols) * CELL_W, (parts[1] // cols) * CELL_H
                block = rgba[y:y + CELL_H, x:x + CELL_W]
                return np.where(block[..., 3] > 0, block[..., 0] / 255.0, np.nan)
        return None

    def depth_cell(self, name):
        """('own' or 'assigned', alpha cell, assigned tile) the engine would use, or (None, None, None)."""
        cell = self.own_cell(name)
        if cell is not None:
            return "own", cell, None
        other = self.assign.get(name)
        cell = other and self.own_cell(other)
        if cell is not None:
            return "assigned", cell, other
        return None, None, None

    def map_size(self, tileset):
        """(width, height) of the smallest existing map of a tileset (the merged size), or None."""
        sizes = [self._alpha_of(p).shape[::-1] for p in self.maps.get(tileset, [])]
        return min(sizes, key=lambda s: s[0] * s[1]) if sizes else None


def media_roots(workshop, game, include_own):
    """Game media, every Workshop mod's common/media, and this mod's when `include_own`."""
    roots = [os.path.join(game, "media")]
    roots += sorted(glob.glob(os.path.join(workshop, "*", "mods", "*", "common", "media")))
    if include_own:
        roots.append(OWN_MEDIA)
    return roots


# ---------------------------------------------------------------------------- sprite masks

class SpriteMasks:
    """Alpha (CELL_H x CELL_W) of sprites read from texture packs (pz-sprite-forge reader)."""

    def __init__(self, forge):
        sys.path.insert(0, forge)
        self.masks, self.packs = {}, {}

    def _pack(self, path):
        """Parsed pack, kept: a later call may look for other sprites in it."""
        if path not in self.packs:
            from pzforge.packfile import TexturePack
            with open(path, "rb") as f:
                self.packs[path] = TexturePack.loads(f.read())
        return self.packs[path]

    def load(self, pack_paths, names):
        """Reads the packs in order until every name of `names` is found."""
        from PIL import Image
        wanted = set(names) - set(self.masks)
        for path in pack_paths:
            if not wanted:
                return
            for page in self._pack(path).pages:
                entries = [e for e in page.entries if e.name in wanted]
                if not entries:
                    continue
                img = Image.open(io.BytesIO(page.png)).convert("RGBA")
                for e in entries:
                    cell = Image.new("RGBA", (e.ow, e.oh), (0, 0, 0, 0))
                    cell.paste(img.crop((e.x, e.y, e.x + e.w, e.y + e.h)), (e.ox, e.oy))
                    self.masks[e.name] = np.array(cell.getchannel("A"))
                    wanted.discard(e.name)

    def get(self, name):
        return self.masks.get(name)

    def tileset_count(self, pack_paths, tileset):
        """Highest index + 1 of a tileset's sprites in the packs (names only, no decoding)."""
        top = -1
        for path in pack_paths:
            for page in self._pack(path).pages:
                for e in page.entries:
                    parts = split(e.name)
                    if parts and parts[0] == tileset:
                        top = max(top, parts[1])
        return top + 1


def packs_of(workshop, game, workshop_id):
    """Texture packs of a target mod (all its variants), then the game's tile packs."""
    paths = []
    if workshop_id:
        paths += sorted(glob.glob(os.path.join(workshop, workshop_id, "mods", "*", "*", "media", "texturepacks",
                                               "*.pack")))
    paths += [p for p in (os.path.join(game, "media", "texturepacks", "Tiles2x.pack"),) if os.path.isfile(p)]
    return paths


def missing_pixels(sprite_alpha, depth_alpha):
    """Pixels the sprite draws but the depth cell leaves transparent (not drawn by the engine)."""
    if sprite_alpha is None or depth_alpha is None:
        return None
    return int(((sprite_alpha > 0) & (depth_alpha == 0)).sum())


def profiles():
    """(name, workshop id, sprite names) of every profile."""
    import check_sprites
    return check_sprites.profiles()


def overlays():
    """(name, workshop id, {overlay sprite: base sprite}) of every profile."""
    import check_sprites
    return check_sprites.overlays()


def overlay_depth(base_depth, overlay_alpha):
    """Depth of a sprite drawn over a machine: the machine's depth, extended to the overlay's pixels
    outside the machine with the farthest neighbouring depth."""
    mask = overlay_alpha > 0
    depth = np.where(mask, base_depth, np.nan)
    depth = fill(depth, mask)
    depth[~mask] = np.nan
    return depth, int((mask & np.isnan(depth)).sum())
