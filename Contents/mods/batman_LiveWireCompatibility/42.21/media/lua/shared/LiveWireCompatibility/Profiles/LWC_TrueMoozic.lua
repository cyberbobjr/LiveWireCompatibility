-- LiveWire Compatibility: True Moozic (Workshop 3632610172, mod id TrueMoozic).
-- Analysis: docs/annexes/recherches/true-moozic.md. Already billed by LiveWire: the HiFi stereo
-- (IsoRadio on mains). Not billable: boomboxes, CD player and walkman (batteries), speakers
-- (passive). Billed here: the vanilla jukebox (IsoJukebox, recreational_01_0 facing E and
-- recreational_01_1 facing S) that True Moozic makes playable. 150 W while it plays (amplifier,
-- turntable and lights of a 1950s jukebox, estimate); md.tmJukebox.isPlaying is synced by the mod.
-- Sprites: the two vanilla tiles with CustomName "Jukebox" (newtiledefinitions.tiles, Facing E and S),
-- the property True Moozic finds jukeboxes by (shared/TMJukeboxDefs.lua:46-54); the conversion to
-- a container keeps the sprite (client/TMJukeboxContext.lua:31-39, server/TMJukeboxServerCommands.lua:45-54).
-- No switch of ours: play/stop of True Moozic is the jukebox's own switch (ADR-002, D01).
require "LiveWireCompatibility/LWC_Profiles"

-- The jukebox plays (ModData tmJukebox.isPlaying, shared/TMJukeboxDefs.lua:131-135).
local function playing(o)
    local md = o:getModData()
    local d = md and md.tmJukebox
    return d ~= nil and d.isPlaying == true
end

LiveWireCompat.Profiles.add({
    name = "TrueMoozic",
    workshop = "3632610172",
    mods = { "TrueMoozic" },
    consumers = {
        { id = "TMJukebox", sprites = { "recreational_01_0", "recreational_01_1" }, watts = 150,
          category = "radio",
          running = playing },
    },
    gates = {
        -- True Moozic 42, shared/TMJukeboxDefs.lua:398-407, hasPower(square), the jukebox square as
        -- argument 1. Called only by client code: play (client/RadioCom/TMJukeboxWindow.lua:598),
        -- window status (:762) and the jukebox tick, which stops playback and syncs it when it
        -- answers false (client/TMJukeboxTick.lua:172-176). Client side (ADR-002, D06, D07).
        { path = "TMJukebox.hasPower", kind = "square", consumer = "TMJukebox", side = "client" },
        -- Every play, stop and track change ends with TMJukebox.transmit(jukebox)
        -- (shared/TMJukeboxDefs.lua:153; client/RadioCom/TMJukeboxWindow.lua:609, 619): a change of
        -- isPlaying is reported to LiveWire (ADR-004).
        { kind = "notify", path = "TMJukebox.transmit", consumer = "TMJukebox", state = playing },
    },
})
