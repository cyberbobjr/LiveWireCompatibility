-- LiveWire Compatibility: Project Arcade (Workshop 3645980077, mod id ProjectArcade).
-- Analysis: docs/annexes/recherches/project-arcade.md. Sprites and footprints read in the mod's
-- ProjectArcadeTiles.tiles. The machines stay lit and play their attract sound whenever their
-- square has power (no on/off state), so they are billed whenever powered. Draws are estimates
-- for real machines of the period. Vanilla arcade cabinets and pinball tables found on the map
-- are swapped by the mod for these sprites (ProjectArcade_ReplaceVanillaArcades.lua).
-- No gates: every power check of the mod is a local machineHasPower(obj).
-- Wall fluorescent lights (pa_decorations_8..15) are light fixtures: already billed by LiveWire.
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

-- Upright cabinets, one tile each (10 games x 4 faces), and the one-tile complex_t2 cabinet.
local cabinets = range("pa_arcades_", 0, 39)
list("pa_complex_", { 0, 1 }, cabinets)
-- complex_sw sit-down cabinet: two tiles per face, the 0,0 tile of each face is billed.
local sitDown = list("pa_complex_", { 2, 5, 6, 9 })
-- Pinball tables: two tiles per face, billed on the head tile the mod plays on (S: n, E: n + 3).
local pinballs = list("pa_pinballs_", { 0, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23, 24, 27 })

LiveWireCompat.Profiles.add({
    name = "ProjectArcade",
    workshop = "3645980077",
    mods = { "ProjectArcade" },
    consumers = {
        -- Upright arcade cabinet: CRT monitor and board in attract mode, 120 W.
        { id = "PAArcadeCabinet", sprites = cabinets, watts = 120 },
        -- Sit-down cabinet: larger screen, 200 W.
        { id = "PASitDownCabinet", sprites = sitDown, watts = 200 },
        -- Pinball table: lamps, display and flipper coils in attract mode, 200 W.
        { id = "PAPinball", sprites = pinballs, watts = 200 },
        -- Claw machine: lighting and gantry, 100 W.
        { id = "PAClawMachine", sprites = range("pa_recreational_", 2, 5), watts = 100 },
        -- Coin pusher: pusher motor and lighting, 150 W.
        { id = "PACoinPusher", sprites = range("pa_recreational_", 6, 7), watts = 150 },
        -- Punching machine: display and sensor, 60 W.
        { id = "PAPunchingMachine", sprites = range("pa_recreational_", 0, 1), watts = 60 },
    },
})
