"""Checks that every profile sprite has a B42 depth (ADR-003). Local, not in CI.

Depth the engine would use, with this mod's maps included: a non-empty cell of the tileset's maps
(merged across mods), else an assignment. A sprite without any depth gets the engine's default one and no
highlight from the front: that is a failure. Opaque pixels (alpha >= 128) a depth leaves out are not drawn
by the engine; they are reported as notes only, the game's own maps leave some out too.
Reads the game, the Workshop and the packs in READ-ONLY mode (the game's tile pack is large: the
vanilla sprites take a while).

Usage: python tools/check_depth.py [--workshop DIR] [--game DIR] [--forge DIR]
Exit code: 0 every sprite has a depth; 1 a sprite without depth or missing from the packs.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import depthlib as dl  # noqa: E402


def check(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workshop", default=dl.DEFAULT_WORKSHOP)
    ap.add_argument("--game", default=dl.DEFAULT_GAME)
    ap.add_argument("--forge", default=dl.DEFAULT_FORGE)
    a = ap.parse_args(argv)
    sources = dl.DepthSources(dl.media_roots(a.workshop, a.game, include_own=True))
    masks = dl.SpriteMasks(a.forge)
    failed = 0
    extra = {name: sorted(table) for name, _w, table in dl.overlays()}
    for pname, workshop_id, sprites in dl.profiles():
        sprites = sprites + extra.get(pname, [])  # sprites drawn over a machine need a depth too
        packs = dl.packs_of(a.workshop, a.game, workshop_id)
        masks.load(packs, sprites)
        counts = {"own": 0, "assigned": 0}
        issues, notes = [], []
        for name in sprites:
            kind, cell, other = sources.depth_cell(name)
            if kind is None:
                issues.append("%s: no depth" % name)
                continue
            alpha = masks.get(name)
            if alpha is None:
                issues.append("%s: sprite not found in the packs" % name)
                continue
            counts[kind] += 1
            miss = dl.missing_pixels(alpha >= 128, cell)
            if miss:
                notes.append("%s: %s depth%s leaves %d opaque px out" % (
                    name, kind, (" (" + other + ")") if other else "", miss))
        failed += len(issues)
        print("%s: %d sprites, own depth %d, assigned %d, without depth %d, notes %d" % (
            pname, len(sprites), counts["own"], counts["assigned"], len(issues), len(notes)))
        for line in issues:
            print("   FAIL " + line)
        for line in notes:
            print("   note " + line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(check())
