"""Offline tests of the profile files under Profiles/ (ADR-001, D06), embedded Lua 5.1 (pip install lupa).

Every profile file is loaded with the registry: it must be accepted, its sprites must not
overlap another profile, and each gate must name one of its own consumers. Each target mod's
profile is checked against doubles of that mod in its own test file (test_artel.py, ...).
Run: python tests/test_profile_files.py
"""
import glob
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402


def load_all(lua):
    lua.execute("require = function() end")
    names = []
    for path in sorted(glob.glob(tp.PROFILE_GLOB)):
        before = lua.eval("#LiveWireCompat.Profiles.list")
        with open(path, encoding="ascii") as f:
            lua.execute(f.read())
        names.append((os.path.basename(path), lua.eval("#LiveWireCompat.Profiles.list") - before))
    return names


class AllProfiles(unittest.TestCase):
    def setUp(self):
        self.lua = tp.make(active=False)
        self.names = load_all(self.lua)

    def test_each_file_adds_exactly_one_profile(self):
        self.assertTrue(self.names)
        for name, added in self.names:
            self.assertEqual(added, 1, name)

    def test_sprites_and_ids_are_unique(self):
        sprites = self.lua.eval("""(function()
            local seen, dup = {}, {}
            for _, p in ipairs(LiveWireCompat.Profiles.list) do
                for _, c in ipairs(p.consumers) do
                    for _, s in ipairs(c.sprites) do
                        if seen[s] then dup[#dup + 1] = s end
                        seen[s] = true
                    end
                    if seen['#' .. c.id] then dup[#dup + 1] = c.id end
                    seen['#' .. c.id] = true
                end
            end
            return table.concat(dup, ',') end)()""")
        self.assertEqual(sprites, "")

    def test_gates_name_their_own_consumers(self):
        bad = self.lua.eval("""(function()
            local bad = {}
            for _, p in ipairs(LiveWireCompat.Profiles.list) do
                local ids = {}
                for _, c in ipairs(p.consumers) do ids[c.id] = true end
                for _, g in ipairs(p.gates or {}) do
                    local named = type(g.consumer) == 'table' and g.consumer or { g.consumer }
                    for _, id in ipairs(named) do
                        if not ids[id] then bad[#bad + 1] = p.name .. ':' .. g.path .. ':' .. id end
                    end
                end
            end
            return table.concat(bad, ',') end)()""")
        self.assertEqual(bad, "")


if __name__ == "__main__":
    unittest.main()
