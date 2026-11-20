"""Offline tests of the Knox Working Machines profile (ADR-005, D02, D03), embedded Lua 5.1 (pip install lupa).

Doubles keep the shape of the target code (read-only Workshop copy 3841890337, variant 42) and of vanilla 42.22:
- every Knox machine is a vanilla tile turned into a GameEntity whose script is named KWM_*
  (scripts/entities/KWM_entities*.txt; GameEntity.getEntityScript, GameEntityScript.getName);
- ISEntityUI.CanOpenWindowFor(_player, _entity) (client/Entity/ISEntityUI.lua:333), already wrapped by
  Knox at file load with its own square test (client/KWM_PowerGate.lua:92-103);
- ISHandcraftAction (shared/Entity/TimedActions/ISHandcraftAction.lua:5-15, :395-402), the bench in
  `isoObject`, its CraftBench component in `craftBench`;
- the car-wash option addOption(name, playerObj, onWash, washer, vehicle) (client/KWM_CarWashMenu.lua:57);
- Machinery keeps its state in ModData movableData.Machinery (Machinery shared/Machinery/Service.lua:349-365).
LiveWire resolves an object by its sprite (one consumer per sprite, shared tiles registered once).
Run: python tests/test_knox.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

KNOX = r"""
HALO = {}
function hero() return { setHaloNote = function(self, text) HALO[#HALO + 1] = text end } end
ELEC = true
-- LiveWire double: an object is resolved by its sprite to the consumer that registered it.
BY_SPRITE = {}
local register = LiveWire.API.registerConsumer
function LiveWire.API.registerConsumer(id, def)
    local ok, why = register(id, def)
    if ok then for _, s in ipairs(def.sprites) do BY_SPRITE[s] = id end end
    return ok, why
end
function LiveWire.API.consumer(o) return type(o) == "table" and BY_SPRITE[o.sprite] or nil end
-- Placed vanilla tile; `entity` is the name of its entity script (nil: no entity attached).
function station(sprite, entity, cut, off)
    local o = setmetatable({ sprite = sprite, cut = cut }, getmetatable(machine('x')))
    if off then o:getModData().LWC_off = true end
    o.getEntityScript = function()
        if not entity then return nil end
        return { getName = function() return entity end }
    end
    o.isUsingPlayer = function() return true end
    o.sq = { haveElectricity = function() return ELEC end, hasGridPower = function() return false end,
             getX = function() return 0 end, getY = function() return 0 end, getZ = function() return 0 end }
    return o
end
function machineryPlaced(o) o:getModData().movableData = { Machinery = { machineId = "drillPress", parts = {} } }; return o end
function draw(o) return REGISTERED[BY_SPRITE[o.sprite]].powerConsumption(o) end

-- Vanilla ISEntityUI.CanOpenWindowFor (client/Entity/ISEntityUI.lua:333-370), reduced to its answer.
ISEntityUI = {}
function ISEntityUI.CanOpenWindowFor(_player, _entity)
    if _entity == nil then return false end
    return true
end
-- Knox's wrapper at file load (client/KWM_PowerGate.lua:92-103).
local original = ISEntityUI.CanOpenWindowFor
function ISEntityUI.CanOpenWindowFor(player, entity)
    if entity and entity.getSprite and entity:getSprite() then
        local square = entity:getSquare()
        if not square or not (square:haveElectricity() or square:hasGridPower()) then return false end
    end
    return original(player, entity)
end

-- ISBaseTimedAction / ISHandcraftAction (shared/Entity/TimedActions/ISHandcraftAction.lua).
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
ISHandcraftAction = ISBaseTimedAction:derive("ISHandcraftAction")
function ISHandcraftAction:isValid()
    if self.craftBench then
        if (not self.isoObject) or (not self.isoObject:isUsingPlayer(self.character)) then return false end
    end
    if (not self.craftRecipe) then return false end
    return true
end
function ISHandcraftAction:new(character, craftRecipe, containers, isoObject, craftBench)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.character = character
    o.craftRecipe = craftRecipe
    o.isoObject = isoObject
    o.craftBench = craftBench
    return o
end
function craft(bench) return ISHandcraftAction:new(hero(), {}, nil, bench, bench and {} or nil) end

-- Machinery (shared/Machinery/Service.lua:128-134).
Machinery = { Service = {} }
function Machinery.Service.isPowered(object)
    local square = object and object:getSquare()
    return square ~= nil and square:haveElectricity() == true
end

-- Context menu (ISContextMenu fields) and the car-wash option (client/KWM_CarWashMenu.lua:50-67).
ISWorldObjectContextMenu = { addToolTip = function() return { setName = function(self, n) self.name = n end } end }
function menu()
    local c = { options = {}, numOptions = 1 }
    function c:addOption(name, target, onSelect, p1, p2)
        local o = { name = name, target = target, onSelect = onSelect, param1 = p1, param2 = p2 }
        self.options[self.numOptions] = o
        self.numOptions = self.numOptions + 1
        return o
    end
    function c:getSubMenu() return nil end
    return c
end
function washMenu(washer)
    local ctx = menu()
    WASH = ctx:addOption("ContextMenu_KWM_CarWash", hero(), print, washer, {})
    trigger("OnFillWorldObjectContextMenu", 0, ctx, { washer }, false)
    return WASH
end
"""


def make(side="client", mods=("KnoxWorkingMachines",)):
    lua = tp.make(active=False)
    lua.execute(KNOX)
    lua.execute('SIDE = "%s"' % side)
    for m in mods:
        lua.execute("ACTIVE.%s = true" % m)
    tpf.load_all(lua)
    lua.execute("fire()")
    return lua


# Every electric Knox machine: one sprite, its entity script, and the draw of that tile.
MACHINES = {
    "industry_02_268": ("KWM_DrillPress", 100),
    "industry_02_152": ("KWM_TableSaw", 375),
    "industry_03_0": ("KWM_LatheGreen_1", 42),
    "industry_03_1": ("KWM_LatheGreen_1", 42),
    "industry_03_33": ("KWM_LatheBlue_1", 42),
    "industry_03_48": ("KWM_Mill_1", 47),
    "industry_03_60": ("KWM_Mill_4", 47),
    "industry_02_46": ("KWM_HydraulicPress", 188),
    "industry_04_20": ("KWM_BenchGrinder", 93),
    "industry_02_163": ("KWM_Charger_1", 38),
    "industry_02_49": ("KWM_Cannery_1", 150),
    "location_business_machinery_01_0": ("KWM_CarLift_1", 188),
    "location_business_machinery_01_6": (None, 125),
    "location_business_machinery_01_37": (None, 125),
}


class Billing(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_each_machine_draws_its_share_and_nothing_switched_off(self):
        for sprite, (entity, watts) in MACHINES.items():
            ent = "'%s'" % entity if entity else "nil"
            self.assertEqual(self.lua.eval("draw(station('%s', %s))" % (sprite, ent)), watts, sprite)
            self.assertEqual(self.lua.eval("draw(station('%s', %s, false, true))" % (sprite, ent)), 0, sprite)

    def test_every_machine_has_our_switch(self):
        for sprite, (entity, _) in MACHINES.items():
            ent = "'%s'" % entity if entity else "nil"
            self.assertTrue(self.lua.eval("LiveWireCompat.Switch.switchable(station('%s', %s))" % (sprite, ent)),
                            sprite)

    def test_sections_add_up_to_one_machine(self):
        lathe = sum(self.lua.eval("draw(station('industry_03_%d', 'KWM_LatheGreen'))" % i) for i in (0, 4, 10))
        mill = sum(self.lua.eval("draw(station('industry_03_%d', 'KWM_Mill'))" % i) for i in (48, 52, 56, 60))
        self.assertEqual((lathe, mill), (126, 188))

    def test_tiles_shared_with_machinery_are_registered_once(self):
        for shared in ("VanillaDrillPress", "VanillaLathe", "VanillaIndustry03Mill", "VanillaBenchGrinder"):
            self.assertIsNotNone(self.lua.eval("REGISTERED.%s" % shared), shared)
        self.assertIsNone(self.lua.eval("REGISTERED.KnoxDrillPress"))

    def test_shared_tile_without_a_knox_entity_is_not_billed(self):
        self.assertEqual(self.lua.eval("draw(station('industry_02_268', nil))"), 0)

    def test_non_electric_stations_are_not_billed(self):
        for sprite in ("industry_03_24", "industry_03_80", "industry_04_0", "location_business_machinery_01_16"):
            self.assertIsNone(self.lua.eval("BY_SPRITE['%s']" % sprite), sprite)


class WithMachinery(unittest.TestCase):
    """Both mods give a use to the same vanilla tiles (ADR-005, D02)."""

    def setUp(self):
        self.lua = make(mods=("KnoxWorkingMachines", "Machinery"))

    def owner(self, code):
        return self.lua.eval("LiveWireCompat.Profiles.consumerIdOf(%s)" % code)

    def test_knox_entity_is_knox(self):
        self.assertEqual(self.owner("station('industry_02_268', 'KWM_DrillPress')"), "KnoxDrillPress")
        self.assertEqual(self.owner("station('industry_03_48', 'KWM_Mill_1')"), "KnoxMill")
        self.assertEqual(self.lua.eval("draw(station('industry_03_48', 'KWM_Mill_1'))"), 47)

    def test_machine_with_machinery_state_is_machinery_even_with_a_knox_entity(self):
        self.assertEqual(self.owner("machineryPlaced(station('industry_02_268', 'KWM_DrillPress'))"),
                         "MachineryDrillPress")
        self.assertEqual(self.lua.eval("draw(machineryPlaced(station('industry_03_48', 'KWM_Mill_1')))"), 300)

    def test_tile_of_neither_falls_back_to_machinery(self):
        self.assertEqual(self.owner("station('industry_04_20', nil)"), "MachineryBenchGrinder")
        self.assertEqual(self.lua.eval("draw(station('industry_03_1', nil))"), 200)

    def test_knox_window_does_not_gate_a_machinery_machine(self):
        self.assertTrue(self.lua.eval(
            "ISEntityUI.CanOpenWindowFor(hero(), machineryPlaced(station('industry_02_268', 'KWM_DrillPress', true)))"))

    def test_machinery_gate_still_gates_its_machines(self):
        self.assertFalse(self.lua.eval(
            "Machinery.Service.isPowered(machineryPlaced(station('industry_02_268', 'KWM_DrillPress', true)))"))


class MachineryAlone(unittest.TestCase):
    def test_every_vanilla_tile_stays_a_machinery_machine(self):
        lua = make(mods=("Machinery",))
        self.assertEqual(lua.eval("LiveWireCompat.Profiles.consumerIdOf(station('industry_02_268', nil))"),
                         "MachineryDrillPress")
        self.assertEqual(lua.eval("draw(station('industry_02_268', nil))"), 150)
        self.assertEqual(lua.eval("draw(station('industry_03_52', nil))"), 300)


class Window(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_unpowered_station_window_does_not_open(self):
        self.assertFalse(self.lua.eval("ISEntityUI.CanOpenWindowFor(hero(), station('industry_02_152', 'KWM_TableSaw', true))"))
        self.assertFalse(self.lua.eval(
            "ISEntityUI.CanOpenWindowFor(hero(), station('industry_02_152', 'KWM_TableSaw', false, true))"))

    def test_powered_station_window_opens(self):
        self.assertTrue(self.lua.eval("ISEntityUI.CanOpenWindowFor(hero(), station('industry_02_152', 'KWM_TableSaw'))"))

    def test_no_engine_power_keeps_knox_answer(self):
        self.lua.execute("ELEC = false")
        self.assertFalse(self.lua.eval("ISEntityUI.CanOpenWindowFor(hero(), station('industry_02_152', 'KWM_TableSaw'))"))

    def test_other_entities_are_untouched(self):
        self.assertTrue(self.lua.eval("ISEntityUI.CanOpenWindowFor(hero(), station('crafted_01_32', 'KWM_FuelDrum_Metal', true))"))


class Crafting(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_unpowered_bench_stops_the_craft_and_tells_why(self):
        self.lua.execute("A = craft(station('industry_03_4', 'KWM_LatheGreen_2', false, true))")
        self.assertFalse(self.lua.eval("A:isValidStart()"))
        self.assertFalse(self.lua.eval("A:isValid()"))
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_power_cut_stops_a_craft_in_progress(self):
        self.lua.execute("B = station('industry_02_268', 'KWM_DrillPress'); A = craft(B)")
        self.assertTrue(self.lua.eval("A:isValid()"))
        self.lua.execute("B.cut = true")
        self.assertFalse(self.lua.eval("A:isValid()"))

    def test_other_crafts_are_untouched(self):
        self.assertTrue(self.lua.eval("craft(nil):isValid()"))
        self.assertTrue(self.lua.eval("craft(station('industry_03_80', 'KWM_ViseBenchMetal_1', true)):isValid()"))

    def test_dedicated_server_keeps_the_original(self):
        lua = make("server")
        self.assertTrue(lua.eval("craft(station('industry_02_268', 'KWM_DrillPress', true)):isValid()"))


class CarWash(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_unpowered_washer_greys_the_wash(self):
        self.assertTrue(self.lua.eval("washMenu(station('location_business_machinery_01_6', nil, true)).notAvailable"))
        self.assertTrue(self.lua.eval(
            "washMenu(station('location_business_machinery_01_36', nil, false, true)).notAvailable"))

    def test_powered_washer_washes(self):
        self.assertIsNone(self.lua.eval("washMenu(station('location_business_machinery_01_14', nil)).notAvailable"))


if __name__ == "__main__":
    unittest.main()
