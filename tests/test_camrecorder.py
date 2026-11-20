"""Offline tests of the CamRecorder profile (ADR-005, D02, D05), embedded Lua 5.1 (pip install lupa).

Doubles keep the shape of CamRecorder 42 (Workshop 3840702720, read-only copy, mods/CamRecorder/42/media/lua):
- shared/PZVideoConsole.lua: CamRecorderConsole.matches (:37-41), available(computer, player, range)
  (:60-65), enabled (:67-69), canUse (:71-73), setPower(computer, enabled) (:92-97);
- client/CamRecorderSecurityTerminal.lua: local powered exported as PZVideoSecurityTerminal.powered
  (:48-55), T.setOption(object, playerNum, key, enabled, deferSync, computer) (:233-254),
  T.toggleComputer(computer, playerNum) (:255-264);
- client/CamRecorderDevices.lua: PZVideoDevices.isNative/usesGrid/isSecurity/isFixture/persist (:19-42);
- client/CamRecorderFixtures.lua: the fixed camera is an IsoObject named after a texture path (:4, :90-93,
  :341-342), wrapped as { pzObject = object } with getFullType from md.pzVideoMount.body (:120-140);
- client/CamRecorderImekagi.lua: Imekagi wrapper { pzObject, pzNativeImekagi = true } (:37-63);
- client/CamRecorderPower.lua: PZVideoPower.hasSupply(camera) (:25-31) and on(camera) (:32-35);
- client/CamRecorderPlayback.lua: PlayerPanel:togglePower (:438-458), ending with PZVideoDevices.persist;
- server/PZVideoAccessServer.lua: CamRecorderAccessServer.setRecording(s, player, object, enabled) (:164-180).
LiveWire's consumer lookup is by exact sprite name and applies couldBePowered (LW_Consumers.lua:71-79).
Run: python -B -m unittest tests.test_camrecorder
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

CAMERA_SPRITE = "media/textures/Item_CamRecorder_SecurityCamera.png"

TARGETS = r"""
-- LiveWire double: lookup by exact sprite name, couldBePowered applied (LW_Consumers.lua:71-79).
BY_SPRITE = {}
local register = LiveWire.API.registerConsumer
function LiveWire.API.registerConsumer(id, def)
    local ok, why = register(id, def)
    if ok then for _, s in ipairs(def.sprites) do BY_SPRITE[s] = id end end
    return ok, why
end
function LiveWire.API.consumer(o)
    if type(o) ~= "table" or not o.getSprite then return nil end
    local id = BY_SPRITE[o:getSprite():getName()]
    local def = id and REGISTERED[id]
    if not def then return nil end
    if def.couldBePowered and def.couldBePowered(o) ~= true then return nil end
    return id
end
SENT = {}
function sendClientCommand(p, mod, cmd, args) SENT[#SENT + 1] = { mod = mod, cmd = cmd, args = args } end
function getPlayer() return HERO end
function getSpecificPlayer() return HERO end
HERO = { getX = function() return 0 end, getY = function() return 0 end, getZ = function() return 0 end }

-- World object on its own square; ELEC is the engine's power on that square.
ELEC = true
local Methods = getmetatable(machine("x"))
function placed(sprite, md, cut)
    local o = setmetatable({ sprite = sprite, cut = cut, md = md }, Methods)
    o.getObjectIndex = function() return 0 end
    o.sq = { getX = function() return 1 end, getY = function() return 2 end, getZ = function() return 0 end,
             haveElectricity = function() return ELEC end, hasGridPower = function() return false end }
    return o
end

-- shared/PZVideoConsole.lua
CamRecorderConsole = {}
local C = CamRecorderConsole
function C.matches(object)
    local sprite = object and object.getSprite and object:getSprite()
    local name = sprite and sprite:getName() or ""
    return name:match("^appliances_com_01_7[2-5]$") ~= nil
end
function C.square(object) return object and object:getSquare() end
function C.available(computer, player, range)
    local q = C.matches(computer) and C.square(computer)
    return q and player and (q:haveElectricity() or q:hasGridPower()) or false
end
function C.enabled(computer) return computer:getModData().pzVideoConsoleEnabled ~= false end
function C.canUse(computer, player, range) return C.available(computer, player, range) and C.enabled(computer) end
function C.setPower(computer, enabled)
    local md = computer:getModData()
    if md.pzVideoConsoleEnabled == enabled then return end
    md.pzVideoConsoleEnabled = enabled
    computer:transmitModData()
end

-- client/CamRecorderDevices.lua
PZVideoDevices = {}
local D = PZVideoDevices
function D.isNative(item) return type(item) == "table" and item.pzNativeImekagi == true end
function D.isSecurity(item) return item and item:getFullType() == "CamRecorder.SecurityCamera" end
function D.usesGrid(item) return D.isSecurity(item) or D.isNative(item) end
function D.isFixture(item) return type(item) == "table" and item.pzObject ~= nil end
function D.persist(item)
    if D.isNative(item) and item.pzObject.transmitModData then item.pzObject:transmitModData() end
end

-- client/CamRecorderFixtures.lua (F.wrap) and client/CamRecorderImekagi.lua (I.wrap)
function fixture(body, cut)
    local o = placed("media/textures/Item_CamRecorder_SecurityCamera.png",
        { pzVideoMount = { body = body }, pzVideoCamera = { id = "c1", powered = false } }, cut)
    local camera = { pzObject = o }
    function camera:getFullType()
        local b = self:getModData().pzVideoMount.body
        if b == "digital" then return "CamRecorder.VideoCameraPrototype" end
        if b == "normal" then return "CamRecorder.VideoCameraNormal" end
        return "CamRecorder.SecurityCamera"
    end
    function camera:getModData() return self.pzObject:getModData() end
    function camera:getSquare() return self.pzObject:getSquare() end
    return camera
end
function imekagi(powered, cut)
    local o = placed("appliances_com_01_45", { pzVideoCamera = { id = "i1", powered = powered } }, cut)
    local camera = { pzObject = o, pzNativeImekagi = true }
    function camera:getFullType() return "Base.Mov_TVCamera" end
    function camera:getModData() return self.pzObject:getModData() end
    function camera:getSquare() return self.pzObject:getSquare() end
    return camera
end

-- client/CamRecorderPower.lua
PZVideoPower = {}
local P = PZVideoPower
function P.hasSupply(camera)
    if PZVideoDevices.usesGrid(camera) then
        local sq = camera:getSquare()
        return sq and (sq:haveElectricity() or sq:hasGridPower()) or false
    end
    local d = camera:getModData().pzVideoCamera
    return d and d.battery and d.battery.charge > 0 or false
end
function P.on(camera)
    if PZVideoDevices.isSecurity(camera) then return P.hasSupply(camera) end
    local d = camera:getModData().pzVideoCamera
    return d and d.powered == true and P.hasSupply(camera)
end

-- client/CamRecorderPlayback.lua PlayerPanel:togglePower (no live preview here)
function togglePower(camera)
    local d = camera:getModData().pzVideoCamera
    if PZVideoDevices.isSecurity(camera) then return "auto" end
    if not d.powered and PZVideoPower and not PZVideoPower.hasSupply(camera) then return "nopower" end
    d.powered = not d.powered
    PZVideoDevices.persist(camera)
    return d.powered
end

-- client/CamRecorderSecurityTerminal.lua
PZVideoSecurityTerminal = {}
local T = PZVideoSecurityTerminal
local function powered(object)
    local square = object:getSquare()
    if not square or not (square:haveElectricity() or square:hasGridPower()) then return false end
    if C.matches(object) then return C.enabled(object) end
    local settings = object:getModData().pzVideoTerminal
    return not settings or settings.enabled ~= false
end
T.powered = powered
function T.setOption(object, playerNum, key, enabled, deferSync, computer)
    if isClient() then
        sendClientCommand(HERO, "CamRecorder", "terminal", { setting = key, enabled = enabled })
    else
        local md = object:getModData()
        md.pzVideoTerminal = md.pzVideoTerminal or { version = 1, assignments = {} }
        md.pzVideoTerminal[key] = enabled
        object:transmitModData()
    end
    return true
end
function T.toggleComputer(computer, playerNum)
    if not C.available(computer, HERO) then return end
    local enabled = not C.enabled(computer)
    if isClient() then
        sendClientCommand(HERO, "CamRecorder", "consolePower", { enabled = enabled })
    else
        C.setPower(computer, enabled)
    end
end
function monitor(index, settings, cut)
    return placed("security_01_" .. index, settings and { pzVideoTerminal = settings } or nil, cut)
end
function desktop(index, md, cut) return placed("appliances_com_01_" .. index, md, cut) end

-- server/PZVideoAccessServer.lua
CamRecorderAccessServer = {}
function CamRecorderAccessServer.setRecording(s, player, object, enabled)
    if type(enabled) ~= "boolean" then return false, "denied" end
    local d = object:getModData().pzVideoCamera
    local sq = object:getSquare()
    if enabled and not (sq:haveElectricity() or sq:hasGridPower()) then return false, "unavailable" end
    d.recordingEnabled = enabled
    return true
end
"""


def make(side="sp", mods=("CamRecorder",)):
    lua = tp.make(active=False)
    lua.execute(TARGETS)
    lua.execute('SIDE = "%s"' % side)
    tpf.load_all(lua)
    for m in mods:
        lua.execute("ACTIVE.%s = true" % m)
    lua.execute("fire()")
    return lua


def draw(lua, expr):
    return lua.eval("(function(o) return REGISTERED[LiveWire.API.consumer(o)].powerConsumption(o) end)(%s)" % expr)


class Registration(unittest.TestCase):
    def test_consumers_and_their_sprites(self):
        lua = make()
        self.assertEqual(lua.eval("#LOG"), 0)
        self.assertEqual(list(lua.eval("REGISTERED.CamRecorderSecurityCamera.sprites").values()), [CAMERA_SPRITE])
        self.assertEqual(sorted(lua.eval("REGISTERED.CamRecorderImekagi.sprites").values()),
                         ["appliances_com_01_%d" % i for i in range(44, 48)])
        self.assertEqual(sorted(lua.eval("REGISTERED.CamRecorderMonitor.sprites").values()),
                         ["security_01_%d" % i for i in range(6)])
        self.assertEqual(sorted(lua.eval("REGISTERED.VanillaDesktop.sprites").values()),
                         ["appliances_com_01_%d" % i for i in range(72, 76)])

    def test_desktop_shared_with_computer_mod(self):
        lua = make(mods=("CamRecorder", "ComputerModkum"))
        self.assertEqual(sorted(lua.eval("REGISTERED.VanillaDesktop.sprites").values()),
                         ["appliances_com_01_%d" % i for i in range(72, 80)])
        self.assertIsNone(lua.eval("REGISTERED.ComputerModDesktop"))
        self.assertIsNone(lua.eval("REGISTERED.CamRecorderConsole"))

    def test_our_switch_on_the_fixed_camera_only(self):
        lua = make()
        self.assertTrue(lua.eval("LiveWireCompat.Switch.ids.CamRecorderSecurityCamera == true"))
        for cid in ("CamRecorderImekagi", "CamRecorderMonitor", "CamRecorderConsole"):
            self.assertFalse(lua.eval("LiveWireCompat.Switch.ids.%s == true" % cid), cid)


class Members(unittest.TestCase):
    """The surveillance PC is CamRecorder's once its power state is written; else Computer Mod's."""

    def setUp(self):
        self.lua = make(mods=("CamRecorder", "ComputerModkum"))

    def member(self, expr):
        return self.lua.eval("LiveWireCompat.Profiles.consumerIdOf(%s)" % expr)

    def test_pc_with_console_state_is_camrecorder(self):
        self.assertEqual(self.member("desktop(72, { pzVideoConsoleEnabled = true })"), "CamRecorderConsole")
        self.assertEqual(self.member("desktop(73, { pzVideoConsoleEnabled = false })"), "CamRecorderConsole")

    def test_other_desktops_stay_computer_mod(self):
        self.assertEqual(self.member("desktop(72)"), "ComputerModDesktop")
        self.assertEqual(self.member("desktop(77, { pzVideoConsoleEnabled = true })"), "ComputerModDesktop")

    def test_each_desktop_billed_by_its_mod(self):
        self.assertEqual(draw(self.lua, "desktop(74, { pzVideoConsoleEnabled = true })"), 120)
        self.assertEqual(draw(self.lua, "desktop(74, { pzVideoConsoleEnabled = false, ComputerModPowerOn = true })"), 0)
        self.assertEqual(draw(self.lua, "desktop(74, { ComputerModPowerOn = true })"), 120)
        self.assertEqual(draw(self.lua, "desktop(74)"), 0)


class Billing(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_fixed_security_camera(self):
        self.assertEqual(draw(self.lua, "fixture('security').pzObject"), 5)
        self.lua.execute("F = fixture('security'); F.pzObject:getModData().LWC_off = true")
        self.assertEqual(draw(self.lua, "F.pzObject"), 0)

    def test_floor_camcorders_on_battery_are_not_consumers(self):
        for body in ("digital", "normal"):
            self.assertIsNone(self.lua.eval("LiveWire.API.consumer(fixture('%s').pzObject)" % body), body)

    def test_imekagi_follows_its_power_button(self):
        self.assertEqual(draw(self.lua, "imekagi(true).pzObject"), 20)
        self.assertEqual(draw(self.lua, "imekagi(false).pzObject"), 0)
        self.assertEqual(draw(self.lua, "placed('appliances_com_01_44')"), 0)

    def test_monitors_follow_their_power_button(self):
        self.assertEqual(draw(self.lua, "monitor(0, { assignments = {} })"), 50)
        self.assertEqual(draw(self.lua, "monitor(5, { enabled = true })"), 100)
        self.assertEqual(draw(self.lua, "monitor(1, { enabled = false })"), 0)
        self.assertEqual(draw(self.lua, "monitor(4)"), 0)  # vanilla decoration never set up by CamRecorder

    def test_console_alone_draws_while_enabled(self):
        self.assertEqual(draw(self.lua, "desktop(75, { pzVideoConsoleEnabled = true })"), 120)
        self.assertEqual(draw(self.lua, "desktop(75, { pzVideoConsoleEnabled = false })"), 0)


class Gates(unittest.TestCase):
    def test_pc_refused_without_livewire_power_on_both_sides(self):
        for side in ("sp", "client", "server"):
            lua = make(side)
            self.assertEqual(lua.eval("CamRecorderConsole.available(desktop(72, { pzVideoConsoleEnabled = true }, true), HERO)"),
                             False, side)
            self.assertEqual(lua.eval("CamRecorderConsole.canUse(desktop(72, { pzVideoConsoleEnabled = true }, true), HERO)"),
                             False, side)
            self.assertEqual(lua.eval("CamRecorderConsole.available(desktop(72, { pzVideoConsoleEnabled = true }), HERO)"),
                             True, side)

    def test_computer_mod_desktop_not_gated_by_camrecorder(self):
        lua = make(mods=("CamRecorder", "ComputerModkum"))
        self.assertEqual(lua.eval("CamRecorderConsole.available(desktop(72, nil, true), HERO)"), True)

    def test_fixed_camera_refused_when_cut_or_switched_off(self):
        lua = make("client")
        self.assertEqual(lua.eval("PZVideoPower.hasSupply(fixture('security', true))"), False)
        self.assertEqual(lua.eval("PZVideoPower.on(fixture('security', true))"), False)
        lua.execute("F = fixture('security'); F.pzObject:getModData().LWC_off = true")
        self.assertEqual(lua.eval("PZVideoPower.hasSupply(F)"), False)
        self.assertEqual(lua.eval("PZVideoPower.hasSupply(fixture('security'))"), True)

    def test_battery_camcorder_untouched(self):
        lua = make("client")
        lua.execute("F = fixture('digital', true); F.pzObject:getModData().pzVideoCamera.battery = { charge = 0.5 }")
        self.assertEqual(lua.eval("PZVideoPower.hasSupply(F)"), True)

    def test_imekagi_cannot_be_switched_on_without_power(self):
        lua = make("client")
        self.assertEqual(lua.eval("togglePower(imekagi(false, true))"), "nopower")
        self.assertEqual(lua.eval("togglePower(imekagi(false))"), True)

    def test_monitor_refused_when_cut(self):
        lua = make("client")
        self.assertEqual(lua.eval("PZVideoSecurityTerminal.powered(monitor(4, { enabled = true }, true))"), False)
        self.assertEqual(lua.eval("PZVideoSecurityTerminal.powered(monitor(4, { enabled = true }))"), True)
        self.assertEqual(lua.eval("PZVideoSecurityTerminal.powered(desktop(72, { pzVideoConsoleEnabled = true }, true))"),
                         False)

    def test_server_refuses_to_start_recording_without_power(self):
        lua = make("server")
        res = lua.eval("{ CamRecorderAccessServer.setRecording({}, HERO, fixture('security', true).pzObject, true) }")
        self.assertEqual(tuple(res.values()), (False, "unavailable"))
        res = lua.eval("{ CamRecorderAccessServer.setRecording({}, HERO, fixture('security', true).pzObject, false) }")
        self.assertEqual(tuple(res.values()), (True,))

    def test_dedicated_server_keeps_client_functions(self):
        lua = make("server")
        self.assertEqual(lua.eval("PZVideoPower.hasSupply(fixture('security', true))"), True)
        self.assertEqual(lua.eval("PZVideoSecurityTerminal.powered(monitor(4, { enabled = true }, true))"), True)


class Notify(unittest.TestCase):
    """Own on/off of the PC, the monitors and the Imekagi is reported to LiveWire (ADR-004)."""

    def test_pc_power_reported_by_the_authority(self):
        for side in ("sp", "server"):
            lua = make(side)
            lua.execute("PC = desktop(72)")
            lua.execute("CamRecorderConsole.setPower(PC, true)")
            self.assertEqual(lua.eval("#CHANGED"), 1, side)
            self.assertEqual(lua.eval("CHANGED[1] == PC"), True, side)
            lua.execute("CamRecorderConsole.setPower(PC, true)")
            self.assertEqual(lua.eval("#CHANGED"), 1, side)
            lua.execute("CamRecorderConsole.setPower(PC, false)")
            self.assertEqual(lua.eval("#CHANGED"), 2, side)

    def test_sp_toggle_computer_reports(self):
        lua = make()
        lua.execute("PC = desktop(72, { pzVideoConsoleEnabled = true }); PZVideoSecurityTerminal.toggleComputer(PC, 0)")
        self.assertEqual(lua.eval("PC:getModData().pzVideoConsoleEnabled"), False)
        self.assertEqual(lua.eval("#CHANGED"), 1)

    def test_monitor_power_button_reported(self):
        lua = make()
        lua.execute("M = monitor(4, { enabled = true }); PZVideoSecurityTerminal.setOption(M, 0, 'enabled', false)")
        self.assertEqual(lua.eval("#CHANGED"), 1)
        lua.execute("PZVideoSecurityTerminal.setOption(M, 0, 'alarmSound', false)")
        self.assertEqual(lua.eval("#CHANGED"), 1)

    def test_mp_client_monitor_power_sent_after_the_target_command(self):
        lua = make("client")
        lua.execute("M = monitor(4, { enabled = true }); PZVideoSecurityTerminal.setOption(M, 0, 'enabled', false)")
        self.assertEqual(lua.eval("SENT[1].cmd"), "terminal")
        self.assertEqual(lua.eval("SENT[2].mod .. '/' .. SENT[2].cmd"), "LWC/changed")

    def test_imekagi_power_button_reported_once_per_change(self):
        lua = make()
        lua.execute("I = imekagi(false); togglePower(I)")
        self.assertEqual(lua.eval("#CHANGED"), 1)
        lua.execute("PZVideoDevices.persist(I)")
        self.assertEqual(lua.eval("#CHANGED"), 1)
        lua.execute("togglePower(I)")
        self.assertEqual(lua.eval("#CHANGED"), 2)

    def test_fixture_persist_not_reported(self):
        lua = make()
        lua.execute("PZVideoDevices.persist(fixture('security'))")
        self.assertEqual(lua.eval("#CHANGED"), 0)


if __name__ == "__main__":
    unittest.main()
