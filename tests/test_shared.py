"""Shared tiles (ADR-005): a vanilla tile two profiles give a use to is registered once to LiveWire;
each placed object belongs to the member whose owns(o) is true, else to the member without owns.
Run: python tests/test_shared.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402

PROFILES = r"""
-- LiveWire double resolves a shared object by its sprite name: registered sprites -> consumer id.
BY_SPRITE = {}
local register = LiveWire.API.registerConsumer
function LiveWire.API.registerConsumer(id, def)
    local ok, why = register(id, def)
    if ok then for _, s in ipairs(def.sprites) do BY_SPRITE[s] = id end end
    return ok, why
end
-- As LW_Consumers.of: found by sprite, then refined by the definition's couldBePowered.
function LiveWire.API.consumer(o)
    if type(o) ~= "table" then return nil end
    if o.cid then return o.cid end
    local id = BY_SPRITE[o.sprite]
    local def = id and REGISTERED[id]
    if def and def.couldBePowered and def.couldBePowered(o) ~= true then return nil end
    return id
end
Tool = { isPowered = function(o) return true end }
DESK = { "desk_0", "desk_1" }
LiveWireCompat.Profiles.add({ name = "A", mods = { "ModA" },
    consumers = { { id = "AMachine", sprites = DESK, watts = 100, switch = true, shared = "VanillaDesk" } },
    gates = { { kind = "object", path = "Tool.isPowered", consumer = "AMachine" } } })
LiveWireCompat.Profiles.add({ name = "B", mods = { "ModB" },
    consumers = { { id = "BMachine", sprites = { "desk_1", "desk_2" }, watts = 40, shared = "VanillaDesk",
                    owns = function(o) return o.b == true end } } })
function obj(sprite, b) return setmetatable({ sprite = sprite, b = b }, getmetatable(machine('x'))) end
"""


def make(*mods):
    lua = tp.make(active=False)
    lua.execute(PROFILES)
    for m in mods:
        lua.execute("ACTIVE.%s = true" % m)
    lua.execute("fire()")
    return lua


class Registration(unittest.TestCase):
    def test_one_livewire_consumer_with_the_sprites_of_the_active_profiles(self):
        lua = make("ModA", "ModB")
        self.assertIsNotNone(lua.eval("REGISTERED.VanillaDesk"))
        self.assertIsNone(lua.eval("REGISTERED.AMachine"))
        self.assertEqual(sorted(lua.eval("REGISTERED.VanillaDesk.sprites").values()), ["desk_0", "desk_1", "desk_2"])

    def test_only_one_profile_active_registers_its_own_sprites(self):
        lua = make("ModA")
        self.assertEqual(sorted(lua.eval("REGISTERED.VanillaDesk.sprites").values()), ["desk_0", "desk_1"])

    def test_second_world_init_registers_nothing_twice(self):
        lua = make("ModA", "ModB")
        lua.execute("fire()")
        self.assertEqual(lua.eval("#LOG"), 0)


class CouldBePowered(unittest.TestCase):
    def test_a_member_refining_its_objects_does_not_recurse(self):
        lua = tp.make(active=False)
        lua.execute(PROFILES)
        lua.execute("""LiveWireCompat.Profiles.add({ name = "C", mods = { "ModC" },
            consumers = { { id = "CCam", sprites = { "desk_0" }, watts = 5, shared = "VanillaDesk",
                            owns = function(o) return o.c == true end,
                            couldBePowered = function(o) return o.grid == true end } } })
            ACTIVE.ModA = true; ACTIVE.ModC = true; fire()""")
        self.assertEqual(lua.eval("LiveWireCompat.Profiles.consumerIdOf(obj('desk_0'))"), "AMachine")
        lua.execute("C1 = obj('desk_0'); C1.c = true; C1.grid = true; C2 = obj('desk_0'); C2.c = true")
        self.assertEqual(lua.eval("LiveWireCompat.Profiles.consumerIdOf(C1)"), "CCam")
        self.assertIsNone(lua.eval("LiveWire.API.consumer(C2)"))   # a battery camcorder is not a consumer


class Members(unittest.TestCase):
    def setUp(self):
        self.lua = make("ModA", "ModB")

    def test_owner_then_fallback(self):
        self.assertEqual(self.lua.eval("LiveWireCompat.Profiles.consumerIdOf(obj('desk_1', true))"), "BMachine")
        self.assertEqual(self.lua.eval("LiveWireCompat.Profiles.consumerIdOf(obj('desk_1', false))"), "AMachine")
        self.assertIsNone(self.lua.eval("LiveWireCompat.Profiles.consumerIdOf(obj('other_0'))"))

    def test_each_object_is_billed_by_its_member(self):
        self.assertEqual(self.lua.eval("REGISTERED.VanillaDesk.powerConsumption(obj('desk_1', true))"), 40)
        self.assertEqual(self.lua.eval("REGISTERED.VanillaDesk.powerConsumption(obj('desk_1', false))"), 100)

    def test_switch_and_gates_follow_the_member(self):
        self.assertTrue(self.lua.eval("LiveWireCompat.Switch.switchable(obj('desk_0'))"))
        self.assertFalse(self.lua.eval("LiveWireCompat.Switch.switchable(obj('desk_1', true))"))
        self.lua.execute("A = obj('desk_0'); A.cut = true; B = obj('desk_1', true); B.cut = true")
        self.assertFalse(self.lua.eval("Tool.isPowered(A)"))
        self.assertTrue(self.lua.eval("Tool.isPowered(B)"))   # B's machine is not gated by A's check

    def test_switched_off_member_draws_nothing(self):
        self.lua.execute("A = obj('desk_0'); A:getModData().LWC_off = true")
        self.assertEqual(self.lua.eval("REGISTERED.VanillaDesk.powerConsumption(A)"), 0)


if __name__ == "__main__":
    unittest.main()
