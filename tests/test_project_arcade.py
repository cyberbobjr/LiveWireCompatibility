"""Offline tests of the Project Arcade profile (ADR-002, D06): switch, menu, action and call gates.

Doubles reproduce the shape of the Project Arcade globals (Workshop 3645980077, common/ variant):
timed action classes derived from ISBaseTimedAction (methods on the class, instances through a
metatable, the machine in `object`, `machine` or `machineObj`), ProjectArcade_CoinPusher.OpenUI
(playerObj, machineObj) and the coin pusher panel (fields playerObj, machineObj, onPlay; method
beginPlay). The context menu double comes from test_gates.py.
Run: python -B -m unittest tests.test_project_arcade
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_gates as tg  # noqa: E402
import test_profile_files as tpf  # noqa: E402
import test_profiles as tp  # noqa: E402

ARCADE = r"""
-- ISBaseTimedAction as in vanilla shared/TimedActions/ISBaseTimedAction.lua.
ISBaseTimedAction = { Type = "ISBaseTimedAction" }
ISBaseTimedAction.__index = ISBaseTimedAction
function ISBaseTimedAction:isValidStart() return true end
function ISBaseTimedAction:isValid() end
function ISBaseTimedAction:derive(type)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.Type = type
    return o
end
function ISBaseTimedAction.new(self, character)
    local o = { character = character }
    setmetatable(o, self)
    self.__index = self
    return o
end
-- ProjectArcade_PlayArcadeTimedAction.lua:750-771, :994-998
ProjectArcade_PlayArcadeTimedAction = ISBaseTimedAction:derive("ProjectArcade_PlayArcadeTimedAction")
function ProjectArcade_PlayArcadeTimedAction:isValid()
    return self.character ~= nil and self.object ~= nil and self.object:getSquare() ~= nil
end
function ProjectArcade_PlayArcadeTimedAction:new(character, object)
    local o = ISBaseTimedAction.new(self, character); o.character = character; o.object = object; return o
end
-- ProjectArcade_ClawTimedAction.lua:189-191, :324-327
ProjectArcade_ClawTimedAction = ISBaseTimedAction:derive("ProjectArcade_ClawTimedAction")
function ProjectArcade_ClawTimedAction:isValid() return self.machine ~= nil and self.machine:getSquare() ~= nil end
function ProjectArcade_ClawTimedAction:new(character, machine)
    local o = ISBaseTimedAction.new(self, character); o.character = character; o.machine = machine; return o
end
-- ProjectArcade_PunchingTimedAction.lua:194-196, :270-273
ProjectArcade_PunchingTimedAction = ISBaseTimedAction:derive("ProjectArcade_PunchingTimedAction")
function ProjectArcade_PunchingTimedAction:isValid()
    return self.character and self.object and self.object:getSquare() ~= nil
end
function ProjectArcade_PunchingTimedAction:new(character, object)
    local o = ISBaseTimedAction.new(self, character); o.character = character; o.object = object; return o
end
-- ProjectArcade_CoinPusherTimedAction.lua:5-7, :26-28
ProjectArcade_CoinPusherTimedAction = ISBaseTimedAction:derive("ProjectArcade_CoinPusherTimedAction")
function ProjectArcade_CoinPusherTimedAction:isValid()
    return self.character ~= nil and self.machineObj ~= nil and self.machineObj:getSquare() ~= nil
end
function ProjectArcade_CoinPusherTimedAction:new(character, machineObj, onDoneFn)
    local o = ISBaseTimedAction.new(self, character); o.machineObj = machineObj; o.onDone = onDoneFn; return o
end
-- ProjectArcade_CoinPusher.lua:174 (opens the panel; nothing is paid yet)
OPENED = 0
ProjectArcade_CoinPusher = {}
function ProjectArcade_CoinPusher.OpenUI(playerObj, machineObj) OPENED = OPENED + 1 end
-- ISUI/ProjectArcade_CoinPusherUI.lua:464-491 (beginPlay calls onPlay, which pays), :637, :658-667
PLAYED = 0
ProjectArcade_CoinPusherUI = {}
ProjectArcade_CoinPusherUI.__index = ProjectArcade_CoinPusherUI
function ProjectArcade_CoinPusherUI:new(playerObj, machineObj)
    return setmetatable({ playerObj = playerObj, machineObj = machineObj, state = "idle",
                          onPlay = function(pitId) PLAYED = PLAYED + 1 end }, self)
end
function ProjectArcade_CoinPusherUI:beginPlay(pitId)
    if self.state ~= "idle" then return end
    if self.onPlay then self.onPlay(pitId) end
end
function ProjectArcade_CoinPusherUI:close() self.closed = true end
-- java.util.ArrayList as seen from Lua (0-based get).
NEW_LISTS = 0
ArrayList = { new = function()
    NEW_LISTS = NEW_LISTS + 1
    local l = { items = {} }
    function l:clear() self.items = {} end
    function l:add(o) self.items[#self.items + 1] = o end
    function l:size() return #self.items end
    function l:get(i) return self.items[i + 1] end
    return l
end }
-- A piece of a multi-tile furniture that is not the billed one: IsoObject.getSpriteGridObjects
-- (IsoObject.java:5074) clears the list and adds every piece of the grid, itself included.
function piece(sprite, ...)
    local others = { ... }
    local p = machine(nil, false, sprite)
    p.sq = {}
    function p:getSpriteGrid() return true end
    function p:getSpriteGridObjectsIncludingSelf(list)
        list:clear(); list:add(self)
        for i = 1, #others do list:add(others[i]) end
        return list
    end
    return p
end
function placed(id, cut) local m = machine(id, cut); m.sq = {}; return m end
"""


def make(side="sp"):
    lua = tp.make(active=False)
    lua.execute(tg.TARGET)
    lua.execute(ARCADE)
    tpf.load_all(lua)
    lua.execute("ACTIVE.ProjectArcade = true; SIDE = '%s'; fire()" % side)
    return lua


def off(name, cid):
    return "local %s = placed('%s'); %s:getModData().LWC_off = true" % (name, cid, name)


class Profile(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_every_machine_gets_the_switch(self):
        for cid in ("PAArcadeCabinet", "PASitDownCabinet", "PAPinball", "PAClawMachine", "PACoinPusher",
                    "PAPunchingMachine"):
            self.assertTrue(self.lua.eval("LiveWireCompat.Switch.ids.%s" % cid), cid)

    def test_sit_down_cabinet_is_billed_on_the_piece_the_mod_plays(self):
        sprites = sorted(self.lua.eval("REGISTERED.PASitDownCabinet.sprites").values())
        self.assertEqual(sprites, ["pa_complex_3", "pa_complex_4", "pa_complex_6", "pa_complex_9"])


class Menu(unittest.TestCase):
    def fill(self, lua, setup):
        lua.execute("CTX = menu(); %s; trigger('OnFillWorldObjectContextMenu', 0, CTX, {}, false)" % setup)

    def test_play_option_of_a_switched_off_cabinet_is_greyed(self):
        lua = make()
        # PAMPlayGameMenu.lua:424: context:addOption(label, obj, function() ... end)
        self.fill(lua, "%s; OPT = CTX:addOption('Play', m, print)" % off("m", "PAArcadeCabinet"))
        self.assertTrue(lua.eval("OPT.notAvailable"))
        self.assertEqual(lua.eval("OPT.toolTip.description"), "IGUI_LWC_MachineOff")

    def test_play_option_of_a_powered_pinball_stays_available(self):
        lua = make()
        self.fill(lua, "OPT = CTX:addOption('Play', placed('PAPinball'), print)")
        self.assertIsNone(lua.eval("OPT.notAvailable"))

    def test_try_strength_of_a_cut_punching_machine_is_greyed(self):
        lua = make()
        # ProjectArcade_PunchingMachine.lua:435: subMenu:addOption(text, worldobjects, onTryStrength, playerObj, machineObj)
        self.fill(lua, "OPT = CTX:addOption('Try', {}, print, hero(), placed('PAPunchingMachine', true))")
        self.assertTrue(lua.eval("OPT.notAvailable"))


    def test_claw_option_found_through_the_clicked_objects(self):
        lua = make()
        # ProjectArcade_ClawMachine.lua:168-169: context:addOption(text, worldobjects, closure)
        self.fill(lua, "OPT = CTX:addOption('ContextMenu_ProjectArcade_PlayClawMachine', "
                       "{ hero(), placed('PAClawMachine', true) }, print); "
                       "VAN = CTX:addOption('Walk to', { placed('PAClawMachine', true) }, print)")
        self.assertTrue(lua.eval("OPT.notAvailable"))
        self.assertIsNone(lua.eval("VAN.notAvailable"))

    def test_claw_option_of_a_powered_machine_stays_available(self):
        lua = make()
        self.fill(lua, "OPT = CTX:addOption('ContextMenu_ProjectArcade_PlayClawMachine', "
                       "{ placed('PAClawMachine') }, print)")
        self.assertIsNone(lua.eval("OPT.notAvailable"))


class Actions(unittest.TestCase):
    CASES = (("ProjectArcade_PlayArcadeTimedAction", "PAArcadeCabinet"),
             ("ProjectArcade_PlayArcadeTimedAction", "PASitDownCabinet"),
             ("ProjectArcade_PlayArcadeTimedAction", "PAPinball"),
             ("ProjectArcade_ClawTimedAction", "PAClawMachine"),
             ("ProjectArcade_PunchingTimedAction", "PAPunchingMachine"),
             ("ProjectArcade_CoinPusherTimedAction", "PACoinPusher"))

    def setUp(self):
        self.lua = make()

    def test_powered_machine_keeps_the_game(self):
        for cls, cid in self.CASES:
            self.assertTrue(self.lua.eval("%s:new(hero(), placed('%s')):isValid()" % (cls, cid)), cls)
            self.assertTrue(self.lua.eval("%s:new(hero(), placed('%s')):isValidStart()" % (cls, cid)), cls)

    def test_cut_machine_stops_the_game(self):
        for cls, cid in self.CASES:
            self.assertFalse(self.lua.eval("%s:new(hero(), placed('%s', true)):isValid()" % (cls, cid)), cls)

    def test_switched_off_machine_refuses_and_says_why(self):
        self.lua.execute("%s; A = ProjectArcade_ClawTimedAction:new(hero(), m); OK = A:isValidStart()"
                         % off("m", "PAClawMachine"))
        self.assertFalse(self.lua.eval("OK"))
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_other_piece_of_a_pinball_is_judged_by_its_billed_head(self):
        # pa_pinballs_21 is the 0,0 piece of pinball_etpm; the mod also plays on it (PAMPlayGameMenu.lua:67).
        self.assertFalse(self.lua.eval(
            "ProjectArcade_PlayArcadeTimedAction:new(hero(), piece('pa_pinballs_21', placed('PAPinball', true))):isValid()"))
        self.assertTrue(self.lua.eval(
            "ProjectArcade_PlayArcadeTimedAction:new(hero(), piece('pa_pinballs_21', placed('PAPinball'))):isValid()"))

    def test_grid_list_is_allocated_once(self):
        self.lua.execute("""for i = 1, 3 do
            ProjectArcade_PlayArcadeTimedAction:new(hero(), piece('pa_pinballs_25', placed('PAPinball'))):isValid()
        end""")
        self.assertEqual(self.lua.eval("NEW_LISTS"), 1)

    def test_removed_machine_keeps_the_original_answer(self):
        self.assertFalse(self.lua.eval(
            "ProjectArcade_PlayArcadeTimedAction:new(hero(), machine(nil, false, 'pa_pinballs_21')):isValid()"))
        self.assertEqual(self.lua.eval("NEW_LISTS"), 0)


class CoinPusher(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_panel_of_a_switched_off_pusher_does_not_open(self):
        self.lua.execute("%s; ProjectArcade_CoinPusher.OpenUI(hero(), m)" % off("m", "PACoinPusher"))
        self.assertEqual(self.lua.eval("OPENED"), 0)
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_panel_of_a_powered_pusher_opens(self):
        self.lua.execute("ProjectArcade_CoinPusher.OpenUI(hero(), placed('PACoinPusher'))")
        self.assertEqual(self.lua.eval("OPENED"), 1)

    def test_cut_while_the_panel_is_open_closes_it_before_paying(self):
        self.lua.execute("UI = ProjectArcade_CoinPusherUI:new(hero(), placed('PACoinPusher', true)); UI:beginPlay(1)")
        self.assertEqual(self.lua.eval("PLAYED"), 0)
        self.assertTrue(self.lua.eval("UI.closed"))
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_NoPower")

    def test_powered_pusher_plays(self):
        self.lua.execute("UI = ProjectArcade_CoinPusherUI:new(hero(), placed('PACoinPusher')); UI:beginPlay(2)")
        self.assertEqual(self.lua.eval("PLAYED"), 1)
        self.assertIsNone(self.lua.eval("UI.closed"))


class Sides(unittest.TestCase):
    def test_gates_are_not_installed_on_a_dedicated_server(self):
        lua = make("server")
        lua.execute("ProjectArcade_CoinPusher.OpenUI(hero(), placed('PACoinPusher', true))")
        self.assertEqual(lua.eval("OPENED"), 1)
        self.assertTrue(lua.eval("ProjectArcade_ClawTimedAction:new(hero(), placed('PAClawMachine', true)):isValid()"))


if __name__ == "__main__":
    unittest.main()
