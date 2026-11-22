"""Offline tests of the gate kinds action, call, menu, custom and of the gate sides (ADR-002, D05).

The "object" and "square" kinds are covered by test_profiles.py. Doubles: a timed action class
built like ISBaseTimedAction (methods on the class, instances through a metatable), a context
menu with the fields of ISContextMenu (options[1..numOptions-1], subOption, getSubMenu).
Run: python tests/test_gates.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402

TARGET = r"""
-- Base class with inherited methods, as ISBaseTimedAction.
Base = {}
Base.__index = Base
function Base:isValidStart() return true end
function Base:isValid() end
function Base.derive(name)
    local c = setmetatable({ Type = name }, { __index = Base })
    c.__index = c
    return c
end
UseMachine = Base.derive("UseMachine")
function UseMachine:isValid() return true end
function UseMachine:new(character, m) return setmetatable({ character = character, machine = m }, self) end
HALO = {}
function hero() return { setHaloNote = function(self, text) HALO[#HALO + 1] = text end } end
CALLS = 0
Target = {
    onUse = function(player, m, mode) CALLS = CALLS + 1; return "used" end,
}
-- Context menu double.
function menu()
    local c = { options = {}, numOptions = 1, subs = {} }
    function c:addOption(name, target, onSelect, p1, p2)
        local o = { name = name, target = target, onSelect = onSelect, param1 = p1, param2 = p2 }
        self.options[self.numOptions] = o
        self.numOptions = self.numOptions + 1
        return o
    end
    function c:getSubMenu(n) return self.subs[n] end
    return c
end
ISWorldObjectContextMenu = { addToolTip = function()
    return { setName = function(self, n) self.name = n end }
end }
GATES = { name = "Gated", mods = { "TargetMod" },
    consumers = {
        { id = "GMachine", sprites = { "g_0" }, watts = 100, switch = true },
        { id = "GOther", sprites = { "g_1" }, watts = 100 },
    },
    gates = {
        { kind = "action", path = "UseMachine", field = "machine", consumer = "GMachine" },
        { kind = "call", path = "Target.onUse", arg = 2, player = 1, consumer = "GMachine",
          allow = function(player, m, mode) return mode == "Off" end, refuse = false },
        { kind = "menu", name = "GatedMenu", consumer = "GMachine" },
    } }
"""


def make(side="sp"):
    lua = tp.make()
    lua.execute(TARGET)
    lua.execute("SIDE = '%s'; LiveWireCompat.Profiles.add(GATES); fire()" % side)
    return lua


def off(name):
    return "local %s = machine('GMachine'); %s:getModData().LWC_off = true" % (name, name)


class Action(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_powered_machine_keeps_the_action(self):
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), machine('GMachine')):isValid()"))
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), machine('GMachine')):isValidStart()"))

    def test_switched_off_machine_refuses_and_stops_the_action(self):
        self.assertFalse(self.lua.eval("(function() %s; return UseMachine:new(hero(), m):isValidStart() end)()" % off("m")))
        self.assertFalse(self.lua.eval("UseMachine:new(hero(), machine('GMachine', true)):isValid()"))

    def test_player_is_told_once_per_action(self):
        self.lua.execute("%s; A = UseMachine:new(hero(), m); A:isValid(); A:isValid(); A:isValidStart()" % off("m"))
        self.assertEqual(self.lua.eval("#HALO"), 1)
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_cut_machine_says_no_power(self):
        self.lua.execute("UseMachine:new(hero(), machine('GMachine', true)):isValid()")
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_NoPower")

    def test_other_machines_and_base_class_are_untouched(self):
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), machine('GOther', true)):isValid()"))
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), nil):isValid()"))
        self.assertIsNone(self.lua.eval("rawget(Base, 'lwcRefused')"))
        self.assertTrue(self.lua.eval("Base.isValidStart({ machine = machine('GMachine', true) })"))

    def test_wrapped_once_across_world_inits(self):
        self.lua.execute("FIRST = UseMachine.isValid; fire()")
        self.assertTrue(self.lua.eval("FIRST == UseMachine.isValid"))

    def test_action_needs_field_or_machine_function(self):
        self.assertEqual(self.lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'Bad', mods = { 'TargetMod' },
            consumers = {}, gates = { { kind = 'action', path = 'UseMachine', consumer = 'X' } } }) }""")[2],
            "invalid_profile")

    def test_machine_function_reads_the_machine(self):
        self.lua.execute("""UseOther = Base.derive('UseOther')
            function UseOther:isValid() return true end
            LiveWireCompat.Profiles.add({ name = 'Fn', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'action', path = 'UseOther', machine = function(a) return a.data.m end,
                            consumer = 'GMachine' } } }); fire()""")
        self.assertFalse(self.lua.eval(
            "setmetatable({ data = { m = machine('GMachine', true) } }, UseOther):isValid()"))


class Call(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_powered_machine_runs_the_function(self):
        self.assertEqual(self.lua.eval("Target.onUse(hero(), machine('GMachine'), 'Hot')"), "used")

    def test_blocked_machine_does_not_run_it_and_tells_the_player(self):
        self.assertFalse(self.lua.eval("(function() %s; return Target.onUse(hero(), m, 'Hot') end)()" % off("m")))
        self.assertEqual(self.lua.eval("CALLS"), 0)
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_allowed_call_goes_through_when_blocked(self):
        self.assertEqual(self.lua.eval("Target.onUse(hero(), machine('GMachine', true), 'Off')"), "used")

    def test_instead_replaces_the_refusal(self):
        self.lua.execute("""Target.update = function(m) return 'warm' end
            LiveWireCompat.Profiles.add({ name = 'Instead', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'call', path = 'Target.update', consumer = 'GMachine',
                            instead = function(original, m) m.forced = true; return 'off' end } } }); fire()""")
        self.assertEqual(self.lua.eval("Target.update(machine('GMachine', true))"), "off")
        self.assertEqual(self.lua.eval("Target.update(machine('GMachine'))"), "warm")

    def test_machine_function_reads_a_field_of_self(self):
        self.lua.execute("""Panel = { isUsable = function(self) return true end }
            LiveWireCompat.Profiles.add({ name = 'Panel', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'call', path = 'Panel.isUsable', consumer = 'GMachine', refuse = false,
                            machine = function(self) return self.bench end } } }); fire()""")
        self.assertFalse(self.lua.eval("Panel.isUsable({ bench = machine('GMachine', true) })"))
        self.assertTrue(self.lua.eval("Panel.isUsable({ bench = machine('GMachine') })"))

    def test_machine_function_and_arg_together_are_refused(self):
        self.assertEqual(self.lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'Both', mods = { 'TargetMod' },
            consumers = {}, gates = { { kind = 'call', path = 'a.b', arg = 2, machine = print, consumer = 'X' } } }) }""")[2],
            "invalid_profile")

    def test_missing_function_is_logged(self):
        self.lua.execute("""LiveWireCompat.Profiles.add({ name = 'Gone', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'call', path = 'Target.nope', consumer = 'GMachine' } } }); fire()""")
        self.assertIn("Target.nope not wrapped (gate_not_found)", self.lua.eval("LOG[#LOG]"))


class Menu(unittest.TestCase):
    def fill(self, lua, setup):
        lua.execute("CTX = menu(); %s; trigger('OnFillWorldObjectContextMenu', 0, CTX, {}, false)" % setup)

    def test_blocked_machine_option_is_greyed_with_the_reason(self):
        lua = make()
        self.fill(lua, "%s; OPT = CTX:addOption('Play', nil, print, m)" % off("m"))
        self.assertTrue(lua.eval("OPT.notAvailable"))
        self.assertEqual(lua.eval("OPT.toolTip.description"), "IGUI_LWC_MachineOff")

    def test_machine_as_target_is_found_too(self):
        lua = make()
        self.fill(lua, "OPT = CTX:addOption('Play', machine('GMachine', true), print)")
        self.assertTrue(lua.eval("OPT.notAvailable"))

    def test_powered_machine_and_other_options_stay_available(self):
        lua = make()
        self.fill(lua, "A = CTX:addOption('Play', nil, print, machine('GMachine')); "
                       "B = CTX:addOption('Look', nil, print, machine('GOther', true))")
        self.assertIsNone(lua.eval("A.notAvailable"))
        self.assertIsNone(lua.eval("B.notAvailable"))

    def test_switch_option_is_never_greyed(self):
        lua = make()
        self.fill(lua, "%s; OPT = CTX:addOption('Turn on', nil, print, m); OPT.lwcSwitch = true" % off("m"))
        self.assertIsNone(lua.eval("OPT.notAvailable"))

    def test_submenus_are_searched(self):
        lua = make()
        self.fill(lua, "SUB = menu(); CTX.subs[7] = SUB; P = CTX:addOption('Arcade'); P.subOption = 7; "
                       "OPT = SUB:addOption('Play', nil, print, machine('GMachine', true))")
        self.assertTrue(lua.eval("OPT.notAvailable"))
        self.assertIsNone(lua.eval("P.notAvailable"))

    def test_java_object_that_is_not_a_world_object_is_ignored(self):
        # 42.22 menu options may hold the Java context menu itself; like any Java object in
        # Kahlua it raises when a missing method is read.
        class JavaMenu:
            def __getitem__(self, key):
                raise KeyError("attempted index: %s of non-table" % key)

        lua = make()
        lua.globals().JAVA_MENU = JavaMenu()
        lua.execute("function instanceof(o, class) return false end")
        self.fill(lua, "A = CTX:addOption('Sub', JAVA_MENU, print, JAVA_MENU); "
                       "OPT = CTX:addOption('Play', nil, print, machine('GMachine', true))")
        self.assertIsNone(lua.eval("A.notAvailable"))
        self.assertTrue(lua.eval("OPT.notAvailable"))

    def test_test_pass_changes_nothing(self):
        lua = make()
        lua.execute("CTX = menu(); OPT = CTX:addOption('Play', nil, print, machine('GMachine', true)); "
                    "trigger('OnFillWorldObjectContextMenu', 0, CTX, {}, true)")
        self.assertIsNone(lua.eval("OPT.notAvailable"))

    def test_handler_added_once_and_never_on_a_server(self):
        lua = make()
        lua.execute("fire()")
        self.assertEqual(lua.eval("#EVENTS.OnFillWorldObjectContextMenu"), 1)
        server = make("server")
        self.assertEqual(server.eval("#EVENTS.OnFillWorldObjectContextMenu"), 0)


PIECES = r"""
-- Pieces of one furniture: only `billed` is a registered consumer (one piece per furniture).
function grid(billed, ...)
    local all = { billed, ... }
    local g = {}
    for _, p in ipairs(all) do
        p.getSpriteGrid = function() return g end
        p.getSquare = function() return {} end
        p.getSpriteGridObjectsIncludingSelf = function(self, list)
            list:clear(); for _, q in ipairs(all) do list:add(q) end; return list
        end
    end
end
function piece() return setmetatable({ sprite = 'g_tail' }, getmetatable(machine('x'))) end
-- B42 built furniture: SpriteConfig.getAllMultiSquareObjects, no sprite grid.
function entity(billed, ...)
    local all = { billed, ... }
    local config = { getAllMultiSquareObjects = function(self, list)
        for _, q in ipairs(all) do list:add(q) end; return true end }
    for _, p in ipairs(all) do
        p.getSpriteGrid = function() return nil end
        p.getSquare = function() return {} end
        p.getSpriteConfig = function() return config end
    end
end
"""


class OtherPieces(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.execute(PIECES)

    def test_piece_of_a_sprite_grid_finds_the_billed_piece(self):
        self.lua.execute("B = machine('GMachine', true); T = piece(); grid(B, T)")
        self.assertTrue(self.lua.eval("LiveWireCompat.Gates.billed(T) == B"))
        self.assertFalse(self.lua.eval("UseMachine:new(hero(), T):isValid()"))

    def test_piece_of_a_built_entity_finds_the_billed_piece(self):
        self.lua.execute("B = machine('GMachine'); T = piece(); entity(B, T); B:getModData().LWC_off = true")
        self.assertFalse(self.lua.eval("Target.onUse(hero(), T, 'Hot')"))
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_powered_furniture_keeps_working_from_any_piece(self):
        self.lua.execute("B = machine('GMachine'); T = piece(); grid(B, T)")
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), T):isValid()"))

    def test_lone_object_without_consumer_is_not_blocked(self):
        self.assertIsNone(self.lua.eval("LiveWireCompat.Gates.billed(piece())"))
        self.assertTrue(self.lua.eval("UseMachine:new(hero(), piece()):isValid()"))


class MenuReader(unittest.TestCase):
    def test_reader_finds_a_machine_the_option_does_not_carry_directly(self):
        lua = make()
        lua.execute("""LiveWireCompat.Profiles.add({ name = 'Reader', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'menu', name = 'Claw', consumer = 'GMachine',
                        machine = function(option) return option.target and option.target.inside end } } }); fire()""")
        lua.execute("CTX = menu(); OPT = CTX:addOption('Claw', { inside = machine('GMachine', true) }, print); "
                    "OK = CTX:addOption('Look', { inside = machine('GMachine') }, print); "
                    "trigger('OnFillWorldObjectContextMenu', 0, CTX, {}, false)")
        self.assertTrue(lua.eval("OPT.notAvailable"))
        self.assertIsNone(lua.eval("OK.notAvailable"))

    def test_reader_must_be_a_function(self):
        lua = make()
        self.assertEqual(lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'Bad', mods = { 'TargetMod' },
            consumers = {}, gates = { { kind = 'menu', name = 'M', consumer = 'X', machine = 3 } } }) }""")[2],
            "invalid_profile")


class Notify(unittest.TestCase):
    NOTIFY = """Mod = { transmit = function(m, extra) m.sent = (m.sent or 0) + 1; return 'ok', extra end }
        LiveWireCompat.Profiles.add({ name = 'N', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'notify', path = 'Mod.transmit', consumer = 'GMachine',
                        state = function(m) return m.on end } } }); fire()"""

    def setUp(self):
        self.lua = make()
        self.lua.execute("""function placed(id, sprite)
            local m = machine(id, false, sprite)
            m.sq = { getX = function() return 3 end, getY = function() return 4 end, getZ = function() return 0 end }
            return m end""")
        self.lua.execute(self.NOTIFY)

    def test_original_runs_and_returns_are_kept(self):
        self.assertEqual(tuple(self.lua.eval("{ Mod.transmit(placed('GMachine'), 7) }").values()), ("ok", 7))

    def test_a_change_of_state_is_reported_once(self):
        self.lua.execute("M = placed('GMachine'); M.on = true; Mod.transmit(M); Mod.transmit(M)")
        self.assertEqual(self.lua.eval("#CHANGED"), 1)
        self.lua.execute("M.on = false; Mod.transmit(M)")
        self.assertEqual(self.lua.eval("#CHANGED"), 2)
        self.assertTrue(self.lua.eval("CHANGED[2] == M"))

    def test_other_machines_are_not_reported(self):
        self.lua.execute("Mod.transmit(placed('GOther')); Mod.transmit({})")
        self.assertEqual(self.lua.eval("#CHANGED"), 0)

    def test_without_state_every_call_is_reported(self):
        self.lua.execute("""Mod2 = { use = function(p, m) end }
            LiveWireCompat.Profiles.add({ name = 'N2', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'notify', path = 'Mod2.use', arg = 2, consumer = 'GMachine' } } }); fire()
            Mod2.use(hero(), placed('GMachine')); Mod2.use(hero(), placed('GMachine'))""")
        self.assertEqual(self.lua.eval("#CHANGED"), 2)

    def test_notify_wraps_on_top_of_a_call_gate_of_the_same_function(self):
        self.lua.execute("""LiveWireCompat.Profiles.add({ name = 'N3', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'notify', path = 'Target.onUse', arg = 2, consumer = 'GMachine',
                        state = function(m) return m.mode end } } }); fire()
            M = placed('GMachine'); M.mode = 'Hot'; Target.onUse(hero(), M, 'Hot')""")
        self.assertEqual(self.lua.eval("CALLS"), 1)
        self.assertEqual(self.lua.eval("#CHANGED"), 1)

    def test_client_reports_through_a_command(self):
        self.lua.execute("""SIDE = 'client'; SENT = {}
            function sendClientCommand(p, mod, cmd, args) SENT[#SENT + 1] = { mod, cmd, args } end
            function getPlayer() return hero() end
            M = placed('GMachine', 'g_0')
            M.on = true; Mod.transmit(M)""")
        self.assertEqual(self.lua.eval("#CHANGED"), 0)
        self.assertEqual(self.lua.eval("SENT[1][1] .. '/' .. SENT[1][2]"), "LWC/changed")
        self.assertEqual(self.lua.eval("SENT[1][3].sprite"), "g_0")


class TwoProfilesOneFunction(unittest.TestCase):
    def test_each_profile_gates_its_own_machines_on_a_shared_vanilla_function(self):
        lua = make()
        lua.execute("""Vanilla = { start = function(p, m) return 'started' end }
            LiveWireCompat.Profiles.add({ name = 'P1', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'call', path = 'Vanilla.start', arg = 2, consumer = 'GMachine' } } })
            LiveWireCompat.Profiles.add({ name = 'P2', mods = { 'TargetMod' }, consumers = {},
                gates = { { kind = 'call', path = 'Vanilla.start', arg = 2, consumer = 'GOther' } } })
            fire(); fire()""")
        self.assertIsNone(lua.eval("Vanilla.start(hero(), machine('GMachine', true))"))
        self.assertIsNone(lua.eval("Vanilla.start(hero(), machine('GOther', true))"))
        self.assertEqual(lua.eval("Vanilla.start(hero(), machine('GOther'))"), "started")
        # Two layers only, even after the second world init.
        self.assertEqual(lua.eval("""(function() local n, f = 0, Vanilla.start
            while f do n = n + 1; f = LiveWireCompat.Gates.inner[f] end return n end)()"""), 3)


class CustomAndSides(unittest.TestCase):
    def test_custom_installer_gets_the_gate_and_helpers(self):
        lua = make()
        lua.execute("""LiveWireCompat.Profiles.add({ name = 'Custom', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'custom', name = 'pause', consumer = 'GMachine',
                        install = function(g, G) GOT = { g.name, G.blocked ~= nil }; return true end } } }); fire()""")
        self.assertEqual(lua.eval("GOT[1]"), "pause")
        self.assertTrue(lua.eval("GOT[2]"))

    def test_custom_failure_is_logged(self):
        lua = make()
        lua.execute("""LiveWireCompat.Profiles.add({ name = 'Custom', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'custom', name = 'pause', consumer = 'GMachine',
                        install = function() return false, 'gate_not_found' end } } }); fire()""")
        self.assertIn("pause not wrapped (gate_not_found)", lua.eval("LOG[#LOG]"))

    def test_custom_needs_name_and_installer(self):
        lua = make()
        self.assertEqual(lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'Bad', mods = { 'TargetMod' },
            consumers = {}, gates = { { kind = 'custom', consumer = 'X', install = print } } }) }""")[2],
            "invalid_profile")

    SERVER_GATE = """Srv = { check = function(m) return true end }
        LiveWireCompat.Profiles.add({ name = 'Srv', mods = { 'TargetMod' }, consumers = {},
            gates = { { kind = 'object', path = 'Srv.check', consumer = 'GMachine', side = 'server' } } }); fire()"""

    def test_server_gate_is_installed_on_the_server_and_in_single_player(self):
        for side in ("server", "sp"):
            lua = make(side)
            lua.execute(self.SERVER_GATE)
            self.assertFalse(lua.eval("Srv.check(machine('GMachine', true))"), side)

    def test_server_gate_is_skipped_on_a_client(self):
        lua = make("client")
        lua.execute(self.SERVER_GATE)
        self.assertTrue(lua.eval("Srv.check(machine('GMachine', true))"))


if __name__ == "__main__":
    unittest.main()
