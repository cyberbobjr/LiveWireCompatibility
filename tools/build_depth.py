"""Builds this mod's B42 depth maps for the profile sprites that lack one (ADR-003). Local, not in CI.

A sprite is filled when, in the game and the Workshop mods (this mod excluded), it has no depth at all:
no non-empty cell in any map and no assignment to a tile that has one. Without depth the engine uses its
default one and does not draw the sprite's highlight from the front. Sprites a target mod draws over one of its machines (the profile's overlays) get the depth of that
machine. A sprite that has a depth, even one
leaving a few pixels out (the game's own maps do too), keeps it: the box of this tool is cruder than a
depth drawn for the sprite. check_depth.py reports those pixels.
One map per tileset in common/media/depthmaps/DEPTH_<tileset>.png, same size as the tileset's existing
map when there is one (the merged size is the smallest), only the filled cells non-empty. Maps of
this mod that no longer get a cell are removed.

Usage: python tools/build_depth.py [--workshop DIR] [--game DIR] [--forge DIR]
Exit code: 0 written, every filled sprite pixel with a depth; 1 a sprite not found or a pixel left
without depth.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import depthlib as dl  # noqa: E402


def plan(sources, masks, workshop, game):
    """{tileset: {index: (sprite name, base sprite or None)}} of the sprites without any depth, and
    the mod packs of each tileset. A base is set for an overlay (the profile's `overlays`): it takes
    the depth of the machine it covers."""
    todo, mod_packs = {}, {}
    over = {name: table for name, _w, table in dl.overlays()}
    for pname, workshop_id, sprites in dl.profiles():
        packs = dl.packs_of(workshop, game, workshop_id)
        wanted = [(name, None) for name in sprites]
        wanted += [(name, base) for name, base in sorted(over.get(pname, {}).items())]
        # A sprite named by a texture path (no tileset cell) has no depth map: the engine uses its
        # default depth for it.
        candidates = [(name, base) for name, base in wanted
                      if dl.split(name) and sources.depth_cell(name)[0] is None]
        masks.load(packs, [name for name, _b in candidates])
        for name, base in candidates:
            tileset, index = dl.split(name)
            todo.setdefault(tileset, {})[index] = (name, base)
            mod_packs.setdefault(tileset, [p for p in packs if not p.endswith("Tiles2x.pack")])
    return todo, mod_packs


def depths(todo, sources, masks):
    """{sprite name: (depth grid, report line, pixels left without depth)}: machines first, then the
    overlays, which take the depth of their machine (computed here, or read from an existing map)."""
    out = {}
    cells = [cell for per_set in todo.values() for cell in per_set.values()]
    for name, base in [c for c in cells if c[1] is None] + [c for c in cells if c[1] is not None]:
        alpha = masks.get(name)
        if alpha is None:
            out[name] = (None, "%s: sprite not found in the packs" % name, 1)
            continue
        if base is None:
            depth, box, left = dl.tile_depth(alpha)
            line = "%s: %d px, box %s, without depth %d" % (
                name, int((~np.isnan(depth)).sum()),
                "none" if box is None else "x %.2f-%.2f y %.2f-%.2f h %.2f" % box, left)
        else:
            base_depth = out[base][0] if base in out else sources.depth_values(base)
            if base_depth is None:
                out[name] = (None, "%s: its machine %s has no depth" % (name, base), 1)
                continue
            depth, left = dl.overlay_depth(base_depth, alpha)
            line = "%s: overlay of %s, %d px, without depth %d" % (name, base, int((~np.isnan(depth)).sum()), left)
        out[name] = (depth, line, left)
    return out


def build(argv=None):
    from PIL import Image
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workshop", default=dl.DEFAULT_WORKSHOP)
    ap.add_argument("--game", default=dl.DEFAULT_GAME)
    ap.add_argument("--forge", default=dl.DEFAULT_FORGE)
    a = ap.parse_args(argv)
    sources = dl.DepthSources(dl.media_roots(a.workshop, a.game, include_own=False))
    masks = dl.SpriteMasks(a.forge)
    todo, mod_packs = plan(sources, masks, a.workshop, a.game)
    computed = depths(todo, sources, masks)
    bad = 0
    out_dir = os.path.join(dl.OWN_MEDIA, "depthmaps")
    os.makedirs(out_dir, exist_ok=True)
    written = set()
    for tileset in sorted(todo):
        cells = todo[tileset]
        size = sources.map_size(tileset)
        if size is None:
            count = max(masks.tileset_count(mod_packs[tileset], tileset), max(cells) + 1)
            size = (dl.CELL_W * dl.COLUMNS, dl.CELL_H * int(math.ceil(count / float(dl.COLUMNS))))
        sheet = np.zeros((size[1], size[0], 4), dtype=np.uint8)
        cols = size[0] // dl.CELL_W
        for index in sorted(cells):
            name = cells[index][0]
            depth, line, left = computed[name]
            print(line)
            bad += left
            if depth is None:
                continue
            ox, oy = (index % cols) * dl.CELL_W, (index // cols) * dl.CELL_H
            if oy + dl.CELL_H > size[1]:
                print("%s: outside the %dx%d map of its tileset" % (name, size[0], size[1]))
                bad += 1
                continue
            sheet[oy:oy + dl.CELL_H, ox:ox + dl.CELL_W] = dl.encode(depth)
        path = os.path.join(out_dir, "DEPTH_%s.png" % tileset)
        Image.fromarray(sheet, "RGBA").save(path)
        written.add(os.path.normcase(path))
        print("wrote %s (%dx%d), %d sprites" % (path, size[0], size[1], len(cells)))
    for path in glob.glob(os.path.join(out_dir, "DEPTH_*.png")):
        if os.path.normcase(path) not in written:
            os.remove(path)
            print("removed %s (no sprite to fill any more)" % path)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(build())
