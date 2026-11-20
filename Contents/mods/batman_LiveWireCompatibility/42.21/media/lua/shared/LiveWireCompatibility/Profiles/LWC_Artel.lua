-- LiveWire Compatibility: Artel Manufactory (Workshop 3794133594, mod id ArtelManufactory).
-- Analysis: docs/annexes/recherches/artel-manufactory.md; switch and gates: ADR-002 (D06).
-- Artel states no power figure: every draw below is an estimate (ADR-001, D03). Already counted by
-- the game, so not here: the portable electric stove (IsoStove) and the smart floodlights
-- (IsoLightSwitch). Not placed in the world, so not billable: battery charging station, electric
-- heater, cooler bag. Target lines below: variant 42/, media/lua/<side>/<file>.
require "LiveWireCompatibility/LWC_Profiles"
require "LiveWireCompatibility/LWC_SourcePatch"

local function artel(name)
    local t = PMK and PMK[name]
    return type(t) == "table" and t or nil
end

local function range(from, to, out)
    out = out or {}
    for i = from, to do out[#out + 1] = "Artel_" .. i end
    return out
end

-- Quantum Base: lit sprites and their dark clones ("no power", shared/PMK_87c_QuantumBaseCore.lua:
-- 52-62). Artel swaps the object between them (QB.rebuild, :562): both must stay the same
-- consumer, or a cut base turned dark would no longer be gated and would light up again.
local quantum = range(112, 120)
range(125, 133, quantum)
range(134, 142, quantum)
quantum[#quantum + 1] = "Artel_143"  -- north face: one sprite for lit and dark

-- Drying stations (dryer, sublimator) keep their batches in a DryingCraftLogic component
-- (server/PMK_58z_SublimatorServer.lua:429-430). The authority reads the batches in progress; the
-- ModData flag PMK_EDryerNoPower (:65, written by setFlag :337 at :467) means Artel holds them for lack of power.
local NO_POWER_FLAG = "PMK_EDryerNoPower"

local function batchRunning(o)
    if not (ComponentType and o.hasComponent and o:hasComponent(ComponentType.DryingCraftLogic)) then
        return false
    end
    local comp = o:getComponent(ComponentType.DryingCraftLogic)
    if not comp or (tonumber(comp:getActiveCraftCount()) or 0) <= 0 then return false end
    return not (o:hasModData() and o:getModData()[NO_POWER_FLAG] == true)
end

-- Batch pause of the drying stations (server). The watchdog (server/PMK_58z:417-475) does, for
-- each station: Pause.thaw(crd) or Pause.freeze(crd) for every batch (:443, Pause = PMK.dryPause
-- read at :417), then the stage global of its kind, looked up in _G (:471-472, KINDS :130-133),
-- which calls PMK_StationApplyStage(obj, comp, cfg) (shared/PMK_54s_ElectricDryerStage.lua:234,
-- :293; shared/PMK_58s_SublimatorStage.lua:55). A batch (CraftRecipeData) does not know its
-- station, so thaw only notes the batch; the stage call of its station then decides: thaw as
-- Artel asked, or freeze (it renews Artel's 6-minute hold lease, shared/PMK_54p_DryingPause.lua:
-- 143, 168-180) while the station is off or cut. Artel's own tick thaws it again once powered.
-- PMK_58z:443 is the only caller of thaw in Artel.
local waiting = {}
local realThaw = nil

local function installDryingPause(gate, G)
    local pause = artel("dryPause")
    if not pause then return false, "gate_not_found" end
    local ids = G.ids(gate)
    local ok, reason = G.wrap("PMK_StationApplyStage", _G, "PMK_StationApplyStage", function(original)
        return function(obj, comp, cfg)
            local blocked = G.blocked(obj, ids)
            local hold = PMK.dryPause.freeze
            for i = 1, #waiting do
                if blocked then hold(waiting[i]) else realThaw(waiting[i]) end
                waiting[i] = nil
            end
            return original(obj, comp, cfg)
        end
    end)
    if not ok then return ok, reason end
    return G.wrap("PMK.dryPause.thaw", pause, "thaw", function(original)
        realThaw = original
        return function(crd)
            if crd then waiting[#waiting + 1] = crd end
        end
    end)
end

-- QB.rebuild(sq, obj, cells, powered, face) replaces the object by a new one
-- (shared/PMK_87c:614-617, IsoObject.getNew) that has none of the old ModData: the switch state
-- goes over to the new object, so a base switched off stays off (dark, cells locked).
local function installQuantumKeepSwitch(gate, G)
    local Switch = LiveWireCompat.Switch
    return G.wrap("PMK.QBase.rebuild", artel("QBase"), "rebuild", function(original)
        return function(sq, obj, ...)
            local wasOff = Switch.isOff(obj)
            local made = original(sq, obj, ...)
            if wasOff and made and made ~= obj then
                Switch.write(made, true)
            end
            return made
        end
    end)
end

-- Sprites Artel draws over a station to show its load (IsoObject:setOverlaySprite,
-- shared/PMK_54s_ElectricDryerStage.lua:257-259, shared/PMK_58s_SublimatorStage.lua:40-42), and the
-- machine sprite each one covers. Read by the depth tools only (ADR-003): an overlay gets the depth
-- of its machine, otherwise it hides the machine's highlight while the station is loaded.
local OVERLAYS = {
    Artel_38 = "Artel_36", Artel_42 = "Artel_36", Artel_39 = "Artel_37", Artel_43 = "Artel_37",
    Artel_48 = "Artel_52", Artel_50 = "Artel_52", Artel_49 = "Artel_53", Artel_51 = "Artel_53",
}

-- Source patch (ADR-006). Artel's drying watchdog decides that a station has power with a local
-- squarePowered(square) (server/PMK_58z_SublimatorServer.lua:82-88): it freezes the batches (:443),
-- writes the "no power" flag of the station window (:467, setFlag :337) and logs it. Our file of the
-- same path (server/PMK_58z_SublimatorServer.lua) runs Artel's own file with that one declaration
-- turned into: Artel's answer AND the station on the square is on and powered by LiveWire. One
-- line in, one line out: Artel's line numbers stay. The effect gates below remain as fallback.
LiveWireCompat.Artel = LiveWireCompat.Artel or {}
local STATIONS = { ArtelElectricDryer = true, ArtelSublimator = true }

function LiveWireCompat.Artel.stationPowered(square, artelAnswer)
    if not artelAnswer(square) then return false end
    local G = LiveWireCompat.Gates
    return not G.blocked(G.machineOn(square, STATIONS), STATIONS)
end

LiveWireCompat.SourcePatch.add({
    mod = "ArtelManufactory",
    path = "media/lua/server/PMK_58z_SublimatorServer.lua",
    edits = { {
        old = "local function squarePowered(square)",
        new = "local lwcArtelSquarePowered; local function squarePowered(square) return "
            .. "LiveWireCompat.Artel.stationPowered(square, lwcArtelSquarePowered) end; "
            .. "function lwcArtelSquarePowered(square)",
    } },
})

LiveWireCompat.Profiles.add({
    name = "Artel",
    workshop = "3794133594",
    overlays = OVERLAYS,
    mods = { "ArtelManufactory" },
    consumers = {
        -- Well, motor stage only (the hand pump and the pipe stages use other sprites).
        -- 500 W pump, about one hour in five: average 100 W.
        { id = "ArtelWellMotor", sprites = { "Artel_104", "Artel_107" }, watts = 100, switch = true },
        -- Electric dryer: 2 kW heater (research doc, section 2.2 item 5) while a batch runs,
        -- 5 W of controls otherwise. Drying stages are overlays on these base sprites
        -- (shared/PMK_54s:225-226), so the base sprite stays.
        { id = "ArtelElectricDryer", sprites = { "Artel_36", "Artel_37" }, watts = 2000, idle = 5,
          switch = true, running = batchRunning },
        -- Freeze dryer: 700 W during a cycle, 5 W standby (research doc, section 2.3 item 5).
        { id = "ArtelSublimator", sprites = { "Artel_52", "Artel_53" }, watts = 700, idle = 5,
          switch = true, running = batchRunning },
        -- Chemistry table, master tile of each face (scripts/PMK_chem_Entity.txt:132-144: S = 56 57,
        -- E = 58 / 59). Heated only while crafting, state not readable: average 30 W.
        { id = "ArtelChemTable", sprites = { "Artel_56", "Artel_58" }, watts = 30, switch = true },
        -- Trade post: two halves per post, 75 W each (150 W) while on grid power; on its own
        -- battery it draws nothing from the network (shared/PMK_91h_TradePower.lua:321-329).
        { id = "ArtelTradePost", sprites = { "Artel_121", "Artel_122", "Artel_123", "Artel_124" }, watts = 75,
          switch = true,
          running = function(o)
              local t = artel("Trade")
              return t ~= nil and t.powerSource ~= nil and t.powerSource(o) == "grid"
          end },
        -- Quantum Base wall module: always-on storage field, 100 W while it has power.
        { id = "ArtelQuantumBase", sprites = quantum, watts = 100, switch = true,
          running = function(o)
              local qb = artel("QBase")
              return qb ~= nil and qb.hasPower ~= nil and qb.hasPower(o) == true
          end },
    },
    gates = {
        -- shared/PMK_80_WellCore.lua:430 isPowered(obj); false = motorIdle speed (:436-440).
        { path = "PMK.Well.isPowered", kind = "object", consumer = "ArtelWellMotor" },
        -- shared/PMK_91h_TradePower.lua:226 gridPowered(obj); false = runs on its battery (:280, :324).
        { path = "PMK.Trade.gridPowered", kind = "object", consumer = "ArtelTradePost" },
        -- shared/PMK_87c:278 squarePowered(sq), looked up in QB at each call by hasPower (:288-291,
        -- used by the cell lock shared/PMK_89a_QuantumPowerLock.lua:85, the client gate
        -- client/PMK_88b:115, the menu client/PMK_88a:219, the actions shared/PMK_88c:194, the cold
        -- ticker PMK_87c:770) AND by the sprite choice (heal :383, rebuild :571). Gating hasPower
        -- alone would lock the cells but never darken the base.
        { path = "PMK.QBase.squarePowered", kind = "square", consumer = "ArtelQuantumBase" },
        { kind = "custom", name = "Artel quantum base switch", consumer = "ArtelQuantumBase", side = "server",
          install = installQuantumKeepSwitch },
        { kind = "custom", name = "Artel drying pause", consumer = { "ArtelElectricDryer", "ArtelSublimator" },
          side = "server", install = installDryingPause },
        -- PMK_StationApplyStage(obj, comp, cfg) runs for each station every game minute on the server
        -- (server/PMK_58z_SublimatorServer.lua:471-472): a batch that starts or ends is reported to
        -- LiveWire, which bills the dryers only during a batch (ADR-004).
        { kind = "notify", path = "PMK_StationApplyStage", consumer = { "ArtelElectricDryer", "ArtelSublimator" },
          state = batchRunning, side = "server" },
        -- Starting a batch ("Dry", "Freeze-dry", steeping): the stations are DryingCraftLogic entities
        -- started from the vanilla craft logic panel through ISEntityUI.GenericCraftStart(player,
        -- entity, ...) or GenericCraftTransferAndStart (client/Entity/ISEntityUI.lua:71-105), which
        -- queue ISGenericCraftStart (shared/Entity/TimedActions/ISGenericCraftStart.lua:5-12, :60-72,
        -- field `entity`). The batch pause above only holds a batch already running: these refuse to
        -- start one on a station switched off or without power, with the reason shown to the player.
        { kind = "call", path = "ISEntityUI.GenericCraftStart", arg = 2, player = 1, side = "client",
          consumer = { "ArtelElectricDryer", "ArtelSublimator", "ArtelChemTable" } },
        { kind = "call", path = "ISEntityUI.GenericCraftTransferAndStart", arg = 2, player = 1, side = "client",
          consumer = { "ArtelElectricDryer", "ArtelSublimator", "ArtelChemTable" } },
        { kind = "action", path = "ISGenericCraftStart", field = "entity", side = "client",
          consumer = { "ArtelElectricDryer", "ArtelSublimator", "ArtelChemTable" } },
        -- Station window (client/PMK_55_ElectricDryerPanel.lua:2586-2597, class :1960; the freeze
        -- dryer's window derives from it, client/PMK_59_SublimatorPanel.lua:27): update() copies
        -- Artel's "no power" flag into pausedFlag, which lights the red lamp, the "Paused" banner
        -- (:2696) and freezes the batch timers (:1206). Artel writes that flag from its own square
        -- check (server/PMK_58z:82, :467), a local function that still sees current on a station
        -- switched off or cut by LiveWire, and clears it every minute: the window of such a station
        -- shows Artel's no-power state itself, on this client only (entity = the station, :2578).
        { kind = "call", path = "PMK_ElectricDryerPanel.update", side = "client",
          consumer = { "ArtelElectricDryer", "ArtelSublimator" },
          machine = function(panel) return panel.entity end,
          instead = function(original, panel, ...)
              local result = original(panel, ...)
              panel.pausedFlag = true
              if panel.batchList then panel.batchList.pausedFlag = true end
              return result
          end },
        -- client/PMK_57_CraftBenchPanel.lua:2145 PMK_CraftBenchPanel:isUsable() (class :1896,
        -- methods through the metatable :2573-2574), checked before selecting a recipe (:2065) and
        -- starting a craft (:2174). The table is self.entity (:2578), the player self.player
        -- (ISBaseComponentPanel.table_constructor). Artel's answer when refused: false.
        { kind = "call", path = "PMK_CraftBenchPanel.isUsable", consumer = "ArtelChemTable", side = "client",
          machine = function(panel) return panel.entity end,
          instead = function(original, panel)
              LiveWireCompat.Gates.notify(panel.player, panel.entity)
              return false
          end },
    },
})
