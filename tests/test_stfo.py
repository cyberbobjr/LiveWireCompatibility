"""Offline tests of the STFO 3T profile (ADR-005, D04), embedded Lua 5.1 (pip install lupa).

Doubles keep the shape of the target code (read-only Workshop copy 3838240933, mods/STFO/42):
- SimpleTraps.hasMains(square) (shared/SimpleTraps.lua:225-228), SimpleTraps.battery(obj) (:266-279,
  best car battery in the object's container and its charge), SimpleTraps.power(obj) (:282-288,
  "mains", "battery" + battery + charge, or nil + battery + charge);
- SimpleTraps.sensorPowered(sensor) (:502-505, mains only), SimpleTraps.isOn(obj) (:914-916, ModData
  SimpleTrapsOn), floodOn / turretOn (:878-881, :900-902);
- SimpleTraps.serverSwitch(player, args) (server/SimpleTrapsServer.lua:901-933): the stand or turret on
  the square args.x/y/z; args.angle aims a floodlight, args.on switches it.
Run: python tests/test_stfo.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

TARGET = r"""
-- World: squares by "x,y,z"; each holds objects, engine electricity and maybe a room.
SQUARES = {}
local function list(t)
    return { size = function() return #t end, get = function(_, i) return t[i + 1] end }
end
function getCell()
    return { getGridSquare = function(_, x, y, z) return SQUARES[x .. "," .. y .. "," .. z] end }
end
function newSquare(x, y, z, elec)
    local sq = { x = x, y = y, z = z, elec = elec, objects = {} }
    function sq:getX() return self.x end
    function sq:getY() return self.y end
    function sq:getZ() return self.z end
    function sq:haveElectricity() return self.elec == true end
    function sq:getRoom() return nil end
    function sq:getObjects() return list(self.objects) end
    SQUARES[x .. "," .. y .. "," .. z] = sq
    return sq
end
-- A car battery item (CarBattery1..3) with its charge.
local nextId = 0
function carBattery(charge)
    nextId = nextId + 1
    local id = nextId
    return { getType = function() return "CarBattery1" end, getCurrentUsesFloat = function() return charge end,
             getID = function() return id end }
end
-- A placed STFO object: sprite, profile consumer id (nil = not one of ours), square, battery inside.
function placed(sprite, cid, elec, opts)
    opts = opts or {}
    local sq = newSquare(opts.x or 10, opts.y or 10, 0, elec)
    local o = machine(cid, opts.cut, sprite)
    o.sq = sq
    if opts.off then o:getModData().LWC_off = true end
    if opts.on then o:getModData().SimpleTrapsOn = true end
    local items = {}
    if opts.charge then items[1] = carBattery(opts.charge) end
    o.container = { getItems = function() return list(items) end }
    function o:getContainer() return self.container end
    table.insert(sq.objects, o)
    return o
end

-- STFO 3T (shared/SimpleTraps.lua), same rules and returns.
SimpleTraps = {}
SimpleTraps.FLOOD_STANDS = { simpletraps_01_54 = true, simpletraps_01_114 = true, simpletraps_01_151 = true,
    simpletraps_01_115 = true, simpletraps_01_116 = true, simpletraps_01_117 = true, simpletraps_01_118 = true }
SimpleTraps.TURRET_BASE = "simpletraps_01_55"
function SimpleTraps.spriteName(obj)
    local sprite = obj and obj:getSprite()
    return sprite and sprite:getName() or nil
end
GRID_ON = false
function SimpleTraps.hasMains(square)
    HAS_MAINS_CALLS = (HAS_MAINS_CALLS or 0) + 1
    if square:haveElectricity() then return true end
    return square:getRoom() ~= nil and GRID_ON
end
function SimpleTraps.batteryCharge(energizer, battery) return battery:getCurrentUsesFloat() end
function SimpleTraps.battery(energizer)
    local container = energizer:getContainer()
    if not container then return nil, 0 end
    local items = container:getItems()
    local best, bestCharge = nil, 0
    for i = 0, items:size() - 1 do
        local item = items:get(i)
        local t = item:getType()
        if t and t:sub(1, 10) == "CarBattery" and t ~= "CarBatteryCharger" then
            local charge = SimpleTraps.batteryCharge(energizer, item)
            if charge > bestCharge then best, bestCharge = item, charge end
        end
    end
    return best, bestCharge
end
function SimpleTraps.power(energizer)
    local square = energizer:getSquare()
    if square and SimpleTraps.hasMains(square) then return "mains" end
    local battery, charge = SimpleTraps.battery(energizer)
    if battery and charge > 0 then return "battery", battery, charge end
    return nil, battery, charge
end
function SimpleTraps.sensorPowered(sensor)
    local square = sensor:getSquare()
    return square ~= nil and SimpleTraps.hasMains(square)
end
function SimpleTraps.isOn(obj)
    return obj:hasModData() and obj:getModData().SimpleTrapsOn == true
end
function SimpleTraps.isFloodStand(name) return name ~= nil and SimpleTraps.FLOOD_STANDS[name] ~= nil end
local function objectWithSprite(square, wanted)
    if not square then return nil end
    local objects = square:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = SimpleTraps.spriteName(obj)
        if name and wanted(name) then return obj end
    end
    return nil
end
function SimpleTraps.floodOn(square)
    return objectWithSprite(square, function(n) return SimpleTraps.FLOOD_STANDS[n] ~= nil end)
end
function SimpleTraps.turretOn(square)
    return objectWithSprite(square, function(n) return n == SimpleTraps.TURRET_BASE end)
end
-- server/SimpleTrapsServer.lua:901-933 (the head turning left out).
function SimpleTraps.serverSwitch(player, args)
    local x, y, z = tonumber(args.x), tonumber(args.y), tonumber(args.z)
    if not (x and y and z) then return end
    local square = getCell():getGridSquare(x, y, z)
    local obj = SimpleTraps.floodOn(square) or SimpleTraps.turretOn(square)
    if not obj then return end
    if args.angle then
        obj:getModData().SimpleTrapsAngle = tonumber(args.angle)
        obj:transmitModData()
    end
    if args.on ~= nil then
        obj:getModData().SimpleTrapsOn = (args.on == true) or nil
        obj:transmitModData()
    end
end
-- Callers as STFO writes them: the gate box (server:263), the turret (server:1243), the battery
-- drain (server:98-99).
function boxWorks(box) return SimpleTraps.power(box) ~= nil end
function drainsBattery(obj) return SimpleTraps.power(obj) == "battery" end

ACTIVE.STFO = true
"""

SWITCHED = ("STFOFenceEnergizer", "STFOMotionSensor", "STFOGateBox")
OWN_SWITCH = ("STFOFloodlight", "STFOWorkLight", "STFOTowerSearchlight", "STFOTurret")
SPRITES = {
    "STFOFenceEnergizer": ["simpletraps_01_6"],
    "STFOMotionSensor": ["simpletraps_01_27"],
    "STFOGateBox": ["simpletraps_01_28", "simpletraps_01_50", "simpletraps_01_51", "simpletraps_01_52"],
    "STFOFloodlight": ["simpletraps_01_54"],
    "STFOWorkLight": ["simpletraps_01_151"],
    "STFOTowerSearchlight": ["simpletraps_01_114", "simpletraps_01_115", "simpletraps_01_116",
                             "simpletraps_01_117", "simpletraps_01_118"],
    "STFOTurret": ["simpletraps_01_55"],
}


def make(side="sp"):
    lua = tp.make(active=False)
    lua.execute(TARGET)
    lua.execute('SIDE = "%s"' % side)
    tpf.load_all(lua)
    lua.execute("fire()")
    return lua


class Consumers(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_every_device_is_registered_with_its_sprites(self):
        for cid, sprites in SPRITES.items():
            got = list(self.lua.eval("REGISTERED.%s.sprites" % cid).values())
            self.assertEqual(got, sprites, cid)

    def test_switch_only_on_devices_without_their_own(self):
        for cid in SWITCHED:
            self.assertTrue(self.lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)
        for cid in OWN_SWITCH:
            self.assertFalse(self.lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)

    def draw(self, cid, sprite, elec, opts="{}"):
        return self.lua.eval("REGISTERED.%s.powerConsumption(placed('%s', '%s', %s, %s))"
                             % (cid, sprite, cid, "true" if elec else "false", opts))

    def test_switchless_devices_draw_on_mains_only_and_not_switched_off(self):
        for cid in SWITCHED:
            sprite = SPRITES[cid][0]
            self.assertGreater(self.draw(cid, sprite, True), 0, cid)
            self.assertEqual(self.draw(cid, sprite, False, "{ charge = 1 }"), 0, cid)
            self.assertEqual(self.draw(cid, sprite, True, "{ off = true }"), 0, cid)

    def test_lights_and_turret_draw_while_on_and_on_mains(self):
        for cid in OWN_SWITCH:
            for sprite in SPRITES[cid]:
                self.assertGreater(self.draw(cid, sprite, True, "{ on = true }"), 0, sprite)
                self.assertEqual(self.draw(cid, sprite, True), 0, sprite)
                self.assertEqual(self.draw(cid, sprite, False, "{ on = true, charge = 1 }"), 0, sprite)

    def test_estimated_watts(self):
        expected = {"STFOFenceEnergizer": 3, "STFOMotionSensor": 2, "STFOGateBox": 5, "STFOFloodlight": 300,
                    "STFOWorkLight": 150, "STFOTowerSearchlight": 300, "STFOTurret": 40}
        for cid, w in expected.items():
            self.assertEqual(self.draw(cid, SPRITES[cid][0], True, "{ on = true }"), w, cid)


class PowerGate(unittest.TestCase):
    """SimpleTraps.power: only "mains" goes through LiveWire; a battery inside still works."""

    def setUp(self):
        self.lua = make()

    def power(self, expr):
        got = self.lua.eval("SimpleTraps.power(%s)" % expr)
        return got if isinstance(got, tuple) else (got,)

    def test_mains_with_livewire_current_stays_mains(self):
        self.assertEqual(self.power("placed('simpletraps_01_6', 'STFOFenceEnergizer', true, { charge = 0.5 })"),
                         ("mains",))

    def test_mains_cut_falls_back_to_a_charged_battery(self):
        self.lua.execute("E = placed('simpletraps_01_6', 'STFOFenceEnergizer', true, { cut = true, charge = 0.4 })")
        source, battery, charge = self.power("E")
        self.assertEqual(source, "battery")
        self.assertEqual(charge, 0.4)
        self.assertTrue(self.lua.eval("drainsBattery(E)"))

    def test_mains_cut_without_battery_is_unpowered(self):
        self.lua.execute("B = placed('simpletraps_01_50', 'STFOGateBox', true, { cut = true })")
        self.assertIsNone(self.power("B")[0])
        self.assertFalse(self.lua.eval("boxWorks(B)"))
        self.lua.execute("F = placed('simpletraps_01_6', 'STFOFenceEnergizer', true, { cut = true, charge = 0 })")
        self.assertIsNone(self.power("F")[0])

    def test_our_switch_off_stops_the_device_even_with_a_charged_battery(self):
        self.lua.execute("B = placed('simpletraps_01_28', 'STFOGateBox', true, { off = true, charge = 1 })")
        self.assertIsNone(self.power("B")[0])
        self.lua.execute("C = placed('simpletraps_01_28', 'STFOGateBox', true, { off = true })")
        self.assertFalse(self.lua.eval("boxWorks(C)"))

    def test_turret_and_floodlight_cut_from_mains(self):
        self.assertIsNone(self.power("placed('simpletraps_01_55', 'STFOTurret', true, { cut = true, on = true })")[0])
        self.assertEqual(self.power("placed('simpletraps_01_115', 'STFOTowerSearchlight', true,"
                                    " { cut = true, on = true, charge = 1 })")[0], "battery")

    def test_battery_answer_and_other_objects_untouched(self):
        self.assertEqual(self.power("placed('simpletraps_01_6', 'STFOFenceEnergizer', false, { cut = true, charge = 0.3 })")[0],
                         "battery")
        self.assertEqual(self.power("placed('simpletraps_01_6', nil, true, { cut = true })"), ("mains",))

    def test_no_recursion_when_livewire_asks_the_draw_while_gating(self):
        # A LiveWire that measures the draw inside consumerPowered must not loop through the gate.
        self.lua.execute("""
            local base = LiveWire.API.consumerPowered
            LiveWire.API.consumerPowered = function(o)
                REGISTERED[o.cid].powerConsumption(o)
                return base(o)
            end""")
        self.assertEqual(self.power("placed('simpletraps_01_54', 'STFOFloodlight', true, { cut = true, on = true })")[0],
                         None)


class SensorGate(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_sensor_needs_livewire_current_and_our_switch(self):
        self.assertTrue(self.lua.eval("SimpleTraps.sensorPowered(placed('simpletraps_01_27', 'STFOMotionSensor', true))"))
        self.assertFalse(self.lua.eval(
            "SimpleTraps.sensorPowered(placed('simpletraps_01_27', 'STFOMotionSensor', true, { cut = true }))"))
        self.assertFalse(self.lua.eval(
            "SimpleTraps.sensorPowered(placed('simpletraps_01_27', 'STFOMotionSensor', true, { off = true }))"))
        self.assertFalse(self.lua.eval("SimpleTraps.sensorPowered(placed('simpletraps_01_27', 'STFOMotionSensor', false))"))


class SwitchNotify(unittest.TestCase):
    """STFO's own switch (serverSwitch) is reported to LiveWire (ADR-004), aiming alone is not."""

    def switch(self, lua, args):
        lua.execute("SimpleTraps.serverSwitch(nil, %s)" % args)

    def test_switching_a_light_or_turret_is_reported(self):
        for side in ("sp", "server"):
            lua = make(side)
            lua.execute("L = placed('simpletraps_01_151', 'STFOWorkLight', true, { x = 3, y = 4 })")
            self.switch(lua, "{ x = 3, y = 4, z = 0, on = true }")
            self.assertTrue(lua.eval("SimpleTraps.isOn(L)"), side)
            self.assertEqual(lua.eval("#CHANGED"), 1, side)
            self.assertTrue(lua.eval("CHANGED[1] == L"), side)
            lua.execute("T = placed('simpletraps_01_55', 'STFOTurret', true, { x = 5, y = 4 })")
            self.switch(lua, "{ x = 5, y = 4, z = 0, on = true }")
            self.assertTrue(lua.eval("CHANGED[2] == T"), side)

    def test_aiming_without_switching_is_not_reported(self):
        lua = make()
        lua.execute("L = placed('simpletraps_01_54', 'STFOFloodlight', true, { x = 3, y = 4, on = true })")
        self.switch(lua, "{ x = 3, y = 4, z = 0, on = true }")
        self.switch(lua, "{ x = 3, y = 4, z = 0, angle = 45 }")
        self.assertEqual(lua.eval("#CHANGED"), 1)
        self.switch(lua, "{ x = 3, y = 4, z = 0, on = false }")
        self.assertEqual(lua.eval("#CHANGED"), 2)

    def test_bad_arguments_still_reach_stfo(self):
        lua = make()
        self.switch(lua, "{ x = 99, y = 99, z = 0, on = true }")
        self.switch(lua, "{}")
        self.assertEqual(lua.eval("#CHANGED"), 0)

    def test_not_installed_on_a_multiplayer_client(self):
        lua = make("client")
        lua.execute("L = placed('simpletraps_01_54', 'STFOFloodlight', true, { x = 3, y = 4 })")
        self.switch(lua, "{ x = 3, y = 4, z = 0, on = true }")
        self.assertEqual(lua.eval("#CHANGED"), 0)


if __name__ == "__main__":
    unittest.main()
