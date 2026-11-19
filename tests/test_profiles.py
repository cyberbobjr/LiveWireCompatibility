"""Offline tests of the profile registry and loader (ADR-001, D02, D04), embedded Lua 5.1 (pip install lupa).

LiveWire's public API is replaced by a double that keeps its contract (revision, refusals,
consumer id of an object, power state after the circuits). The profile files are tested by
test_profile_files.py.
Run: python tests/test_profiles.py
"""
import os
import unittest

import lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = os.path.join(ROOT, "Contents", "mods")
LUA = os.path.join(MODS, "batman_LiveWireCompatibility", "42.21", "media", "lua")
# Profile files, one per target mod.
PROFILE_GLOB = os.path.join(MODS, "*", "42.21", "media", "lua", "shared", "LiveWireCompatibility", "Profiles", "*.lua")

DOUBLES = r"""
LOG = {}
print = function(s) LOG[#LOG + 1] = s end
HANDLERS = {}
EVENTS = {}
local function event(name)
    EVENTS[name] = {}
    return { Add = function(fn) table.insert(EVENTS[name], fn) end }
end
Events = { OnInitWorld = { Add = function(fn) HANDLERS[#HANDLERS + 1] = fn end },
           OnFillWorldObjectContextMenu = event("OnFillWorldObjectContextMenu"),
           OnClientCommand = event("OnClientCommand") }
function fire() for _, fn in ipairs(HANDLERS) do fn() end end
function trigger(name, ...) for _, fn in ipairs(EVENTS[name] or {}) do fn(...) end end
-- Side of the Lua state: SIDE = "sp", "client" or "server".
SIDE = "sp"
function isClient() return SIDE == "client" end
function isServer() return SIDE == "server" end
function getText(key, ...) return key end
-- java.util.ArrayList as seen from Lua (0-based get).
ArrayList = { new = function()
    local l = { items = {} }
    function l:add(o) self.items[#self.items + 1] = o end
    function l:size() return #self.items end
    function l:get(i) return self.items[i + 1] end
    function l:clear() self.items = {} end
    return l
end }
ACTIVE = {}
function getActivatedMods()
    return { contains = function(self, id) return ACTIVE[id] == true end }
end
-- LiveWire API double (revision 6 contract).
REGISTERED = {}
REFUSE = {}
LiveWire = { API = { revision = 6 } }
function LiveWire.API.registerConsumer(id, def)
    if REFUSE[id] then return false, REFUSE[id] end
    if REGISTERED[id] then return false, "duplicate_consumer" end
    REGISTERED[id] = def
    return true
end
function LiveWire.API.consumer(o) return type(o) == "table" and o.cid or nil end
function LiveWire.API.consumerPowered(o) return o.cut ~= true end
-- World object double: ModData as IsoObject (hasModData false while empty).
local ObjectMethods = {}
ObjectMethods.__index = ObjectMethods
function ObjectMethods:hasModData() return self.md ~= nil and next(self.md) ~= nil end
function ObjectMethods:getModData() self.md = self.md or {}; return self.md end
function ObjectMethods:transmitModData() self.sent = (self.sent or 0) + 1 end
function ObjectMethods:getSprite() return { getName = function() return self.sprite end } end
function ObjectMethods:getSquare() return self.sq end
function machine(id, cut, sprite) return setmetatable({ cid = id, cut = cut, sprite = sprite }, ObjectMethods) end
function square(...)
    local list = { ... }
    return { getObjects = function()
        return { size = function() return #list end, get = function(_, i) return list[i + 1] end }
    end }
end
-- A target mod with public power checks.
Target = { Power = {
    isPowered = function(obj) return SQUARE_POWER end,
    squarePowered = function(sq) return SQUARE_POWER end,
    twoArgs = function(player, obj) return SQUARE_POWER end,
} }
SQUARE_POWER = true
"""

PROFILE = r"""
PROFILE = { name = "Target", mods = { "TargetMod" },
    consumers = {
        { id = "TargetDryer", sprites = { "target_0", "target_1" }, watts = 1200,
          running = function(o) return o.on end, idle = 5, category = "laundry" },
        { id = "TargetLamp", sprites = { "target_2" }, watts = function(o) return o.level * 10 end },
    },
    gates = {
        { path = "Target.Power.isPowered", kind = "object", consumer = "TargetDryer" },
        { path = "Target.Power.squarePowered", kind = "square", consumer = "TargetDryer" },
        { path = "Target.Power.twoArgs", arg = 2, kind = "object", consumer = "TargetDryer" },
    } }
"""


def require_files(lua):
    """Kahlua-like require: a module path is looked up under shared/, client/ then server/, loaded once."""
    lua.globals().REQUIRE_ROOT = LUA.replace("\\", "/")
    lua.execute(r"""
LOADED = {}
function require(name)
    if LOADED[name] ~= nil then return LOADED[name] end
    for _, side in ipairs({ "shared", "client", "server" }) do
        local f = io.open(REQUIRE_ROOT .. "/" .. side .. "/" .. name .. ".lua", "r")
        if f then
            local code = f:read("*a"); f:close()
            LOADED[name] = true
            local r = assert((loadstring or load)(code, name))()
            if r ~= nil then LOADED[name] = r end
            return LOADED[name]
        end
    end
    error("module not found: " .. name)
end
""")


def make(active=True):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(DOUBLES)
    require_files(lua)
    lua.execute('require "LiveWireCompatibility/LWC_Profiles"')
    lua.execute(PROFILE)
    if active:
        lua.execute("ACTIVE.TargetMod = true")
    return lua


class Registry(unittest.TestCase):
    def test_valid_profile_is_added(self):
        lua = make()
        self.assertEqual(lua.eval("{ LiveWireCompat.Profiles.add(PROFILE) }")[1], True)

    def test_invalid_profiles_are_refused(self):
        lua = make()
        for bad in ["nil", "{ name = 'x', mods = {}, consumers = {} }",
                    "{ name = 'x', mods = { 'm' }, consumers = { { id = 'a', sprites = {}, watts = 1 } } }",
                    "{ name = 'x', mods = { 'm' }, consumers = { { id = 'a', sprites = { 's' }, watts = 'w' } } }",
                    "{ name = 'x', mods = { 'm' }, consumers = {}, gates = { { path = 'a.b', kind = 'x', consumer = 'a' } } }"]:
            self.assertEqual(tuple(lua.eval("{ LiveWireCompat.Profiles.add(%s) }" % bad).values()),
                             (False, "invalid_profile"), bad)

    def test_same_name_twice_is_refused(self):
        lua = make()
        lua.execute("LiveWireCompat.Profiles.add(PROFILE)")
        self.assertEqual(tuple(lua.eval("{ LiveWireCompat.Profiles.add(PROFILE) }").values()),
                         (False, "duplicate_profile"))


class Loading(unittest.TestCase):
    def test_active_profile_registers_its_consumers_at_world_init(self):
        lua = make()
        lua.execute("LiveWireCompat.Profiles.add(PROFILE)")
        self.assertIsNone(lua.eval("REGISTERED.TargetDryer"))
        lua.execute("fire()")
        self.assertEqual(lua.eval("REGISTERED.TargetDryer.sprites[2]"), "target_1")
        self.assertEqual(lua.eval("REGISTERED.TargetDryer.category"), "laundry")
        self.assertIsNotNone(lua.eval("REGISTERED.TargetLamp"))

    def test_inactive_profile_does_nothing(self):
        lua = make(active=False)
        lua.execute("LiveWireCompat.Profiles.add(PROFILE); fire()")
        self.assertIsNone(lua.eval("REGISTERED.TargetDryer"))
        self.assertEqual(lua.eval("Target.Power.isPowered({ cid = 'TargetDryer', cut = true })"), True)

    def test_old_or_missing_api_registers_nothing_and_logs(self):
        lua = make()
        lua.execute("LiveWire.API.revision = 5; LiveWireCompat.Profiles.add(PROFILE); fire()")
        self.assertIsNone(lua.eval("REGISTERED.TargetDryer"))
        self.assertIn("revision 6", lua.eval("LOG[1]"))

    def test_second_world_init_registers_nothing_twice(self):
        lua = make()
        lua.execute("LiveWireCompat.Profiles.add(PROFILE); fire(); fire()")
        self.assertEqual(lua.eval("#LOG"), 0)

    def test_refused_consumer_is_logged_and_others_still_registered(self):
        lua = make()
        lua.execute("REFUSE.TargetDryer = 'duplicate_sprite'; LiveWireCompat.Profiles.add(PROFILE); fire()")
        self.assertIn("TargetDryer not registered (duplicate_sprite)", lua.eval("LOG[1]"))
        self.assertIsNotNone(lua.eval("REGISTERED.TargetLamp"))


class Consumption(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.execute("LiveWireCompat.Profiles.add(PROFILE); fire()")

    def test_running_machine_draws_its_watts(self):
        self.assertEqual(self.lua.eval("REGISTERED.TargetDryer.powerConsumption({ on = true })"), 1200)

    def test_stopped_machine_draws_idle(self):
        self.assertEqual(self.lua.eval("REGISTERED.TargetDryer.powerConsumption({ on = false })"), 5)

    def test_watts_function_is_called_without_running(self):
        self.assertEqual(self.lua.eval("REGISTERED.TargetLamp.powerConsumption({ level = 4 })"), 40)


class Gates(unittest.TestCase):
    def setUp(self):
        self.lua = make()
        self.lua.execute("LiveWireCompat.Profiles.add(PROFILE); fire()")

    def ask(self, code):
        return self.lua.eval(code)

    def test_cut_machine_has_no_power(self):
        self.assertEqual(self.ask("Target.Power.isPowered(machine('TargetDryer', true))"), False)

    def test_machine_with_current_keeps_power(self):
        self.assertEqual(self.ask("Target.Power.isPowered(machine('TargetDryer', false))"), True)

    def test_original_no_power_stays_no_power(self):
        self.lua.execute("SQUARE_POWER = false")
        self.assertEqual(self.ask("Target.Power.isPowered(machine('TargetDryer', false))"), False)

    def test_other_objects_keep_the_original_answer(self):
        self.assertEqual(self.ask("Target.Power.isPowered({ cid = 'Other', cut = true })"), True)
        self.assertEqual(self.ask("Target.Power.isPowered({})"), True)

    def test_square_gate_finds_the_machine_on_the_square(self):
        self.assertEqual(self.ask("Target.Power.squarePowered(square({}, machine('TargetDryer', true)))"), False)
        self.assertEqual(self.ask("Target.Power.squarePowered(square({}, machine('TargetDryer', false)))"), True)
        self.assertEqual(self.ask("Target.Power.squarePowered(square({}))"), True)

    def test_argument_position_is_respected(self):
        self.assertEqual(self.ask("Target.Power.twoArgs({}, machine('TargetDryer', true))"), False)

    def test_wrapped_once_across_world_inits(self):
        self.lua.execute("FIRST = Target.Power.isPowered; fire()")
        self.assertTrue(self.ask("FIRST == Target.Power.isPowered"))

    def test_missing_power_check_is_logged(self):
        lua = make()
        lua.execute("""LiveWireCompat.Profiles.add({ name = 'Gone', mods = { 'TargetMod' }, consumers = {},
            gates = { { path = 'Target.Nope.fn', kind = 'object', consumer = 'X' } } }); fire()""")
        self.assertIn("Target.Nope.fn not wrapped (gate_not_found)", lua.eval("LOG[1]"))



class SharedAndClientGates(unittest.TestCase):
    """One power check for several machines; a check that lives in the target's client Lua."""

    SHARED = """LiveWireCompat.Profiles.add({ name = 'Shared', mods = { 'TargetMod' },
        consumers = {
            { id = 'TargetSaw', sprites = { 's_0' }, watts = 500 },
            { id = 'TargetDrill', sprites = { 's_1' }, watts = 150 },
        },
        gates = {
            { path = 'Target.Power.isPowered', kind = 'object', consumer = { 'TargetSaw', 'TargetDrill' } },
            { path = 'Target.Power.squarePowered', kind = 'square', consumer = { 'TargetSaw', 'TargetDrill' } },
        } }); fire()"""

    def test_every_named_machine_is_cut(self):
        lua = make()
        lua.execute(self.SHARED)
        self.assertEqual(lua.eval("Target.Power.isPowered(machine('TargetSaw', true))"), False)
        self.assertEqual(lua.eval("Target.Power.isPowered(machine('TargetDrill', true))"), False)
        self.assertEqual(lua.eval("Target.Power.isPowered(machine('TargetDrill', false))"), True)
        self.assertEqual(lua.eval("Target.Power.squarePowered(square({}, machine('TargetDrill', true)))"), False)

    def test_machines_not_named_keep_the_original_answer(self):
        lua = make()
        lua.execute(self.SHARED)
        self.assertEqual(lua.eval("Target.Power.isPowered({ cid = 'Other', cut = true })"), True)

    def test_empty_consumer_list_is_refused(self):
        lua = make()
        self.assertEqual(lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'E', mods = { 'TargetMod' },
            consumers = {}, gates = { { path = 'a.b', kind = 'object', consumer = {} } } }) }""")[2],
            "invalid_profile")

    CLIENT = """LiveWireCompat.Profiles.add({ name = 'Client', mods = { 'TargetMod' },
        consumers = { { id = 'TargetPc', sprites = { 'pc_0' }, watts = 120 } },
        gates = { { path = 'ClientOnly.hasPower', kind = 'object', consumer = 'TargetPc', side = 'client' } } })"""

    def test_client_gate_is_skipped_silently_on_a_dedicated_server(self):
        lua = make()
        lua.execute("isServer = function() return true end")
        lua.execute(self.CLIENT + "; fire()")
        self.assertEqual(lua.eval("#LOG"), 0)
        self.assertIsNotNone(lua.eval("REGISTERED.TargetPc"))

    def test_client_gate_is_wrapped_on_a_client(self):
        lua = make()
        lua.execute("isServer = function() return false end")
        lua.execute("ClientOnly = { hasPower = function(o) return true end }")
        lua.execute(self.CLIENT + "; fire()")
        self.assertEqual(lua.eval("ClientOnly.hasPower(machine('TargetPc', true))"), False)

    def test_unknown_side_is_refused(self):
        lua = make()
        self.assertEqual(lua.eval("""{ LiveWireCompat.Profiles.add({ name = 'S', mods = { 'TargetMod' },
            consumers = {}, gates = { { path = 'a.b', kind = 'object', consumer = 'X', side = 'both' } } }) }""")[2],
            "invalid_profile")


if __name__ == "__main__":
    unittest.main()
