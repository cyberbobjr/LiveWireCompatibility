-- LiveWire Compatibility: True Moozic (Workshop 3632610172, mod id TrueMoozic).
-- Analysis: docs/annexes/recherches/true-moozic.md. Already billed by LiveWire: the HiFi stereo
-- (IsoRadio on mains). Not billable: boomboxes, CD player and walkman (batteries), speakers
-- (passive). Billed here: the vanilla jukebox (IsoJukebox, recreational_01_0 facing E and
-- recreational_01_1 facing S) that True Moozic makes playable. 150 W while it plays (amplifier,
-- turntable and lights of a 1950s jukebox, estimate); md.tmJukebox.isPlaying is synced by the mod.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "TrueMoozic",
    workshop = "3632610172",
    mods = { "TrueMoozic" },
    consumers = {
        { id = "TMJukebox", sprites = { "recreational_01_0", "recreational_01_1" }, watts = 150,
          category = "radio",
          running = function(o)
              local md = o:getModData()
              local d = md and md.tmJukebox
              return d ~= nil and d.isPlaying == true
          end },
    },
    gates = {
        { path = "TMJukebox.hasPower", kind = "square", consumer = "TMJukebox" },
    },
})
