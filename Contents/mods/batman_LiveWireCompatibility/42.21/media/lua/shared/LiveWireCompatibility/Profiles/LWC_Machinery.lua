-- LiveWire Compatibility: Machinery (Workshop 3780027195, mod id Machinery).
-- Analysis: docs/annexes/recherches/machinery.md. More Machinery Recipes (3807360837) adds
-- recipes only. Machinery stores no running state, so each machine draws an average over a
-- workshop day (ADR-001, D03): rated motor power times a share of use, estimates.
-- Not billed: the Cabinet table saw (petrol) and the propane storage.
-- Lathe: only the centre tile of each face is listed, so one lathe is one consumer.
-- One public power check, Machinery.Service.isPowered(object), serves every electric machine.
-- Machinery has no on/off switch (no running state): every machine gets ours (ADR-002, D01).
-- Drill press, hydraulic press, lathe and bench grinder are vanilla tiles Knox Working Machines also
-- gives a use to (ADR-005, D02): they are shared, and Machinery is the fallback member (no `owns`),
-- so with Machinery alone every such tile is billed as before; Knox claims only its own entities
-- (Profiles/LWC_KnoxWorkingMachines.lua).
require "LiveWireCompatibility/LWC_Profiles"

local ALL = { "MachineryDrillPress", "MachineryMetalBandsaw", "MachineryHydraulicPress", "MachineryLathe",
              "MachineryBenchGrinder", "MachineryTableSawIndustrial", "MachineryTableSawContractor",
              "MachineryConcreteMixer" }

LiveWireCompat.Profiles.add({
    name = "Machinery",
    workshop = "3780027195",
    mods = { "Machinery" },
    consumers = {
        { id = "MachineryDrillPress", shared = "VanillaDrillPress", watts = 150, switch = true,
          sprites = { "industry_02_268", "industry_02_269", "industry_02_270", "industry_02_271" } },
        { id = "MachineryMetalBandsaw", watts = 330, switch = true,
          sprites = { "industry_02_264", "industry_02_265", "industry_02_266", "industry_02_267",
                      "machinery_metal_bandsaw_01_0", "machinery_metal_bandsaw_01_1",
                      "machinery_metal_bandsaw_01_2", "machinery_metal_bandsaw_01_3" } },
        { id = "MachineryHydraulicPress", shared = "VanillaIndustry03Mill", watts = 300, switch = true,
          sprites = { "industry_03_48", "industry_03_49", "industry_03_50", "industry_03_51",
                      "industry_03_52", "industry_03_53", "industry_03_54", "industry_03_55" } },
        { id = "MachineryLathe", shared = "VanillaLathe", watts = 200, switch = true,
          sprites = { "industry_03_1", "industry_03_4", "industry_03_9", "industry_03_12",
                      "industry_03_33", "industry_03_36", "industry_03_41", "industry_03_44" } },
        { id = "MachineryBenchGrinder", shared = "VanillaBenchGrinder", watts = 125, switch = true,
          sprites = { "industry_04_20", "industry_04_21", "industry_04_22", "industry_04_23" } },
        { id = "MachineryTableSawIndustrial", watts = 500, switch = true,
          sprites = { "machinery_table_saws_01_8", "machinery_table_saws_01_9",
                      "machinery_table_saws_01_10", "machinery_table_saws_01_11" } },
        { id = "MachineryTableSawContractor", watts = 500, switch = true,
          sprites = { "machinery_table_saws_01_0", "machinery_table_saws_01_1",
                      "machinery_table_saws_01_2", "machinery_table_saws_01_3" } },
        { id = "MachineryConcreteMixer", watts = 350, switch = true,
          sprites = { "construction_01_6", "construction_01_7", "construction_01_14", "construction_01_15" } },
    },
    gates = {
        -- Machinery 42, shared/Machinery/Service.lua:128-134, isPowered(object), the placed machine
        -- as argument 1. Read through `local Service = Machinery.Service` (Service.lua:69-70) at each
        -- call by getOperationStatus (Service.lua:981, also hasRequiredPower :334-335), which guards
        -- every work path: the server's operate (Service.lua:1201), ISMachineAction:isValid
        -- (client/Machinery/TimedActions/ISMachineAction.lua:21) and the window
        -- (client/Machinery/UI/ISTableSawMachineWindow.lua:1372). Shared: the server has the last word.
        { path = "Machinery.Service.isPowered", kind = "object", consumer = ALL },
    },
})
