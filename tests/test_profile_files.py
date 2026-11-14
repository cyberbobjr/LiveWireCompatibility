"""Offline tests of the profile files under Profiles/ (ADR-001, D06), embedded Lua 5.1 (pip install lupa).

Every profile file is loaded with the registry: it must be accepted, its sprites must not
overlap another profile, and each gate must name one of its own consumers. The Artel profile
is then checked against a double of the Artel tables it reads (PMK.Trade, PMK.QBase, PMK.Well).
Run: python tests/test_profile_files.py
"""
import glob
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402


ARTEL = r"""
GRID = true
PMK = {
    Well = { isPowered = function(obj) return GRID end },
    Trade = { gridPowered = function(obj) return GRID end },
    QBase = { squarePowered = function(sq) return GRID end },
}
function PMK.Trade.powerSource(obj)
    if PMK.Trade.gridPowered(obj) then return "grid" end
    if obj.battery then return "batt" end
    return "none"
end
function PMK.QBase.hasPower(obj) return PMK.QBase.squarePowered(obj.sq) end
"""


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


class Artel(unittest.TestCase):
    def setUp(self):
        self.lua = tp.make(active=False)
        self.lua.execute(ARTEL + "ACTIVE.ArtelManufactory = true")
        load_all(self.lua)
        self.lua.execute("fire()")

    def watts(self, cid, obj):
        return self.lua.eval("REGISTERED.%s.powerConsumption(%s)" % (cid, obj))

    def test_all_consumers_registered(self):
        for cid in ("ArtelWellMotor", "ArtelElectricDryer", "ArtelSublimator", "ArtelChemTable",
                    "ArtelTradePost", "ArtelQuantumBase"):
            self.assertIsNotNone(self.lua.eval("REGISTERED.%s" % cid), cid)

    def test_trade_post_draws_only_on_grid(self):
        self.assertEqual(self.watts("ArtelTradePost", "{}"), 75)
        self.lua.execute("GRID = false")
        self.assertEqual(self.watts("ArtelTradePost", "{ battery = true }"), 0)

    def test_quantum_base_lit_sprites_only(self):
        sprites = list(self.lua.eval("REGISTERED.ArtelQuantumBase.sprites").values())
        self.assertIn("Artel_116", sprites)
        self.assertNotIn("Artel_117", sprites)
        self.assertEqual(len(sprites), 16)

    def test_cut_circuit_stops_the_gated_machines(self):
        self.assertEqual(self.lua.eval("PMK.Well.isPowered(machine('ArtelWellMotor', true))"), False)
        self.assertEqual(self.lua.eval("PMK.Trade.gridPowered(machine('ArtelTradePost', true))"), False)
        self.assertEqual(self.lua.eval(
            "PMK.QBase.hasPower({ sq = square(machine('ArtelQuantumBase', true)) })"), False)

    def test_trade_post_battery_survives_a_cut(self):
        self.assertEqual(self.lua.eval(
            "PMK.Trade.powerSource((function() local m = machine('ArtelTradePost', true); m.battery = true; return m end)())"),
            "batt")

    def test_other_well_stages_keep_artel_answer(self):
        self.assertEqual(self.lua.eval("PMK.Well.isPowered({ cut = true })"), True)


if __name__ == "__main__":
    unittest.main()
