"""Offline tests of the Machinery, Plysken Weather Station, Computer Mod and True Moozic profiles
(ADR-002, D06), embedded Lua 5.1 (pip install lupa).

Doubles keep the shape of the target code (read-only Workshop copies):
- Machinery 42: Machinery.Service.isPowered(object) (shared/Machinery/Service.lua:128-134), read
  again at every call by Service.getOperationStatus through `local Service = Machinery.Service`
  (Service.lua:69-70, :981);
- PWS 42.1: PWS.Power.isPowered(obj) (shared/PWS/PWSPower.lua:29-64), called as PWS.Power.isPowered
  by the station read and the server log (PWSStation.lua:74, server/PWS/PWSLog.lua:89);
- Computer Mod 42: ComputerModPower.hasComputerPower(computer) (client/ComputerMod_Power.lua:144-156),
  reached through a local helper that reads the global at each call (ComputerMod_UI.lua:690-691),
  the per-tick screen update shutting the computer down (ComputerMod_UI_Lifecycle.lua:245-256);
- True Moozic 42: TMJukebox.hasPower(square) (shared/TMJukeboxDefs.lua:398-407) and the per-jukebox
  tick that stops playback when it answers false (client/TMJukeboxTick.lua:163-176).
Run: python tests/test_small_profiles.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

TARGETS = r"""
ELEC = true
-- LiveWire id of the Machinery consumers on tiles shared with Knox Working Machines (ADR-005, D02).
LW_ID = { MachineryDrillPress = "VanillaDrillPress", MachineryHydraulicPress = "VanillaIndustry03Mill",
          MachineryLathe = "VanillaLathe", MachineryBenchGrinder = "VanillaBenchGrinder" }
-- Placed machine on a square whose engine power is ELEC; LiveWire knows it by its LiveWire id.
function placed(id, cut, off)
    local m = machine(LW_ID[id] or id, cut)
    if off then m:getModData().LWC_off = true end
    m.sq = square(m)
    m.sq.haveElectricity = function(self) return ELEC end
    return m
end

-- Machinery (shared/Machinery/Service.lua).
Machinery = Machinery or {}
Machinery.Service = Machinery.Service or {}
local Service = Machinery.Service
function Service.isPowered(object)
    if not object then return false end
    local square = object:getSquare()
    if not square then return false end
    if square:haveElectricity() then return true end
    return false
end
function Service.getOperationStatus(player, object)
    if not Service.isPowered(object) then return false, "IGUI_Machinery_Error_NoPower" end
    return true
end

-- Plysken Weather Station (shared/PWS/PWSPower.lua, shared/PWS/PWSStation.lua).
PWS = PWS or {}
PWS.Power = {}
local P = PWS.Power
function P.isPowered(obj)
    if not obj then return false end
    local sq = obj:getSquare()
    return sq ~= nil and sq:haveElectricity() == true
end
PWS.Station = { read = function(obj)
    local powered = PWS.Power and PWS.Power.isPowered(obj) or false
    return { powered = powered }
end }

-- Computer Mod (client/ComputerMod_Power.lua, client/ComputerMod_UI.lua, ComputerMod_UI_Lifecycle.lua).
ComputerModPower = ComputerModPower or {}
function ComputerModPower.hasComputerPower(computer)
    local sq = computer and computer:getSquare()
    return sq ~= nil and sq:haveElectricity() == true
end
local function hasComputerPower(computer)
    return ComputerModPower and ComputerModPower.hasComputerPower and ComputerModPower.hasComputerPower(computer) or false
end
function screenUpdate(computer)
    if not hasComputerPower(computer) then
        computer:getModData().ComputerModPowerOn = false
        return "Power is out."
    end
    return "on"
end

-- True Moozic (shared/TMJukeboxDefs.lua, client/TMJukeboxTick.lua).
TMJukebox = TMJukebox or {}
function TMJukebox.hasPower(square)
    if not square then return false end
    if square:haveElectricity() then return true end
    return false
end
function TMJukebox.transmit(obj) obj:transmitModData() end
function manageJukebox(obj)
    local d = obj:getModData().tmJukebox
    if not d or not d.isPlaying then return "stopped" end
    if not TMJukebox.hasPower(obj:getSquare()) then
        d.isPlaying = false
        TMJukebox.transmit(obj)
        return "stopped"
    end
    return "playing"
end
function jukebox(cut, playing)
    local m = placed("TMJukebox", cut)
    m:getModData().tmJukebox = { isPlaying = playing }
    return m
end

ACTIVE.Machinery = true
ACTIVE.PWS = true
ACTIVE.ComputerModkum = true
ACTIVE.TrueMoozic = true
"""

MACHINERY = ("MachineryDrillPress", "MachineryMetalBandsaw", "MachineryHydraulicPress", "MachineryLathe",
             "MachineryBenchGrinder", "MachineryTableSawIndustrial", "MachineryTableSawContractor",
             "MachineryConcreteMixer")


def make(side="sp"):
    lua = tp.make(active=False)
    lua.execute(TARGETS)
    lua.execute('SIDE = "%s"' % side)
    tpf.load_all(lua)
    lua.execute("fire()")
    return lua


class Switched(unittest.TestCase):
    """Machinery and PWS have no switch of their own: they get ours (D01)."""

    def setUp(self):
        self.lua = make()

    def test_each_gets_our_switch_and_draws_nothing_off(self):
        for cid in MACHINERY + ("PWSStation",):
            self.assertTrue(self.lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)
            lw = "(LW_ID.%s or '%s')" % (cid, cid)
            self.assertEqual(self.lua.eval("REGISTERED[%s].powerConsumption(placed('%s', false, true))"
                                           % (lw, cid)), 0, cid)
            self.assertGreater(self.lua.eval("REGISTERED[%s].powerConsumption(placed('%s', false))"
                                             % (lw, cid)), 0, cid)


class MachineryGate(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def status(self, code):
        return self.lua.eval("(Machinery.Service.getOperationStatus(nil, %s))" % code)

    def test_switched_off_or_cut_machine_refuses_every_operation(self):
        for cid in MACHINERY:
            self.assertEqual(self.status("placed('%s', false, true)" % cid), False, cid)
            self.assertEqual(self.status("placed('%s', true)" % cid), False, cid)

    def test_powered_machine_works(self):
        for cid in MACHINERY:
            self.assertEqual(self.status("placed('%s', false)" % cid), True, cid)

    def test_no_engine_power_stays_no_power(self):
        self.lua.execute("ELEC = false")
        self.assertEqual(self.status("placed('MachineryLathe', false)"), False)

    def test_gate_is_shared(self):
        lua = make("server")
        self.assertEqual(lua.eval("(Machinery.Service.isPowered(placed('MachineryDrillPress', true)))"), False)
        lua = make("client")
        self.assertEqual(lua.eval("(Machinery.Service.isPowered(placed('MachineryDrillPress', true)))"), False)


class PWSGate(unittest.TestCase):
    def test_station_off_or_cut_reads_nothing_on_both_sides(self):
        for side in ("server", "client"):
            lua = make(side)
            self.assertEqual(lua.eval("PWS.Station.read(placed('PWSStation', false, true)).powered"), False, side)
            self.assertEqual(lua.eval("PWS.Station.read(placed('PWSStation', true)).powered"), False, side)
            self.assertEqual(lua.eval("PWS.Station.read(placed('PWSStation', false)).powered"), True, side)


class ComputerMod(unittest.TestCase):
    """Native power button (ModData ComputerModPowerOn): no switch of ours, client gate."""

    def setUp(self):
        self.lua = make("client")

    def test_no_switch_of_ours(self):
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.ids.ComputerModDesktop == true"))

    def test_bill_follows_the_power_button(self):
        self.lua.execute("C = placed('ComputerModDesktop', false)")
        self.assertEqual(self.lua.eval("REGISTERED.VanillaDesktop.powerConsumption(C)"), 0)
        self.lua.execute("C:getModData().ComputerModPowerOn = true")
        self.assertEqual(self.lua.eval("REGISTERED.VanillaDesktop.powerConsumption(C)"), 120)

    def test_cut_computer_shuts_down_at_the_next_screen_update(self):
        self.lua.execute("C = placed('ComputerModDesktop', true); C:getModData().ComputerModPowerOn = true")
        self.assertEqual(self.lua.eval("screenUpdate(C)"), "Power is out.")
        self.assertEqual(self.lua.eval("C:getModData().ComputerModPowerOn"), False)

    def test_powered_computer_stays_on(self):
        self.lua.execute("C = placed('ComputerModDesktop', false); C:getModData().ComputerModPowerOn = true")
        self.assertEqual(self.lua.eval("screenUpdate(C)"), "on")

    def test_dedicated_server_keeps_the_original(self):
        lua = make("server")
        self.assertEqual(lua.eval("ComputerModPower.hasComputerPower(placed('ComputerModDesktop', true))"), True)


class TrueMoozic(unittest.TestCase):
    """Native play/stop (md.tmJukebox.isPlaying): no switch of ours, client square gate."""

    def setUp(self):
        self.lua = make("client")

    def test_vanilla_jukebox_sprites(self):
        sprites = sorted(self.lua.eval("REGISTERED.TMJukebox.sprites").values())
        self.assertEqual(sprites, ["recreational_01_0", "recreational_01_1"])

    def test_no_switch_of_ours(self):
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.ids.TMJukebox == true"))

    def test_bill_follows_playback(self):
        self.assertEqual(self.lua.eval("REGISTERED.TMJukebox.powerConsumption(jukebox(false, true))"), 150)
        self.assertEqual(self.lua.eval("REGISTERED.TMJukebox.powerConsumption(jukebox(false, false))"), 0)

    def test_cut_jukebox_stops_playing_and_syncs(self):
        self.lua.execute("J = jukebox(true, true)")
        self.assertEqual(self.lua.eval("manageJukebox(J)"), "stopped")
        self.assertEqual(self.lua.eval("J:getModData().tmJukebox.isPlaying"), False)
        self.assertEqual(self.lua.eval("J.sent"), 1)

    def test_powered_jukebox_keeps_playing(self):
        self.assertEqual(self.lua.eval("manageJukebox(jukebox(false, true))"), "playing")

    def test_dedicated_server_keeps_the_original(self):
        lua = make("server")
        self.assertEqual(lua.eval("TMJukebox.hasPower(jukebox(true, true):getSquare())"), True)


if __name__ == "__main__":
    unittest.main()
