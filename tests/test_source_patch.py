"""Offline tests of the source patches (ADR-006): LWC_SourcePatch and the Artel drying watchdog patch."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import test_profiles as tp  # noqa: E402
import test_artel as ta  # noqa: E402

FILES = r"""
FILES = {}
READS = 0
-- getModFileReader(modId, path, create) (LuaManager.java:4925): a BufferedReader, or nil.
function getModFileReader(modId, path, create)
    local text = FILES[modId .. ":" .. path]
    if not text then return nil end
    READS = READS + 1
    local lines, i = {}, 0
    for line in (text .. "\n"):gmatch("(.-)\n") do lines[#lines + 1] = line end
    return { readLine = function() i = i + 1; return lines[i] end, close = function() end }
end
loadstring = loadstring or load
"""

TARGET = "local function check(x)\n    return x == 1\nend\nRAN = (RAN or 0) + 1\nCHECK = check\nreturn 'module'\n"


def make():
    lua = tp.make()
    lua.execute(FILES)
    lua.execute('require "LiveWireCompatibility/LWC_SourcePatch"')
    lua.execute("SP = LiveWireCompat.SourcePatch; ACTIVE.TargetMod = true")
    return lua


class SourcePatch(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.globals().TARGET = TARGET
        self.lua.execute("""FILES['TargetMod:media/lua/server/T.lua'] = TARGET
            SP.add({ mod = 'TargetMod', path = 'media/lua/server/T.lua',
                     edits = { { old = 'return x == 1', new = 'return x == 2' } } })""")

    def test_runs_the_target_file_with_the_edit_and_returns_its_result(self):
        self.assertEqual(self.lua.eval("SP.run('media/lua/server/T.lua')"), "module")
        self.assertEqual(self.lua.eval("RAN"), 1)
        self.assertTrue(self.lua.eval("CHECK(2)"))
        self.assertEqual(self.lua.eval("SP.applied['media/lua/server/T.lua']"), True)

    def test_edit_not_found_runs_the_original_unchanged_and_says_so(self):
        self.lua.execute("FILES['TargetMod:media/lua/server/T.lua'] = TARGET:gsub('x == 1', 'x >= 1')")
        self.lua.execute("SP.run('media/lua/server/T.lua')")
        self.assertTrue(self.lua.eval("CHECK(5)"))
        self.assertEqual(self.lua.eval("SP.applied['media/lua/server/T.lua']"), "edit_not_found")
        self.assertIn("original", self.lua.eval("LOG[#LOG]"))

    def test_edit_found_twice_runs_the_original(self):
        self.lua.execute("FILES['TargetMod:media/lua/server/T.lua'] = TARGET .. '-- return x == 1' .. string.char(10)")
        self.lua.execute("SP.run('media/lua/server/T.lua')")
        self.assertTrue(self.lua.eval("CHECK(1)"))
        self.assertEqual(self.lua.eval("SP.applied['media/lua/server/T.lua']"), "edit_not_found")

    def test_edit_that_does_not_compile_runs_the_original(self):
        self.lua.execute("SP.patches['media/lua/server/T.lua'].edits[1].new = 'return x =='")
        self.lua.execute("SP.run('media/lua/server/T.lua')")
        self.assertTrue(self.lua.eval("CHECK(1)"))
        self.assertEqual(self.lua.eval("SP.applied['media/lua/server/T.lua']"), "compile_error")

    def test_inactive_target_mod_runs_nothing(self):
        self.lua.execute("ACTIVE.TargetMod = nil; R = SP.run('media/lua/server/T.lua')")
        self.assertIsNone(self.lua.eval("R"))
        self.assertIsNone(self.lua.eval("RAN"))
        self.assertEqual(self.lua.eval("READS"), 0)

    def test_unreadable_target_runs_nothing_and_says_so(self):
        self.lua.execute("FILES['TargetMod:media/lua/server/T.lua'] = nil; SP.run('media/lua/server/T.lua')")
        self.assertIsNone(self.lua.eval("RAN"))
        self.assertEqual(self.lua.eval("SP.applied['media/lua/server/T.lua']"), "unreadable")

    def test_report_names_an_active_patch_that_never_ran(self):
        self.lua.execute("N0 = #LOG; SP.report(); N1 = #LOG")
        self.assertEqual(self.lua.eval("N1 - N0"), 1)
        self.assertIn("load", self.lua.eval("LOG[#LOG]"))
        self.lua.execute("SP.run('media/lua/server/T.lua'); N0 = #LOG; SP.report()")
        self.assertEqual(self.lua.eval("#LOG - N0"), 0)

    def test_bad_declarations_are_refused(self):
        self.assertFalse(self.lua.eval("SP.add({ mod = 'X', path = 'p' })"))
        self.assertFalse(self.lua.eval("SP.add({ mod = 'X', path = 'p', edits = { { old = '' , new = 'a' } } })"))


ARTEL_WATCHDOG = (
    "local function call(o, m) local f = o and o[m]; if f then return f(o) end end\n"
    "local function squarePowered(square)\n"
    "    if not square then return false end\n"
    "    if call(square, 'haveElectricity') then return true end\n"
    "    return false\n"
    "end\n"
    "WATCH = function(sq) return squarePowered(sq) end\n"
)
PATH = "media/lua/server/PMK_58z_SublimatorServer.lua"


class ArtelWatchdog(unittest.TestCase):
    def setUp(self):
        self.lua = ta.make(side="server")
        self.lua.execute(FILES)
        self.lua.globals().SRC = ARTEL_WATCHDOG
        self.lua.execute("FILES['ArtelManufactory:%s'] = SRC" % PATH)
        self.lua.execute("SP = LiveWireCompat.SourcePatch; SP.run('%s')" % PATH)

    def at(self, station):
        self.lua.execute("SQ = square(%s); SQ.haveElectricity = function() return true end" % station)
        return self.lua.eval("WATCH(SQ)")

    def test_patch_applies_to_artel_watchdog(self):
        self.assertEqual(self.lua.eval("SP.applied['%s']" % PATH), True)

    def test_switched_off_station_has_no_power_for_artel(self):
        self.assertFalse(self.at("off(station('ArtelSublimator', false, 1))"))

    def test_station_cut_by_livewire_has_no_power_for_artel(self):
        self.assertFalse(self.at("station('ArtelElectricDryer', true, 1)"))

    def test_powered_station_keeps_artel_answer(self):
        self.assertTrue(self.at("station('ArtelSublimator', false, 1)"))
        self.lua.execute("SQ.haveElectricity = function() return false end")
        self.assertFalse(self.lua.eval("WATCH(SQ)"))
        self.assertFalse(self.lua.eval("WATCH(nil)"))

    def test_square_without_a_station_keeps_artel_answer(self):
        self.assertTrue(self.at("machine('SomethingElse', true)"))

    def test_line_numbers_of_artel_are_kept(self):
        self.lua.execute("P = SP.patches['%s'].edits[1]" % PATH)
        self.assertNotIn("\n", self.lua.eval("P.new"))


if __name__ == "__main__":
    unittest.main()
