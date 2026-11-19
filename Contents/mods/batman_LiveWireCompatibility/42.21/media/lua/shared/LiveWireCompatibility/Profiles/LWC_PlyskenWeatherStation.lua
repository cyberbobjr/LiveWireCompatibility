-- LiveWire Compatibility: Plysken Weather Station (Workshop 3781590169, mod id PWS).
-- Analysis: docs/annexes/recherches/plysken-weather-station.md. The station is the only placed
-- object (pws_tileset_01_0 facing S, pws_tileset_01_1 facing E, read in the mod's .tiles).
-- PWS states no power figure: 15 W for sensors, logger and display (estimate). It records
-- whenever it has power, so it is billed whenever powered.
-- The desktop computer it reports to is a vanilla tile, billed by the Computer Mod profile when that mod is enabled.
-- PWS has no on/off switch: the station gets ours (ADR-002, D01).
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "PlyskenWeatherStation",
    workshop = "3781590169",
    mods = { "PWS" },
    consumers = {
        { id = "PWSStation", sprites = { "pws_tileset_01_0", "pws_tileset_01_1" }, watts = 15, switch = true },
    },
    gates = {
        -- PWS 42.1, shared/PWS/PWSPower.lua:51-64, isPowered(obj), the station as argument 1, field
        -- of the global PWS.Power (PWSPower.lua:29-30). Every caller reads PWS.Power.isPowered at
        -- call time: station read (PWSStation.lua:74), computer report (PWSComputer.lua:211), panel
        -- (client/PWS/PWSPanel.lua:180) and the server log, which records a gap (server/PWS/PWSLog.lua:89).
        { path = "PWS.Power.isPowered", kind = "object", consumer = "PWSStation" },
    },
})
