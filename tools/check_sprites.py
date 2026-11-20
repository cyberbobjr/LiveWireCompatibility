"""Checks that every sprite of every profile still exists for its target mod (ADR-001, D06).

Reads the Workshop copy and the game in READ-ONLY mode: never writes there. A sprite counts as
found when a .tiles file of the target mod or of the game defines it (many mods give a use to
vanilla map tiles), or when its name appears in the target mod's Lua or script files.
Not run in CI (needs the copy and the game).
Usage: python tools/check_sprites.py [--workshop DIR] [--game DIR]
Exit code: 0 all found, 1 missing sprites, 2 target mod not found.
"""
import argparse
import glob
import os
import re
import struct
import sys

import lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = os.path.join(ROOT, "Contents", "mods")
LUA = os.path.join(MODS, "batman_LiveWireCompatibility", "42.21", "media", "lua")
PROFILE_GLOB = os.path.join(MODS, "*", "42.21", "media", "lua", "shared", "LiveWireCompatibility", "Profiles", "*.lua")
DEFAULT_WORKSHOP = r"D:\SteamLibrary\steamapps\workshop\content\108600"
DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\ProjectZomboid"


def _profile_list():
    """LiveWireCompat.Profiles.list after loading the core modules and every profile file."""
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    # Kahlua-like require: each module of this mod is loaded once from shared/ (core files need
    # each other: LWC_Profiles requires LWC_Switch, LWC_Gates and the gate kinds).
    lua.globals().SHARED_ROOT = os.path.join(LUA, "shared").replace("\\", "/")
    lua.execute(r"""
print = function() end
local loaded = {}
function require(name)
    if loaded[name] then return end
    loaded[name] = true
    local f = io.open(SHARED_ROOT .. "/" .. name .. ".lua", "r")
    if not f then return end
    local code = f:read("*a"); f:close()
    assert((loadstring or load)(code, name))()
end
require "LiveWireCompatibility/LWC_Profiles"
""")
    for path in sorted(glob.glob(PROFILE_GLOB)):
        with open(path, encoding="ascii") as f:
            lua.execute(f.read())
    return list(lua.eval("LiveWireCompat.Profiles.list").values())


def profiles():
    """(name, workshop id, sprite names of its consumers) of every profile."""
    out = []
    for p in _profile_list():
        sprites = [s for c in p.consumers.values() for s in c.sprites.values()]
        out.append((p.name, p.workshop, sprites))
    return out


def overlays():
    """(name, workshop id, {overlay sprite: base sprite}) of every profile: the optional `overlays`
    field (tools only) names the sprites the target mod draws over a machine (setOverlaySprite)."""
    out = []
    for p in _profile_list():
        table = p.overlays
        out.append((p.name, p.workshop, dict(table.items()) if table else {}))
    return out


def tile_names(path):
    """Sprite names ("<sheet>_<index>") defined by a binary .tiles file.

    Layout: "tdef", version, sheet count; per sheet: name, image (newline-terminated), four int32
    (width, height, sheet number, tile count); per tile: property count, then key and value lines.
    """
    with open(path, "rb") as f:
        data = f.read()
    names = set()
    if data[:4] != b"tdef":
        return names
    pos = 12

    def text():
        nonlocal pos
        end = data.index(b"\n", pos)
        value = data[pos:end].decode("latin-1")
        pos = end + 1
        return value

    try:
        for _ in range(struct.unpack_from("<i", data, 8)[0]):
            sheet = text()
            text()
            count = struct.unpack_from("<4i", data, pos)[3]
            pos += 16
            for index in range(count):
                props = struct.unpack_from("<i", data, pos)[0]
                pos += 4
                for _ in range(2 * props):
                    text()
                names.add("%s_%d" % (sheet, index))
    except (ValueError, struct.error):
        pass  # unexpected layout: keep the names read so far
    return names


def tiles_in(root):
    names = set()
    for path in glob.glob(os.path.join(root, "**", "*.tiles"), recursive=True):
        names |= tile_names(path)
    return names


def known_names(mod_dir):
    names = tiles_in(mod_dir)
    for ext in ("lua", "txt"):
        for path in glob.glob(os.path.join(mod_dir, "**", "*." + ext), recursive=True):
            with open(path, encoding="utf-8", errors="replace") as f:
                names.update(re.findall(r"[A-Za-z][A-Za-z0-9_]*_\d+", f.read()))
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workshop", default=DEFAULT_WORKSHOP)
    ap.add_argument("--game", default=DEFAULT_GAME)
    args = ap.parse_args()
    vanilla = tiles_in(os.path.join(args.game, "media"))
    code = 0
    extra = {name: list(table) for name, _w, table in overlays()}
    for name, workshop, sprites in profiles():
        sprites = sprites + extra.get(name, [])
        mod_dir = os.path.join(args.workshop, str(workshop))
        if not workshop or not os.path.isdir(mod_dir):
            print("%s: target mod not found (%s)" % (name, mod_dir))
            code = max(code, 2)
            continue
        known = known_names(mod_dir) | vanilla
        # A sprite named by a texture path (IsoObject.new(square, "media/textures/...png")) is found
        # when the target mod ships that file.
        def texture_found(s):
            return "/" in s and bool(glob.glob(os.path.join(mod_dir, "mods", "*", "*", s.replace("/", os.sep))))
        missing = [s for s in sprites if s not in known and not texture_found(s)]
        if missing:
            print("%s: %d sprite(s) defined nowhere (target mod or game): %s" % (name, len(missing), ", ".join(missing)))
            code = max(code, 1)
        else:
            print("%s: %d sprites found" % (name, len(sprites)))
    return code


if __name__ == "__main__":
    sys.exit(main())
