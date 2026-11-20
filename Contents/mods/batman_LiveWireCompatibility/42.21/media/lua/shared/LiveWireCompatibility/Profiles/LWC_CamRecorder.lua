-- LiveWire Compatibility: CamRecorder (Workshop 3840702720, mod id CamRecorder; ADR-005, D02, D05).
-- Analysis: docs/annexes/recherches/camrecorder.md. Paths below are relative to
-- mods/CamRecorder/42/media/lua/. CamRecorder has no tiles of its own: it gives a use to vanilla
-- tiles (Imekagi camera, security monitors, desktop computer) and places its fixed camera as an
-- IsoObject named after a texture path. None of them is billed by the engine (plain IsoObjects:
-- no "signal" property, no container); the vanilla TVs it feeds are IsoTelevision, already
-- billed by LiveWire, so they are not registered here.
-- Draws are estimates (CamRecorder states none): see each consumer.
require "LiveWireCompatibility/LWC_Profiles"

local CAMERA_SPRITE = "media/textures/Item_CamRecorder_SecurityCamera.png"

-- ModData of a placed object, or nil without creating it (read at each LiveWire measure).
local function modData(o)
    return o ~= nil and o:hasModData() and o:getModData() or nil
end

-- The fixed camera's sprite is also used by camcorders set on the floor, which run on their
-- battery: only the security body runs on the grid (PZVideoDevices.usesGrid,
-- client/CamRecorderDevices.lua:20, :30; body read by client/CamRecorderFixtures.lua:124-129 and
-- server/PZVideoMotionServer.lua:17).
local function onGrid(o)
    local md = modData(o)
    local mount = md and md.pzVideoMount
    return type(mount) == "table" and mount.body ~= "digital" and mount.body ~= "normal"
end

-- Imekagi power button: md.pzVideoCamera.powered (client/CamRecorderPlayback.lua:449).
local function imekagiOn(o)
    local md = modData(o)
    return md ~= nil and type(md.pzVideoCamera) == "table" and md.pzVideoCamera.powered == true
end

-- Monitor power button: md.pzVideoTerminal.enabled, false = off (client/CamRecorderSecurityTerminal.lua:
-- 48-54). A monitor CamRecorder never set up (no pzVideoTerminal) is vanilla decoration: 0 W.
local function monitorOn(o)
    local md = modData(o)
    return md ~= nil and type(md.pzVideoTerminal) == "table" and md.pzVideoTerminal.enabled ~= false
end

-- Surveillance PC: CamRecorder writes md.pzVideoConsoleEnabled when the PC is first opened as a
-- console and at each press of its power button (shared/PZVideoConsole.lua:92-97, called by
-- client/CamRecorderSecurityTerminal.lua:255-264, :571-575 and server/PZVideoServer.lua:295-307).
local function consoleState(o)
    local md = modData(o)
    return md and md.pzVideoConsoleEnabled
end
-- Desktop tiles CamRecorder makes consoles of (CamRecorderConsole.matches, shared/PZVideoConsole.lua:37-41);
-- the other desktops of the shared group (Computer Mod's 76..79) are never CamRecorder's.
local CONSOLE_SPRITES = { "appliances_com_01_72", "appliances_com_01_73", "appliances_com_01_74",
    "appliances_com_01_75" }
local isConsoleSprite = {}
for i = 1, #CONSOLE_SPRITES do isConsoleSprite[CONSOLE_SPRITES[i]] = true end
local function ownsConsole(o)
    local sprite = o:getSprite()
    return sprite ~= nil and isConsoleSprite[sprite:getName()] == true and consoleState(o) ~= nil
end
local function consoleOn(o) return consoleState(o) == true end

-- Monitors: security_01_0..3 are control desks with 2 screens, 4..5 wall units with 4 screens
-- (slotsFor, client/CamRecorderSecurityTerminal.lua:34-37). 25 W per screen: a 1990s 9-12 inch
-- black-and-white CCTV monitor (estimate).
local function monitorWatts(o)
    local name = o:getSprite():getName()
    local index = tonumber(string.match(name, "^security_01_(%d+)$")) or 0
    return index <= 3 and 50 or 100
end

-- The camera object behind a CamRecorder camera wrapper ({ pzObject = object },
-- client/CamRecorderFixtures.lua:124, client/CamRecorderImekagi.lua:40); an inventory camcorder
-- (Java item) has none.
local function cameraObject(camera)
    return type(camera) == "table" and camera.pzObject or nil
end

-- The Imekagi object behind a wrapper handed to PZVideoDevices.persist, else nil (fixtures and
-- items are persisted too, client/CamRecorderDevices.lua:21-23, :64).
local function imekagiObject(item)
    return type(item) == "table" and item.pzNativeImekagi == true and item.pzObject or nil
end

LiveWireCompat.Profiles.add({
    name = "CamRecorder",
    workshop = "3840702720",
    mods = { "CamRecorder" },
    consumers = {
        -- Fixed security camera (client/CamRecorderFixtures.lua:4, :341-342; server/PZVideoServer.lua:
        -- 11, :582-583). 5 W: a 1990s CCD CCTV camera on 12 V (estimate). Always on while it has
        -- power (PZVideoPower.on, client/CamRecorderPower.lua:33): it gets our switch.
        { id = "CamRecorderSecurityCamera", watts = 5, sprites = { CAMERA_SPRITE }, switch = true,
          couldBePowered = onGrid },
        -- Imekagi HK533p broadcast camera (vanilla tiles, client/CamRecorderImekagi.lua:9). 20 W: a 1990s
        -- shoulder broadcast camera (estimate). Its own power button, reported below.
        { id = "CamRecorderImekagi", watts = 20, running = imekagiOn,
          sprites = { "appliances_com_01_44", "appliances_com_01_45", "appliances_com_01_46",
                      "appliances_com_01_47" } },
        -- Security monitors (client/CamRecorderSecurityTerminal.lua:29-33). Own power button, reported below.
        { id = "CamRecorderMonitor", watts = monitorWatts, running = monitorOn,
          sprites = { "security_01_0", "security_01_1", "security_01_2", "security_01_3", "security_01_4",
                      "security_01_5" } },
        -- Surveillance PC: the vanilla desktop (shared/PZVideoConsole.lua:37-41), shared with Computer
        -- Mod (ADR-005, D02): CamRecorder's once its console state is written, else Computer Mod's.
        -- 120 W while on: a 486 PC with its CRT screen (estimate, as Computer Mod's). Own power
        -- button, reported below.
        { id = "CamRecorderConsole", watts = 120, running = consoleOn, shared = "VanillaDesktop",
          owns = ownsConsole, sprites = CONSOLE_SPRITES },
    },
    gates = {
        -- shared/PZVideoConsole.lua:60-65, available(computer, player, range), the PC as argument 1:
        -- the test behind canUse (:71-73), resolve (:128-137, every server command on a PC,
        -- server/PZVideoServer.lua:278, :297, :651, :726) and the client panels
        -- (client/CamRecorderCctvUI.lua:301, client/CamRecorderSecurityTerminal.lua:257, :569). Both sides.
        { path = "CamRecorderConsole.available", kind = "object", consumer = "CamRecorderConsole" },
        -- client/CamRecorderPower.lua:25-31, hasSupply(camera): grid supply of the fixed camera and the
        -- Imekagi, read through the table by on (:32-35), status (:37), the panels
        -- (client/CamRecorderPlayback.lua:441, :444, :715). The machine is camera.pzObject. Client only.
        { path = "PZVideoPower.hasSupply", kind = "call", machine = cameraObject, refuse = false,
          consumer = { "CamRecorderSecurityCamera", "CamRecorderImekagi" }, side = "client" },
        -- client/CamRecorderSecurityTerminal.lua:48-55, powered(object) exported as T.powered; the
        -- terminal's own calls use the local (:267, :322, :403, :471, :496: not covered), the panels the export
        -- (client/CamRecorderCctvUI.lua:365, :415, :605; client/CamRecorderPlayback.lua:82). Client only.
        { path = "PZVideoSecurityTerminal.powered", kind = "object",
          consumer = { "CamRecorderMonitor", "CamRecorderConsole" }, side = "client" },
        -- server/PZVideoAccessServer.lua:164-180, setRecording(s, player, object, enabled): the camera
        -- object as argument 3; starting a recording without power answers false, "unavailable"
        -- (:167), as CamRecorder does; stopping stays allowed. Called through the table
        -- (:185, server/PZVideoServer.lua:676). Server Lua (the authority).
        { path = "CamRecorderAccessServer.setRecording", kind = "call", arg = 3, player = 2,
          consumer = "CamRecorderSecurityCamera", side = "server",
          allow = function(_, _, _, enabled) return enabled ~= true end,
          instead = function() return false, "unavailable" end },
        -- Own power buttons reported to LiveWire (ADR-004):
        -- PC: shared/PZVideoConsole.lua:92-97, setPower(computer, enabled), run by the authority only
        -- (client/CamRecorderSecurityTerminal.lua:255-264 sends consolePower from an MP client).
        { kind = "notify", path = "CamRecorderConsole.setPower", consumer = "CamRecorderConsole",
          state = consoleState, side = "server" },
        -- Monitors: client/CamRecorderSecurityTerminal.lua:233-254, setOption(object, playerNum, key,
        -- enabled), also used for alarm and pairing settings: only key "enabled" is reported. An MP
        -- client's report follows its "terminal" command, so the server measures after the change.
        { kind = "notify", path = "PZVideoSecurityTerminal.setOption", consumer = "CamRecorderMonitor",
          machine = function(object, _, key) if key == "enabled" then return object end return nil end,
          side = "client" },
        -- Imekagi: the power button (client/CamRecorderPlayback.lua:438-452) ends with
        -- PZVideoDevices.persist(camera) (:451; client/CamRecorderDevices.lua:21-23),
        -- also called after a rename: only a change of the power state is reported.
        { kind = "notify", path = "PZVideoDevices.persist", consumer = "CamRecorderImekagi",
          machine = imekagiObject, state = imekagiOn, side = "client" },
    },
})
