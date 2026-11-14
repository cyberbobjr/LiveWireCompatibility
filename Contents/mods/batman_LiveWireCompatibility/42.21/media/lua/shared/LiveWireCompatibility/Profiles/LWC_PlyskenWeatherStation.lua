-- LiveWire Compatibility: Plysken Weather Station (Workshop 3781590169, mod id PWS).
-- Analysis: docs/annexes/recherches/plysken-weather-station.md. The station is the only placed
-- object (pws_tileset_01_0 facing S, pws_tileset_01_1 facing E, read in the mod's .tiles).
-- PWS states no power figure: 15 W for sensors, logger and display (estimate). It records
-- whenever it has power, so it is billed whenever powered.
-- The desktop computer it reports to is a vanilla tile, billed by the Computer Mod profile when that mod is enabled.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "PlyskenWeatherStation",
    workshop = "3781590169",
    mods = { "PWS" },
    consumers = {
        { id = "PWSStation", sprites = { "pws_tileset_01_0", "pws_tileset_01_1" }, watts = 15 },
    },
    gates = {
        { path = "PWS.Power.isPowered", kind = "object", consumer = "PWSStation" },
    },
})
