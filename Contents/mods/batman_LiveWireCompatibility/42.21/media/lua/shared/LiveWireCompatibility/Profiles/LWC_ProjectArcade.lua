-- LiveWire Compatibility: Project Arcade (Workshop 3645980077, mod id ProjectArcade).
-- Analysis: docs/annexes/recherches/project-arcade.md. Sprites and footprints read in the mod's
-- ProjectArcadeTiles.tiles. In 42.22 the game loads common/ and 42.15/ (media only): all the Lua
-- cited below is under common/media/lua/client (abbreviated C/). The machines stay lit and play
-- their attract sound whenever their square has power (no on/off state of their own), so each one
-- gets our switch (ADR-002, D01). Draws are estimates for real machines of the period. Vanilla
-- arcade cabinets and pinball tables found on the map are swapped by the mod for these sprites
-- (server/ProjectArcade_ReplaceVanillaArcades.lua).
-- Wall fluorescent lights (pa_decorations_8..15) are light fixtures: already billed by LiveWire.
--
-- Gates (ADR-002, D06), all client side: every power check of the mod is a local
-- machineHasPower(obj) of a client file, and the coin is paid by
-- ProjectArcade_Currency.CheckAndQueueAction BEFORE the play action is queued (C/ProjectArcade_
-- Currency.lua:82-140). So a use is stopped first in the menu, then the play actions stop a game
-- in progress. The attract sound has no lever (ADR-002, out of scope).
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
-- complex_sw sit-down cabinet, two tiles per face (E 2+3, S 5+4, W 6+7, N 9+8). The menu ends as
-- soon as the clicked square holds pa_complex_2, 5, 7 or 8 (C/ProjectArcade_PAMPlayGameMenu.lua:
-- 404-410): the mod only plays the other piece (3, 4, 6, 9, its "tail", :220-240), which is billed.
local sitDown = list("pa_complex_", { 3, 4, 6, 9 })
-- Pinball tables: two tiles per face, billed on the head tile the mod plays on (S: n, E: n + 3).
local pinballs = list("pa_pinballs_", { 0, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23, 24, 27 })

-- The mod also plays the other piece of two pinball tables (pa_pinballs_21, 22, 25, 26 are play
-- sprites, PAMPlayGameMenu.lua:62-70): the gates judge any piece by the billed one of its
-- furniture (LiveWireCompat.Gates.billed, sprite grid).

-- Claw machine menu: addOption(text, worldobjects, closure) (C/ProjectArcade_ClawMachine.lua:168-169),
-- the machine is only in the closure. The option is recognised by its label (the same getText key
-- the mod uses) and the machine is the claw among the clicked objects (:156-161).
local function clawOfOption(option)
    if type(option.target) ~= "table" or option.name ~= getText("ContextMenu_ProjectArcade_PlayClawMachine") then
        return nil
    end
    for _, o in ipairs(option.target) do
        local billed = LiveWireCompat.Gates.billed(o)
        if billed and LiveWire.API.consumer(billed) == "PAClawMachine" then return o end
    end
    return nil
end

local PLAYED = { "PAArcadeCabinet", "PASitDownCabinet", "PAPinball" }
local ALL = { "PAArcadeCabinet", "PASitDownCabinet", "PAPinball", "PAClawMachine", "PACoinPusher",
    "PAPunchingMachine" }

LiveWireCompat.Profiles.add({
    name = "ProjectArcade",
    workshop = "3645980077",
    mods = { "ProjectArcade" },
    consumers = {
        -- Upright arcade cabinet: CRT monitor and board in attract mode, 120 W.
        { id = "PAArcadeCabinet", sprites = cabinets, watts = 120, switch = true },
        -- Sit-down cabinet: larger screen, 200 W.
        { id = "PASitDownCabinet", sprites = sitDown, watts = 200, switch = true },
        -- Pinball table: lamps, display and flipper coils in attract mode, 200 W.
        { id = "PAPinball", sprites = pinballs, watts = 200, switch = true },
        -- Claw machine: lighting and gantry, 100 W.
        { id = "PAClawMachine", sprites = range("pa_recreational_", 2, 5), watts = 100, switch = true },
        -- Coin pusher: pusher motor and lighting, 150 W.
        { id = "PACoinPusher", sprites = range("pa_recreational_", 6, 7), watts = 150, switch = true },
        -- Punching machine: display and sensor, 60 W.
        { id = "PAPunchingMachine", sprites = range("pa_recreational_", 0, 1), watts = 60, switch = true },
    },
    gates = {
        -- Greys the play options before the coin is paid. Machine found as option target or param:
        -- cabinets and pinballs: addOption(label, obj, fn) (PAMPlayGameMenu.lua:424);
        -- punching machine: subMenu:addOption(text, worldobjects, onTryStrength, playerObj,
        -- machineObj) (ProjectArcade_PunchingMachine.lua:435-439, high scores too).
        -- Coin pusher: target = worldobjects (ProjectArcade_CoinPusher.lua:318); stopped by its walk-up
        -- action and panel below, before any coin.
        { kind = "menu", name = "ProjectArcade menus", consumer = ALL, side = "client" },
        { kind = "menu", name = "ProjectArcade claw menu", consumer = "PAClawMachine", side = "client",
          machine = clawOfOption },
        -- Play actions (isValid read at every update): refuse, or stop a game in progress.
        -- C/TimedActions/ProjectArcade_PlayArcadeTimedAction.lua:994-998: o.object = object.
        { kind = "action", path = "ProjectArcade_PlayArcadeTimedAction", field = "object", consumer = PLAYED,
          side = "client" },
        -- C/TimedActions/ProjectArcade_ClawTimedAction.lua:324-327: o.machine = machine.
        { kind = "action", path = "ProjectArcade_ClawTimedAction", field = "machine",
          consumer = "PAClawMachine", side = "client" },
        -- C/TimedActions/ProjectArcade_PunchingTimedAction.lua:270-273: o.object = object.
        { kind = "action", path = "ProjectArcade_PunchingTimedAction", field = "object",
          consumer = "PAPunchingMachine", side = "client" },
        -- C/TimedActions/ProjectArcade_CoinPusherTimedAction.lua:26-28: o.machineObj = machineObj
        -- (walk-up action queued by the menu, before the panel; nothing paid yet).
        { kind = "action", path = "ProjectArcade_CoinPusherTimedAction", field = "machineObj",
          consumer = "PACoinPusher", side = "client" },
        -- C/ProjectArcade_CoinPusher.lua:174: OpenUI(playerObj, machineObj) opens the panel.
        { kind = "call", path = "ProjectArcade_CoinPusher.OpenUI", arg = 2, player = 1,
          consumer = "PACoinPusher", side = "client" },
        -- C/ISUI/ProjectArcade_CoinPusherUI.lua:464-491: beginPlay(self, pitId) calls onPlay, which
        -- pays (CoinPusher.lua:190-230); panel fields playerObj, machineObj (:658-662). A machine cut
        -- while the panel is open closes it before any coin is taken.
        { kind = "call", path = "ProjectArcade_CoinPusherUI.beginPlay", consumer = "PACoinPusher", side = "client",
          machine = function(ui) return ui.machineObj end,
          instead = function(original, ui)
              LiveWireCompat.Gates.notify(ui.playerObj, ui.machineObj)
              ui:close()
          end },
    },
})
