"""Offline tests of the on/off switch (ADR-002, D01-D04), embedded Lua (pip install lupa).

Doubles: LiveWire's API and world objects from test_profiles.py, plus a cell, a player and the
client command channel.
Run: python tests/test_switch.py
"""
import glob
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402

WORLD = r"""
SENT = {}
function sendClientCommand(player, module, command, args)
    SENT[#SENT + 1] = { module = module, command = command, args = args }
end
SQUARES = {}
function sq(x, y, z, ...)
    local list = { ... }
    local s = { x = x, y = y, z = z }
    function s:getX() return self.x end
    function s:getY() return self.y end
    function s:getZ() return self.z end
    function s:getObjects()
        return { size = function() return #list end, get = function(_, i) return list[i + 1] end }
    end
    for _, o in ipairs(list) do o.sq = s end
    SQUARES[x .. "," .. y .. "," .. z] = s
    return s
end
function getCell()
    return { getGridSquare = function(_, x, y, z) return SQUARES[x .. "," .. y .. "," .. z] end }
end
function player(x, y, z)
    return { getX = function() return x end, getY = function() return y end, getZ = function() return z end }
end
SWITCHED = { name = "Switched", mods = { "TargetMod" },
    consumers = {
        { id = "SwDryer", sprites = { "sw_0" }, watts = 700, switch = true },
        { id = "SwLamp", sprites = { "sw_1" }, watts = 40, running = function(o) return o.on end, idle = 3,
          switch = true },
        { id = "NativePc", sprites = { "pc_0" }, watts = 120 },
    } }
"""


def make():
    lua = tp.make()
    lua.execute(WORLD)
    lua.execute("LiveWireCompat.Profiles.add(SWITCHED); fire()")
    return lua


class Billing(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def watts(self, cid, setup):
        return self.lua.eval("(function() local m = machine('%s'); %s; return REGISTERED.%s.powerConsumption(m) end)()"
                             % (cid, setup, cid))

    def test_machine_on_by_default_draws_its_watts(self):
        self.assertEqual(self.watts("SwDryer", "local _ = 0"), 700)

    def test_switched_off_machine_draws_nothing(self):
        self.assertEqual(self.watts("SwDryer", "m:getModData().LWC_off = true"), 0)

    def test_switched_off_machine_draws_no_idle_either(self):
        self.assertEqual(self.watts("SwLamp", "m:getModData().LWC_off = true"), 0)
        self.assertEqual(self.watts("SwLamp", "m.on = false"), 3)
        self.assertEqual(self.watts("SwLamp", "m.on = true"), 40)

    def test_machine_without_our_switch_ignores_the_key(self):
        self.assertEqual(self.watts("NativePc", "m:getModData().LWC_off = true"), 120)


class Powered(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_on_with_current_is_powered(self):
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.powered(machine('SwDryer'))"))

    def test_off_is_not_powered_even_with_current(self):
        self.assertFalse(self.lua.eval(
            "(function() local m = machine('SwDryer'); m:getModData().LWC_off = true; "
            "return LiveWireCompat.Switch.powered(m) end)()"))

    def test_cut_is_not_powered(self):
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.powered(machine('SwDryer', true))"))

    def test_only_profile_switches_are_switchable(self):
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.switchable(machine('SwDryer'))"))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.switchable(machine('NativePc'))"))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.switchable(machine('Unknown'))"))

    def test_inactive_profile_gives_no_switch(self):
        lua = tp.make(active=False)
        lua.execute(WORLD)
        lua.execute("LiveWireCompat.Profiles.add(SWITCHED); fire()")
        self.assertFalse(lua.eval("LiveWireCompat.Switch.switchable(machine('SwDryer'))"))


class Command(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.execute("M = machine('SwDryer', false, 'sw_0'); sq(10, 20, 0, machine('Other'), M)")

    def handle(self, args, at="10, 21, 0"):
        return tuple(self.lua.eval("{ LiveWireCompat.Switch.handle(player(%s), %s) }" % (at, args)).values())

    def test_switch_off_then_on(self):
        self.assertEqual(self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true }"), (True,))
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))
        self.assertEqual(self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = false }"), (True,))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))
        self.assertFalse(self.lua.eval("M:hasModData()"))

    def test_server_sends_the_mod_data(self):
        self.lua.execute("SIDE = 'server'")
        self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true }")
        self.assertEqual(self.lua.eval("M.sent"), 1)

    def test_single_player_does_not_send(self):
        self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true }")
        self.assertIsNone(self.lua.eval("M.sent"))

    def test_malformed_request_is_refused(self):
        self.assertEqual(self.handle("{ x = 10, y = 20, sprite = 'sw_0' }"), (False, "bad_request"))
        self.assertEqual(self.handle("nil"), (False, "bad_request"))

    def test_wrong_sprite_or_square_is_refused(self):
        self.assertEqual(self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_9', off = true }"), (False, "no_machine"))
        self.assertEqual(self.handle("{ x = 11, y = 20, z = 0, sprite = 'sw_0', off = true }"), (False, "no_machine"))

    def test_machine_without_our_switch_is_refused(self):
        self.lua.execute("sq(12, 20, 0, machine('NativePc', false, 'pc_0'))")
        self.assertEqual(self.handle("{ x = 12, y = 20, z = 0, sprite = 'pc_0', off = true }", "12, 21, 0"),
                         (False, "no_machine"))

    def test_player_out_of_reach_is_refused(self):
        self.assertEqual(self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true }", "10, 25, 0"),
                         (False, "out_of_reach"))
        self.assertEqual(self.handle("{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true }", "10, 21, 1"),
                         (False, "out_of_reach"))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))

    def test_client_request_goes_to_the_server(self):
        self.lua.execute("SIDE = 'client'; LiveWireCompat.Switch.request(player(10, 21, 0), M, true)")
        self.assertEqual(self.lua.eval("SENT[1].module .. '/' .. SENT[1].command"), "LWC/setSwitch")
        self.assertEqual(self.lua.eval("SENT[1].args.sprite"), "sw_0")
        self.assertTrue(self.lua.eval("SENT[1].args.off"))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))

    def test_single_player_request_applies_at_once(self):
        self.lua.execute("LiveWireCompat.Switch.request(player(10, 21, 0), M, true)")
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))
        self.assertEqual(self.lua.eval("#SENT"), 0)

    def test_server_handler_applies_client_commands(self):
        self.lua.execute("SIDE = 'server'")
        self.lua.execute('require "LiveWireCompatibility/LWC_SwitchServer"')
        self.lua.execute("trigger('OnClientCommand', 'LWC', 'setSwitch', player(10, 21, 0), "
                         "{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = true })")
        self.lua.execute("trigger('OnClientCommand', 'Other', 'setSwitch', player(10, 21, 0), "
                         "{ x = 10, y = 20, z = 0, sprite = 'sw_0', off = false })")
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))


CLIENT = r"""
LOADED["TimedActions/ISBaseTimedAction"] = true
ISBaseTimedAction = {}
ISBaseTimedAction.__index = ISBaseTimedAction
function ISBaseTimedAction:derive(name) local c = setmetatable({ Type = name }, { __index = self }); c.__index = c; return c end
function ISBaseTimedAction.new(self, character) return setmetatable({ character = character }, self) end
function ISBaseTimedAction.perform(self) DONE = (DONE or 0) + 1 end
function ISBaseTimedAction.stop(self) end
QUEUE = {}
ISTimedActionQueue = { add = function(a) QUEUE[#QUEUE + 1] = a end }
luautils = { walkAdj = function() return true end }
ISWorldObjectContextMenu = { addToolTip = function() return { setName = function(self, n) self.name = n end } end }
PLAYER = player(10, 21, 0)
PLAYER.isDead = function() return false end
function getSpecificPlayer(n) return PLAYER end
function menu()
    local c = { options = {}, numOptions = 1 }
    function c:addOption(name, target, onSelect, p1, p2)
        local o = { name = name, target = target, onSelect = onSelect, param1 = p1, param2 = p2 }
        self.options[self.numOptions] = o
        self.numOptions = self.numOptions + 1
        return o
    end
    return c
end
"""


class SwitchMenu(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.execute(CLIENT)
        self.lua.execute("M = machine('SwDryer', false, 'sw_0'); N = machine('NativePc', false, 'pc_0'); "
                         "sq(10, 20, 0, M, N)")
        self.lua.execute('require "LiveWireCompatibility/LWC_SwitchMenu"')

    def fill(self):
        self.lua.execute("CTX = menu(); trigger('OnFillWorldObjectContextMenu', 0, CTX, { N }, false)")

    def test_machine_on_offers_turn_off_with_its_watts(self):
        self.fill()
        self.assertEqual(self.lua.eval("CTX.numOptions"), 2)
        self.assertEqual(self.lua.eval("CTX.options[1].name"), "ContextMenu_LWC_TurnOff")
        self.assertTrue(self.lua.eval("CTX.options[1].lwcSwitch"))
        self.assertEqual(self.lua.eval("CTX.options[1].toolTip.description"), "IGUI_LWC_RatedWatts")

    def test_machine_off_offers_turn_on(self):
        self.lua.execute("M:getModData().LWC_off = true")
        self.fill()
        self.assertEqual(self.lua.eval("CTX.options[1].name"), "ContextMenu_LWC_TurnOn")

    def test_choosing_walks_then_the_action_switches(self):
        self.fill()
        self.lua.execute("local o = CTX.options[1]; o.onSelect(o.target, o.param1, o.param2)")
        self.assertEqual(self.lua.eval("#QUEUE"), 1)
        self.lua.execute("QUEUE[1]:perform()")
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.isOff(M)"))
        self.assertEqual(self.lua.eval("DONE"), 1)

    def test_test_pass_adds_nothing(self):
        self.lua.execute("CTX = menu(); trigger('OnFillWorldObjectContextMenu', 0, CTX, { M }, true)")
        self.assertEqual(self.lua.eval("CTX.numOptions"), 1)


class Sources(unittest.TestCase):
    def test_lua_files_are_ascii(self):
        files = glob.glob(os.path.join(tp.LUA, "**", "*.lua"), recursive=True)
        self.assertTrue(files)
        for path in files:
            with open(path, "rb") as f:
                data = f.read()
            self.assertTrue(all(b < 128 for b in data), path)

    def test_no_next_call_in_mod_lua(self):
        # Kahlua has no next(): a call would fail only in game.
        for path in glob.glob(os.path.join(tp.LUA, "**", "*.lua"), recursive=True):
            with open(path, encoding="ascii") as f:
                self.assertNotRegex(f.read(), r"(?<![\w.:])next\s*\(", path)


if __name__ == "__main__":
    unittest.main()
