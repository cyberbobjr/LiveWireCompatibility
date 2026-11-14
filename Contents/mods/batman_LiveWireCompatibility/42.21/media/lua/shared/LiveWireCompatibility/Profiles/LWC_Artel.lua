-- LiveWire Compatibility: Artel Manufactory (Workshop 3794133594, mod id ArtelManufactory).
-- Analysis: docs/annexes/recherches/artel-manufactory.md. Artel states no power figure: every
-- draw below is an estimate (ADR-001, D03). Already counted by the game, so not here: the
-- portable electric stove (IsoStove) and the smart floodlights (IsoLightSwitch). Not placed in
-- the world, so not billable: battery charging station, electric heater, cooler bag.
require "LiveWireCompatibility/LWC_Profiles"

local function artel(name)
    local t = PMK and PMK[name]
    return type(t) == "table" and t or nil
end

local function range(from, to, out)
    out = out or {}
    for i = from, to do out[#out + 1] = "Artel_" .. i end
    return out
end

-- Quantum Base: lit sprites only (dark clones mean "no power", PMK_87c_QuantumBaseCore.lua:52-62).
local quantum = range(112, 116)
range(125, 129, quantum)
range(134, 138, quantum)
quantum[#quantum + 1] = "Artel_143"  -- north face: one sprite for lit and dark

LiveWireCompat.Profiles.add({
    name = "Artel",
    workshop = "3794133594",
    mods = { "ArtelManufactory" },
    consumers = {
        -- Well, motor stage only (the hand pump and the pipe stages use other sprites).
        -- 500 W pump, about one hour in five: average 100 W.
        { id = "ArtelWellMotor", sprites = { "Artel_104", "Artel_107" }, watts = 100 },
        -- Electric dryer: 2 kW heater used in batches; its running state is not readable
        -- from the object: average 300 W. Drying stages are overlays on these base sprites.
        { id = "ArtelElectricDryer", sprites = { "Artel_36", "Artel_37" }, watts = 300 },
        -- Freeze dryer: 700 W during a cycle, state not readable: average 150 W.
        { id = "ArtelSublimator", sprites = { "Artel_52", "Artel_53" }, watts = 150 },
        -- Chemistry table: heated only while crafting, state not readable: average 30 W.
        { id = "ArtelChemTable", sprites = { "Artel_56" }, watts = 30 },
        -- Trade post: two halves per post, 75 W each (150 W) while on grid power; on its own
        -- battery it draws nothing from the network.
        { id = "ArtelTradePost", sprites = { "Artel_121", "Artel_122", "Artel_123", "Artel_124" }, watts = 75,
          running = function(o)
              local t = artel("Trade")
              return t ~= nil and t.powerSource ~= nil and t.powerSource(o) == "grid"
          end },
        -- Quantum Base wall module: always-on storage field, 100 W while lit.
        { id = "ArtelQuantumBase", sprites = quantum, watts = 100,
          running = function(o)
              local qb = artel("QBase")
              return qb ~= nil and qb.hasPower ~= nil and qb.hasPower(o) == true
          end },
    },
    -- Public power checks: a cut circuit stops these machines (the others keep running).
    gates = {
        { path = "PMK.Well.isPowered", kind = "object", consumer = "ArtelWellMotor" },
        { path = "PMK.Trade.gridPowered", kind = "object", consumer = "ArtelTradePost" },
        { path = "PMK.QBase.squarePowered", kind = "square", consumer = "ArtelQuantumBase" },
    },
})
