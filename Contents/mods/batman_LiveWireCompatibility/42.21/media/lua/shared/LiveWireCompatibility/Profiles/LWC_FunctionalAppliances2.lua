-- LiveWire Compatibility: Functional Appliances 2 (Workshop 3042138819, mod id FunctionalAppliances2).
-- Analysis: docs/annexes/recherches/functional-appliances-2.md. Variant loaded in 42.22: 42.20.
-- FA 2 reuses vanilla map tiles and gives them a mode or a use that needs power; it states no
-- power figure, so every draw below is an estimate (ADR-001, D03). None of these tiles has a
-- fridge or freezer container, so LiveWire does not bill them on its own.
-- FA 2 tests square:haveElectricity() inline, but every use goes through a global function or a
-- timed action class looked up by name: the gates below wrap those (ADR-002, D06). All of FA 2's
-- power logic runs on the client (client/*.lua), so the menu-side gates are client side (ADR-002,
-- D07); the timed action classes are shared, so their gates are installed on both sides.
-- Not listed: deep fryers, coffee machine, wall clock, payphones (FA 2 checks no power for
-- them), the SiloGenerator (a power source).
require "LiveWireCompatibility/LWC_Profiles"

local function range(prefix, from, to, out)
    out = out or {}
    for n = from, to do out[#out + 1] = prefix .. n end
    return out
end

local function list(prefix, ids, out)
    out = out or {}
    for i = 1, #ids do out[#out + 1] = prefix .. ids[i] end
    return out
end

-- FA 2 keeps the mode in ModData.CustomTemp ("Off", "Cold", "Warm", "Hot"), sent to the server
-- with transmitModData. It turns "Off" when power is lost at the object's next update.
local function mode(o)
    local md = o:getModData()
    return md and md.CustomTemp or "Off"
end

local function running(o)
    return mode(o) ~= "Off"
end

local function byMode(watts)
    return function(o) return watts[mode(o)] or 0 end
end

-- FA 2's onUse functions of the mode machines: tempSetting is the 4th argument.
local function settingOff(_junk, _player, _machine, tempSetting)
    return tempSetting == "Off"
end

-- FA.updateMachineTemp of a machine without power: FA 2's own Off branch, reached by its mode.
local function forceOff(original, Machine)
    Machine:getModData()['CustomTemp'] = "Off"
    return original(Machine)
end

-- Exhaust hood: its fan only matters (FAExhaustVents.lua) while a generator runs on its square.
local function generatorRunning(o)
    local sq = o:getSquare()
    local objects = sq and sq:getObjects()
    if not objects then return false end
    for i = 0, objects:size() - 1 do
        local g = objects:get(i)
        if instanceof(g, "IsoGenerator") and g:isActivated() then return true end
    end
    return false
end

-- Two-tile displays: each tile has its own container and its own mode, so each tile is billed.
local displays = range("location_restaurant_generic_01_", 24, 29)
range("location_restaurant_generic_01_", 32, 37, displays)
range("location_shop_generic_01_", 32, 35, displays)
range("location_restaurant_pie_01_", 48, 51, displays)
range("location_restaurant_seahorse_01_", 56, 59, displays)
range("location_restaurant_pizzawhirled_01_", 64, 67, displays)

LiveWireCompat.Profiles.add({
    name = "FunctionalAppliances2",
    workshop = "3042138819",
    mods = { "FunctionalAppliances2" },
    consumers = {
        -- Cantina food counter, one segment per tile: steam well hot 800 W, warm 400 W, cold 150 W.
        { id = "FA2HeatedCounter", sprites = range("location_restaurant_generic_01_", 16, 23),
          watts = byMode({ Hot = 800, Warm = 400, Cold = 150 }), running = running, category = "stove" },
        -- Display counters and glass displays, per tile: warm 150 W, cold 200 W.
        { id = "FA2DisplayCounter", sprites = displays,
          watts = byMode({ Warm = 150, Cold = 200 }), running = running, category = "fridge" },
        -- Snack and soda vending machines: warm 300 W, cold 200 W (lit cabinet and compressor).
        { id = "FA2VendingMachine",
          sprites = list("location_shop_accessories_01_", { 16, 17, 18, 19, 28, 29, 30, 31 }),
          watts = byMode({ Warm = 300, Cold = 200 }), running = running, category = "fridge" },
        -- Hot dog roller: no on/off of its own, works whenever powered; thermostat average 500 W.
        { id = "FA2HotDogMachine", sprites = list("location_shop_fossoil_01_", { 10, 11, 72, 73 }), watts = 500,
          switch = true },
        -- Popcorn machine: warmer and lamp between batches, average 200 W.
        { id = "FA2PopcornMachine", sprites = { "location_entertainment_theatre_01_17" }, watts = 200,
          switch = true },
        -- Tabletop soda fountain: carbonator and cold plate, average 200 W.
        { id = "FA2SodaFountain", sprites = list("location_shop_accessories_01_", { 8, 9, 12, 13 }),
          watts = 200, category = "fridge", switch = true },
        -- SlurpNBurp frozen drink machine: compressor duty cycle, average 400 W.
        { id = "FA2SlurpNBurp", sprites = list("location_shop_zippee_01_", { 56, 57, 60, 61 }),
          watts = 400, category = "fridge", switch = true },
        -- Bar taps: keg cooler, average 150 W.
        { id = "FA2BarTap", sprites = range("location_restaurant_bar_01_", 32, 35), watts = 150, category = "fridge",
          switch = true },
        -- Exhaust hood: 150 W fan while it clears a running generator's fumes. FA 2 gives it no
        -- entry point to wrap (FAExhaustVents.lua): no switch, no gate (ADR-002, D06).
        { id = "FA2ExhaustHood", sprites = range("appliances_cooking_01_", 68, 71), watts = 150,
          running = generatorRunning },
    },
    gates = {
        -- Greys the menu options of a switched-off or unpowered machine (ADR-002, D04 bis): FA 2's
        -- options carry the machine as param2 (HotDogMachineMenu.lua:14-19 and the other menus).
        -- Not for the mode machines: their "Off" choice must stay available.
        { kind = "menu", name = "FA2 menus", side = "client",
          consumer = { "FA2HotDogMachine", "FA2PopcornMachine", "FA2SodaFountain", "FA2SlurpNBurp", "FA2BarTap" } },
        -- Native Off mode (heated counter, displays, vending machines). FA.updateMachineTemp(Machine)
        -- (client/FAMapObjects.lua:102-129) is looked up by name at chunk load (:98, :136) and before
        -- each menu (client/FAInitContextMenus.lua:41, :44, :47, :50); its last branch (:117-120) is
        -- FA 2's own Off: room temperature, CustomTemp "Off", transmitted when it changed (:122-126).
        -- A machine LiveWire does not power takes that branch; FA 2's return value is kept.
        { kind = "call", path = "FA.updateMachineTemp", arg = 1, side = "client",
          consumer = { "FA2HeatedCounter", "FA2DisplayCounter", "FA2VendingMachine" },
          instead = forceOff },
        -- onUse(junk, player, machine, tempSetting): HeatedCountersMenu.lua:87,
        -- DisplayCountersMenu.lua:50, VendingMachinesMenu.lua:50. Setting "Off" stays allowed.
        { kind = "call", path = "FAHeatedCounter.onUseHeatedCounter", arg = 3, player = 2, side = "client",
          consumer = "FA2HeatedCounter", allow = settingOff },
        { kind = "call", path = "FADisplayCounter.onUseDisplayCounter", arg = 3, player = 2, side = "client",
          consumer = "FA2DisplayCounter", allow = settingOff },
        { kind = "call", path = "FAVendingMachine.onUseVendingMachine", arg = 3, player = 2, side = "client",
          consumer = "FA2VendingMachine", allow = settingOff },
        -- No-state machines: onUse(junk, player, machine, soundFile, ...) queues the action
        -- (HotDogMachineMenu.lua:77, :104, :112; PopcornMachineMenu.lua:23, :38;
        -- SodaFountainMenu.lua:238, :256, also for the SlurpNBurp; BarTapsMenu.lua:137, :149).
        { kind = "call", path = "FAHotDogMachine.onUseHotDogMachine", arg = 3, player = 2, side = "client",
          consumer = "FA2HotDogMachine" },
        { kind = "call", path = "FAPopcornMachine.onUsePopcornMachine", arg = 3, player = 2, side = "client",
          consumer = "FA2PopcornMachine" },
        { kind = "call", path = "FASodaFountain.onUseSodaFountain", arg = 3, player = 2, side = "client",
          consumer = { "FA2SodaFountain", "FA2SlurpNBurp" } },
        { kind = "call", path = "FABarTaps.onUseBarTaps", arg = 3, player = 2, side = "client",
          consumer = "FA2BarTap" },
        -- Timed actions (shared/TimedActions/Use*.lua): isValid at :5 always returns true; :new
        -- stores the machine in o.machine (UseHotDogMachine.lua:175, UsePopcornMachine.lua:139,
        -- UseSodaFountain.lua:181, UseBarTaps.lua:114). A cut stops the action in progress. The classes are
        -- shared (shared/TimedActions) and have complete(): installed on both sides, so the server refuses too.
        { kind = "action", path = "UseHotDogMachine", field = "machine",
          consumer = "FA2HotDogMachine" },
        { kind = "action", path = "UsePopcornMachine", field = "machine",
          consumer = "FA2PopcornMachine" },
        { kind = "action", path = "UseSodaFountain", field = "machine",
          consumer = { "FA2SodaFountain", "FA2SlurpNBurp" } },
        { kind = "action", path = "UseBarTaps", field = "machine",
          consumer = "FA2BarTap" },
    },
})
