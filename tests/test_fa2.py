"""Offline tests of the Functional Appliances 2 profile (ADR-002, D06), embedded Lua 5.1 (pip install lupa).

Doubles keep the shape of FA 2 42.20 (client/*.lua, shared/TimedActions/*.lua):
- FA.updateMachineTemp(Machine): mode from ModData.CustomTemp, container temperature, transmit on
  change, returns the machine (client/FAMapObjects.lua:102-129);
- FAxxx.onUseXxx(junk, player, machine, ...) functions of global tables (client/*Menu.lua);
- UseXxx timed action classes derived like ISBaseTimedAction, machine in the `machine` field.
Run: python tests/test_fa2.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

FA2 = r"""
SIDE = "client"
HALO = {}
function hero() return { setHaloNote = function(self, text) HALO[#HALO + 1] = text end } end
-- Placed FA 2 machine: a LiveWire consumer with a container whose temperature FA 2 sets.
function famachine(id, cut, temp)
    local m = machine(id, cut)
    if temp then m:getModData().CustomTemp = temp end
    m.temp = 1
    m.squareSent = 0
    m.getContainer = function(self)
        return { getCustomTemperature = function() return self.temp end,
                 setCustomTemperature = function(_, t) self.temp = t end,
                 requestSync = function() end }
    end
    m.getSquare = function(self)
        return { transmitModdata = function() self.squareSent = self.squareSent + 1 end,
                 haveElectricity = function() return true end }
    end
    return m
end
FA = {}
local TEMPS = { Warm = 1.5, Hot = 1.61, Cold = 0.1 }
FA.updateMachineTemp = function(Machine)
    local preTemp = Machine:getContainer():getCustomTemperature()
    Machine:getModData()['Loaded'] = true
    local t = TEMPS[Machine:getModData()['CustomTemp']]
    if t then
        Machine:getContainer():setCustomTemperature(t)
    else
        Machine:getContainer():setCustomTemperature(1)
        Machine:getModData()['CustomTemp'] = "Off"
    end
    if preTemp ~= Machine:getContainer():getCustomTemperature() then
        Machine:getSquare():transmitModdata()
        Machine:transmitModData()
        Machine:getContainer():requestSync()
    end
    return Machine
end
USED = {}
local function modeSetter(name)
    return function(junk, player, m, tempSetting)
        USED[#USED + 1] = name .. ":" .. tostring(tempSetting)
        m:getModData()['CustomTemp'] = tempSetting
    end
end
FAHeatedCounter = { onUseHeatedCounter = modeSetter("heated") }
FADisplayCounter = { onUseDisplayCounter = modeSetter("display") }
FAVendingMachine = { onUseVendingMachine = modeSetter("vending") }
local function user(name)
    return function(junk, player, m, ...) USED[#USED + 1] = name end
end
FAHotDogMachine = { onUseHotDogMachine = user("hotdog") }
FAPopcornMachine = { onUsePopcornMachine = user("popcorn") }
FASodaFountain = { onUseSodaFountain = user("soda") }
FABarTaps = { onUseBarTaps = user("bartaps") }
-- ISBaseTimedAction double: methods on the class, instances through a metatable.
ISBaseTimedAction = {}
ISBaseTimedAction.__index = ISBaseTimedAction
function ISBaseTimedAction:isValidStart() return true end
function ISBaseTimedAction:derive(type)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.Type = type
    return o
end
local function action(name)
    local c = ISBaseTimedAction:derive(name)
    function c:isValid() return true end
    function c:new(character, machine, ...)
        local o = {}
        setmetatable(o, self)
        self.__index = self
        o.character = character
        o.machine = machine
        return o
    end
    return c
end
UseHotDogMachine = action("UseHotDogMachine")
UsePopcornMachine = action("UsePopcornMachine")
UseSodaFountain = action("UseSodaFountain")
UseBarTaps = action("UseBarTaps")
ACTIVE.FunctionalAppliances2 = true
"""


def make(side="client"):
    lua = tp.make(active=False)
    lua.execute(FA2)
    lua.execute('SIDE = "%s"' % side)
    tpf.load_all(lua)
    lua.execute("fire()")
    return lua


MENU = r"""
ISWorldObjectContextMenu = { addToolTip = function() return { setName = function(self, n) self.name = n end } end }
function menu()
    local c = { options = {}, numOptions = 1 }
    function c:addOption(name, target, onSelect, p1, p2, p3)
        local o = { name = name, target = target, onSelect = onSelect, param1 = p1, param2 = p2, param3 = p3 }
        self.options[self.numOptions] = o
        self.numOptions = self.numOptions + 1
        return o
    end
    function c:getSubMenu() return nil end
    return c
end
"""


class Menus(unittest.TestCase):
    """FA 2 menu options carry the machine as param2 (HotDogMachineMenu.lua:14-19)."""

    def fill(self, setup):
        lua = make()
        lua.execute(MENU)
        lua.execute("CTX = menu(); %s; trigger('OnFillWorldObjectContextMenu', 0, CTX, {}, false)" % setup)
        return lua

    def test_switched_off_hot_dog_options_are_greyed(self):
        lua = self.fill("local m = machine('FA2HotDogMachine'); m:getModData().LWC_off = true; "
                        "OPT = CTX:addOption('Make hot dog', nil, print, {}, m, 'snd')")
        self.assertTrue(lua.eval("OPT.notAvailable"))

    def test_mode_machine_options_stay_available_without_power(self):
        lua = self.fill("OPT = CTX:addOption('Off', nil, print, {}, machine('FA2HeatedCounter', true), 'Off')")
        self.assertIsNone(lua.eval("OPT.notAvailable"))


class NativeModeMachines(unittest.TestCase):
    """Heated counter, display counters, vending machines: FA 2's own Off mode is the switch."""

    def setUp(self):
        self.lua = make()

    def test_no_switch_of_ours(self):
        for cid in ("FA2HeatedCounter", "FA2DisplayCounter", "FA2VendingMachine"):
            self.assertFalse(self.lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)

    def test_update_turns_a_cut_machine_off_as_fa2_does(self):
        self.lua.execute("M = famachine('FA2HeatedCounter', true, 'Hot'); M.temp = 1.61; R = FA.updateMachineTemp(M)")
        self.assertEqual(self.lua.eval("M:getModData().CustomTemp"), "Off")
        self.assertEqual(self.lua.eval("M.temp"), 1)
        self.assertEqual(self.lua.eval("M.sent"), 1)
        self.assertEqual(self.lua.eval("M.squareSent"), 1)
        self.assertTrue(self.lua.eval("R == M"))

    def test_update_keeps_the_mode_of_a_powered_machine(self):
        self.lua.execute("M = famachine('FA2VendingMachine', false, 'Cold'); R = FA.updateMachineTemp(M)")
        self.assertEqual(self.lua.eval("M:getModData().CustomTemp"), "Cold")
        self.assertEqual(self.lua.eval("M.temp"), 0.1)
        self.assertTrue(self.lua.eval("R == M"))

    def test_update_of_other_objects_is_untouched(self):
        self.lua.execute("M = famachine('Other', true, 'Warm'); FA.updateMachineTemp(M)")
        self.assertEqual(self.lua.eval("M:getModData().CustomTemp"), "Warm")

    def test_cut_machine_refuses_a_mode_and_tells_the_player(self):
        for fn, cid in (("FAHeatedCounter.onUseHeatedCounter", "FA2HeatedCounter"),
                        ("FADisplayCounter.onUseDisplayCounter", "FA2DisplayCounter"),
                        ("FAVendingMachine.onUseVendingMachine", "FA2VendingMachine")):
            self.lua.execute("USED = {}; HALO = {}; M = famachine('%s', true, 'Off'); %s(nil, hero(), M, 'Warm')"
                             % (cid, fn))
            self.assertEqual(self.lua.eval("#USED"), 0, fn)
            self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_NoPower", fn)

    def test_cut_machine_can_still_be_set_off(self):
        self.lua.execute("USED = {}; M = famachine('FA2DisplayCounter', true, 'Cold');"
                         "FADisplayCounter.onUseDisplayCounter(nil, hero(), M, 'Off')")
        self.assertEqual(self.lua.eval("USED[1]"), "display:Off")

    def test_powered_machine_changes_mode(self):
        self.lua.execute("USED = {}; M = famachine('FA2HeatedCounter', false, 'Off');"
                         "FAHeatedCounter.onUseHeatedCounter(nil, hero(), M, 'Hot')")
        self.assertEqual(self.lua.eval("USED[1]"), "heated:Hot")


class SwitchedMachines(unittest.TestCase):
    """Hot dog, popcorn, soda fountain, SlurpNBurp, bar taps: our switch, use and action gated."""

    CASES = (
        ("FA2HotDogMachine", "FAHotDogMachine.onUseHotDogMachine", "UseHotDogMachine", "hotdog"),
        ("FA2PopcornMachine", "FAPopcornMachine.onUsePopcornMachine", "UsePopcornMachine", "popcorn"),
        ("FA2SodaFountain", "FASodaFountain.onUseSodaFountain", "UseSodaFountain", "soda"),
        ("FA2SlurpNBurp", "FASodaFountain.onUseSodaFountain", "UseSodaFountain", "soda"),
        ("FA2BarTap", "FABarTaps.onUseBarTaps", "UseBarTaps", "bartaps"),
    )

    def setUp(self):
        self.lua = make()

    def test_each_gets_our_switch_and_draws_nothing_off(self):
        for cid, _, _, _ in self.CASES:
            self.assertTrue(self.lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)
            self.lua.execute("M = famachine('%s', false); M:getModData().LWC_off = true" % cid)
            self.assertEqual(self.lua.eval("REGISTERED.%s.powerConsumption(M)" % cid), 0, cid)

    def test_switched_off_machine_refuses_the_use(self):
        for cid, fn, _, name in self.CASES:
            self.lua.execute("USED = {}; HALO = {}; M = famachine('%s', false); M:getModData().LWC_off = true;"
                             "%s(nil, hero(), M, 'sound')" % (cid, fn))
            self.assertEqual(self.lua.eval("#USED"), 0, cid)
            self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff", cid)

    def test_powered_machine_is_used(self):
        for cid, fn, _, name in self.CASES:
            self.lua.execute("USED = {}; %s(nil, hero(), famachine('%s', false), 'sound')" % (fn, cid))
            self.assertEqual(self.lua.eval("USED[1]"), name, cid)

    def test_cut_machine_stops_the_action(self):
        for cid, _, action, _ in self.CASES:
            self.lua.execute("A = %s:new(hero(), famachine('%s', true), 'sound')" % (action, cid))
            self.assertEqual(self.lua.eval("A:isValid()"), False, cid)
            self.assertEqual(self.lua.eval("A:isValidStart()"), False, cid)
            self.lua.execute("A = %s:new(hero(), famachine('%s', false), 'sound')" % (action, cid))
            self.assertEqual(self.lua.eval("A:isValid()"), True, cid)


class Sides(unittest.TestCase):
    def test_dedicated_server_installs_no_fa2_gate(self):
        lua = make(side="server")
        self.assertEqual(lua.eval("#LOG"), 0)
        lua.execute("USED = {}; M = famachine('FA2HotDogMachine', true); FAHotDogMachine.onUseHotDogMachine(nil, hero(), M)")
        self.assertEqual(lua.eval("USED[1]"), "hotdog")


class ExhaustHood(unittest.TestCase):
    def test_has_no_switch(self):
        lua = make()
        self.assertFalse(lua.eval("LiveWireCompat.Switch.ids.FA2ExhaustHood == true"))


if __name__ == "__main__":
    unittest.main()
