-- LiveWire Compatibility: Knox Working Machines (Workshop 3841890337, mod id KnoxWorkingMachines).
-- Analysis: docs/annexes/recherches/knox-working-machines.md; decisions ADR-005 D02, D03.
-- Knox gives a use to VANILLA tiles: each machine is the vanilla tile turned into a GameEntity whose
-- script is KWM_* (scripts/entities/KWM_entities.txt, KWM_entities_v2.txt), attached on placement,
-- map load and to older objects (server/KWM_Attach.lua). Lathes and the mill are independent
-- single-tile sections (one KWM_* entity each, shared/KWM_Moveables.lua "(Section)"): every section
-- is billed with its share of the machine. Electric machines: the sprites Knox asks power for
-- (client/KWM_PowerGate.lua:9-83) plus the car wash (client/KWM_CarWashMenu.lua:63). Not billed:
-- welding cart, vises, furnaces, gas racks, tyre bench, fuel drums (no power test in Knox).
-- Draw: no running state is readable (a CraftBench has none), so each machine draws an average
-- while switched on: rated power of a real 1990s equivalent (analysis, section 1) times a share
-- of use, the factor the Machinery profile uses (about a quarter). Estimates.
-- Knox has no on/off switch: every machine gets ours (ADR-002, D01).
--
-- Tiles shared with the Machinery profile (ADR-005, D02): drill press, the lathe centres, the
-- industry_03_48..55 block (Machinery's hydraulic press, Knox's mill) and the bench grinder.
-- Knox owns an object that carries a KWM_* entity and no Machinery state; Machinery is the fallback
-- (no `owns`): with Machinery alone, every such tile stays billed as before, and Knox attaches its
-- entity to any object with these sprites (KWM_Attach.lua:9-25), Machinery-placed ones included,
-- so the Machinery state (movableData.Machinery, Machinery shared/Machinery/Service.lua:349-365)
-- must win over the entity.
require "LiveWireCompatibility/LWC_Profiles"

-- Share of use applied to the rated power (Machinery profile, docs/annexes/recherches/machinery.md 5).
local USE = 0.25

-- Average W of one tile: rated W of the whole machine, spread over its `pieces` tiles.
local function share(rated, pieces)
    return math.floor(rated * USE / (pieces or 1) + 0.5)
end

-- The object is one of Knox's entities (GameEntity.getEntityScript, GameEntityScript.getName,
-- 42.22 java/zombie/entity/GameEntity.java:148, scripting/entity/GameEntityScript.java:49).
local function knoxEntity(o)
    local script = o:getEntityScript()
    local name = script and script:getName()
    return type(name) == "string" and string.sub(name, 1, 4) == "KWM_"
end

-- Machinery has used this object: its state lives in movableData.Machinery (Service.lua:349-365).
local function machineryState(o)
    if not o:hasModData() then return false end
    local data = o:getModData().movableData
    return type(data) == "table" and data.Machinery ~= nil
end

local function knoxOwns(o)
    return knoxEntity(o) and not machineryState(o)
end

local IDS = { "KnoxDrillPress", "KnoxTableSaw", "KnoxLatheCentre", "KnoxLathe", "KnoxMill", "KnoxMillOther",
              "KnoxHydraulicPress", "KnoxBenchGrinder", "KnoxCharger", "KnoxCannery", "KnoxCarLift" }

LiveWireCompat.Profiles.add({
    name = "KnoxWorkingMachines",
    workshop = "3841890337",
    mods = { "KnoxWorkingMachines" },
    consumers = {
        -- Drill press, 400 W rated (single tile, KWM_DrillPress).
        { id = "KnoxDrillPress", watts = share(400), switch = true, shared = "VanillaDrillPress", owns = knoxOwns,
          sprites = { "industry_02_268", "industry_02_269", "industry_02_270", "industry_02_271" } },
        -- Table saw, 1500 W rated (KWM_TableSaw).
        { id = "KnoxTableSaw", watts = share(1500), switch = true,
          sprites = { "industry_02_152", "industry_02_153", "industry_02_154", "industry_02_155" } },
        -- Lathes (green KWM_LatheGreen_1..3, blue KWM_LatheBlue_1..3), 500 W rated, 3 sections each.
        -- The sections Machinery bills as lathe centres are shared.
        { id = "KnoxLatheCentre", watts = share(500, 3), switch = true, shared = "VanillaLathe", owns = knoxOwns,
          sprites = { "industry_03_1", "industry_03_4", "industry_03_9", "industry_03_12",
                      "industry_03_33", "industry_03_36", "industry_03_41", "industry_03_44" } },
        { id = "KnoxLathe", watts = share(500, 3), switch = true,
          sprites = { "industry_03_0", "industry_03_2", "industry_03_3", "industry_03_5",
                      "industry_03_8", "industry_03_10", "industry_03_11", "industry_03_13",
                      "industry_03_32", "industry_03_34", "industry_03_35", "industry_03_37",
                      "industry_03_40", "industry_03_42", "industry_03_43", "industry_03_45" } },
        -- Milling machine (KWM_Mill_1..4), 750 W rated, 4 sections. Sections 1-2 are the tiles
        -- Machinery bills as its hydraulic press.
        { id = "KnoxMill", watts = share(750, 4), switch = true, shared = "VanillaIndustry03Mill", owns = knoxOwns,
          sprites = { "industry_03_48", "industry_03_49", "industry_03_50", "industry_03_51",
                      "industry_03_52", "industry_03_53", "industry_03_54", "industry_03_55" } },
        { id = "KnoxMillOther", watts = share(750, 4), switch = true,
          sprites = { "industry_03_56", "industry_03_57", "industry_03_58", "industry_03_59",
                      "industry_03_60", "industry_03_61", "industry_03_62", "industry_03_63" } },
        -- Hydraulic press, 750 W rated pump (KWM_HydraulicPress).
        { id = "KnoxHydraulicPress", watts = share(750), switch = true,
          sprites = { "industry_02_46", "industry_02_47" } },
        -- Bench grinder, 370 W rated (KWM_BenchGrinder).
        { id = "KnoxBenchGrinder", watts = share(370), switch = true, shared = "VanillaBenchGrinder", owns = knoxOwns,
          sprites = { "industry_04_20", "industry_04_21", "industry_04_22", "industry_04_23" } },
        -- Battery charging panel, 150 W rated (KWM_Charger_1..11, one tile each; 166 and 167 not used).
        { id = "KnoxCharger", watts = share(150), switch = true,
          sprites = { "industry_02_163", "industry_02_164", "industry_02_165", "industry_02_168", "industry_02_169",
                      "industry_02_170", "industry_02_171", "industry_02_172", "industry_02_173", "industry_02_174",
                      "industry_02_175" } },
        -- Canning line, 1200 W rated, 2 sections (KWM_Cannery_1..4: tiles 49+50 and 54+55 sit side by
        -- side on the vanilla sheet, newtiledefinitions xy 1,6 2,6 and 6,6 7,6; assumption).
        { id = "KnoxCannery", watts = share(1200, 2), switch = true,
          sprites = { "industry_02_49", "industry_02_50", "industry_02_54", "industry_02_55" } },
        -- Two-post vehicle lift, 1500 W rated, intermittent (KWM_CarLift_1..4, "Vehicle Lift Post":
        -- posts 0+2 and 11+13, newtiledefinitions xy 0,0 2,0 and 3,1 5,1; assumption).
        { id = "KnoxCarLift", watts = share(1500, 2), switch = true,
          sprites = { "location_business_machinery_01_0", "location_business_machinery_01_2",
                      "location_business_machinery_01_11", "location_business_machinery_01_13" } },
        -- Car wash, 1000 W rated (hypothesis), one brush and one curtain per wash. No entity: Knox
        -- finds the washer by sprite (shared/KWM_Sprites.lua CarWashSprites).
        { id = "KnoxCarWash", watts = share(1000, 2), switch = true,
          sprites = { "location_business_machinery_01_6", "location_business_machinery_01_14",
                      "location_business_machinery_01_36", "location_business_machinery_01_37" } },
    },
    gates = {
        -- Station window: vanilla client/Entity/ISEntityUI.lua:333 CanOpenWindowFor(_player, _entity),
        -- the clicked IsoObject as argument 2, false refuses. Knox wraps it at file load with its own
        -- square test (client/KWM_PowerGate.lua:92-103); we wrap at OnInitWorld, on top of it. Shared
        -- by every vanilla station: only the ids below are refused. Client only (client Lua).
        { path = "ISEntityUI.CanOpenWindowFor", kind = "object", arg = 2, consumer = IDS, side = "client" },
        -- Crafting at a bench: Knox machines are CraftBench entities, crafted through ISHandcraftAction
        -- (vanilla shared/Entity/TimedActions/ISHandcraftAction.lua:5-15; the bench object in field
        -- `isoObject`, :395-402; queued by ISEntityUI.HandcraftStart, client/Entity/ISEntityUI.lua:107-130).
        -- Wrapping isValid also stops a craft in progress when the power goes. isValid runs on the client.
        { path = "ISHandcraftAction", kind = "action", field = "isoObject", consumer = IDS, side = "client" },
        -- Car wash: Knox's option carries the washer as param1
        -- (client/KWM_CarWashMenu.lua:57, addOption(text, playerObj, onWash, washer, vehicle)).
        { kind = "menu", name = "KnoxCarWash", consumer = "KnoxCarWash", side = "client" },
    },
})
