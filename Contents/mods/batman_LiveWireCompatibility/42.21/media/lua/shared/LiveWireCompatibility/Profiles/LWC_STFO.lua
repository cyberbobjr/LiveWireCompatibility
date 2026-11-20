-- LiveWire Compatibility: STFO 3T: Traps, Turrets and Towers (Workshop 3838240933, mod id STFO).
-- Analysis: docs/annexes/recherches/stfo-3t.md. ADR-005, D04: an STFO device runs on the mains OR on
-- a car battery put inside it; only the MAINS goes through LiveWire (billed, cut off), a battery
-- inside keeps working. Paths below are under mods/STFO/42/media/lua.
-- Billed: the stand / base that holds the battery, switch and aim of each device (one object per
-- device). The heads that turn (floodlight 34-41, tower searchlight 119-150, work light 152-159,
-- turret 42-49, 56-63, 70-109) are separate plain objects on the same tile (shared/SimpleTraps.lua:
-- 818-820) and are not billed; neither are the electric fence pieces (3-5), powered by the
-- energizer. The tower searchlight's stand is its parapet mount (115-118, one per tower facing,
-- :668-680, :828-830); the holder 114 built from the menu is swapped for the mount at the next
-- server tick (server/SimpleTrapsServer.lua:790-834), both are listed. Gate box: one sprite per
-- facing S, E, N, W (shared/SimpleTraps.lua:516-517).
-- Draw (estimates, while on the mains): fence energizer 3 W (small mains energizer of the 1990s),
-- motion sensor 2 W (PIR detector and its transformer), gate control box 5 W at rest (controller
-- board and receiver), floodlight on a stand 300 W and tower searchlight 300 W (halogen floodlight),
-- work light 150 W (halogen work lamp), turret 40 W on standby (camera-less servo base and its
-- electronics).
-- Switches: energizer, motion sensor and gate box have none: they get ours (ADR-002, D01). The
-- floodlight, work light, tower searchlight and turret have their own (ModData SimpleTrapsOn,
-- shared/SimpleTraps.lua:914-916), reported to LiveWire (ADR-004).
require "LiveWireCompatibility/LWC_Profiles"

local SWITCHED_BY_STFO = { "STFOFloodlight", "STFOWorkLight", "STFOTowerSearchlight", "STFOTurret" }
local POWERED = { "STFOFenceEnergizer", "STFOGateBox", "STFOFloodlight", "STFOWorkLight",
                  "STFOTowerSearchlight", "STFOTurret" }

-- STFO would take this device's power from the mains (shared/SimpleTraps.lua:225-228, the test
-- SimpleTraps.power makes first, :284). Not the gated SimpleTraps.power: LiveWire may ask the draw
-- while a gate asks LiveWire.
local function onMains(o)
    local square = o:getSquare()
    return square ~= nil and SimpleTraps.hasMains(square) == true
end

-- Switched on by its own switch and fed from the mains.
local function onAndOnMains(o)
    return SimpleTraps.isOn(o) == true and onMains(o)
end

-- SimpleTraps.power(obj) blocked by LiveWire: what STFO answers without the mains. A battery inside
-- with charge still works (SimpleTraps.battery, shared/SimpleTraps.lua:266-279, the same returns as
-- power's battery branch, :285-287); else nil.
-- Switched off with our switch (energizer, sensor, gate box): the device does not work at all, battery
-- or not (ADR-002, D01).
local function withoutMains(original, obj, ...)
    if LiveWireCompat.Switch.isOff(obj) then return nil end
    local source, battery, charge = original(obj, ...)
    if source ~= "mains" then return source, battery, charge end
    battery, charge = SimpleTraps.battery(obj)
    if battery and charge > 0 then return "battery", battery, charge end
    return nil, battery, charge
end

-- The stand or turret serverSwitch acts on (server/SimpleTrapsServer.lua:902-905).
local function switchedMachine(player, args)
    if type(args) ~= "table" then return nil end
    local x, y, z = tonumber(args.x), tonumber(args.y), tonumber(args.z)
    if not (x and y and z) then return nil end
    local square = getCell():getGridSquare(x, y, z)
    if not square then return nil end
    return SimpleTraps.floodOn(square) or SimpleTraps.turretOn(square)
end

local function isOn(o)
    return SimpleTraps.isOn(o) == true
end

LiveWireCompat.Profiles.add({
    name = "STFO",
    workshop = "3838240933",
    mods = { "STFO" },
    consumers = {
        { id = "STFOFenceEnergizer", sprites = { "simpletraps_01_6" }, watts = 3, switch = true,
          running = onMains },
        { id = "STFOMotionSensor", sprites = { "simpletraps_01_27" }, watts = 2, switch = true,
          running = onMains },
        { id = "STFOGateBox", watts = 5, switch = true, running = onMains,
          sprites = { "simpletraps_01_28", "simpletraps_01_50", "simpletraps_01_51", "simpletraps_01_52" } },
        { id = "STFOFloodlight", sprites = { "simpletraps_01_54" }, watts = 300, running = onAndOnMains,
          category = "light", circuit = "light" },
        { id = "STFOWorkLight", sprites = { "simpletraps_01_151" }, watts = 150, running = onAndOnMains,
          category = "light", circuit = "light" },
        { id = "STFOTowerSearchlight", watts = 300, running = onAndOnMains, category = "light", circuit = "light",
          sprites = { "simpletraps_01_114", "simpletraps_01_115", "simpletraps_01_116", "simpletraps_01_117",
                      "simpletraps_01_118" } },
        { id = "STFOTurret", sprites = { "simpletraps_01_55" }, watts = 40, running = onAndOnMains },
    },
    gates = {
        -- shared/SimpleTraps.lua:282-288, power(obj), the device as argument 1: "mains", "battery" +
        -- battery + charge, or nil. Read as SimpleTraps.power at each call by the fence
        -- (findEnergizer :301, fenceEnergizer :1070), the battery drain (server/SimpleTrapsServer.lua:99),
        -- the gate box (server:263), the turret's shot (server:1243), the floodlight beam (client/
        -- SimpleTrapsClient.lua:450) and the status lines (shared:585, client:1201, :1356, :1507).
        -- Shared: client and server both decide with it. Blocked: the mains answer falls back to the
        -- battery inside (ADR-005, D04).
        { kind = "call", path = "SimpleTraps.power", consumer = POWERED, instead = withoutMains },
        -- shared/SimpleTraps.lua:502-505, sensorPowered(sensor), mains only, the sensor as argument 1;
        -- read by the server's alarm (server/SimpleTrapsServer.lua:173) and the client's watch and
        -- menu (client/SimpleTrapsClient.lua:452, :1686).
        { kind = "object", path = "SimpleTraps.sensorPowered", consumer = "STFOMotionSensor" },
        -- server/SimpleTrapsServer.lua:901-933, serverSwitch(player, args): switches (args.on) or aims
        -- (args.angle) the stand or turret on square args.x, args.y, args.z. Run by the server on the
        -- client command (server:1365-1366) and, in single player, by the client directly
        -- (client/SimpleTrapsClient.lua:132-133), which reads the global at call time: side "server"
        -- covers both. Only a change of SimpleTrapsOn is reported (aiming is not).
        { kind = "notify", path = "SimpleTraps.serverSwitch", consumer = SWITCHED_BY_STFO, side = "server",
          machine = switchedMachine, state = isOn },
    },
})
