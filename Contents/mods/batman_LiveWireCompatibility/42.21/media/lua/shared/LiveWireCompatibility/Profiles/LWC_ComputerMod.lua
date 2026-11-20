-- LiveWire Compatibility: Computer Mod (Workshop 3725497089, mod id ComputerModkum).
-- Analysis: docs/annexes/recherches/computer-mod.md. Desktop computers are the vanilla tiles
-- appliances_com_01_72..79 (no container, no LiveWire family): free power without this profile.
-- 120 W while switched on (a 486 PC with a CRT screen, estimate), nothing when off.
-- The laptop addon (Workshop 3798992436) is an inventory item: not billable.
-- Power check: ComputerModPower.hasComputerPower lives in the client Lua, so the cut applies to
-- the client side only; the dedicated server keeps its own local check (not reachable).
require "LiveWireCompatibility/LWC_Profiles"

-- The power button's state (ModData ComputerModPowerOn).
local function poweredOn(o)
    local md = o:getModData()
    return md ~= nil and md.ComputerModPowerOn == true
end

LiveWireCompat.Profiles.add({
    name = "ComputerMod",
    workshop = "3725497089",
    mods = { "ComputerModkum" },
    consumers = {
        -- Shared with CamRecorder's surveillance PC (appliances_com_01_72..75, ADR-005, D02): this
        -- member is the fallback (no owns), so every desktop CamRecorder did not set up stays here.
        { id = "ComputerModDesktop", watts = 120, shared = "VanillaDesktop",
          sprites = { "appliances_com_01_72", "appliances_com_01_73", "appliances_com_01_74", "appliances_com_01_75",
                      "appliances_com_01_76", "appliances_com_01_77", "appliances_com_01_78", "appliances_com_01_79" },
          running = poweredOn },
    },
    -- No switch of ours: the power button of Computer Mod (ModData ComputerModPowerOn, written by
    -- client/ComputerMod_UI_System.lua:3983-3986) is the machine's own switch (ADR-002, D01).
    gates = {
        -- Computer Mod 42, client/ComputerMod_Power.lua:144-156, hasComputerPower(computer), the
        -- placed computer as argument 1. Its callers read the global at each call
        -- (ComputerMod_UI.lua:690-691, ComputerMod_ContextMenu.lua:221-222); the screen update runs
        -- it every frame and turns the computer off when it answers false
        -- (ComputerMod_UI_Lifecycle.lua:245-256). Client only: the function lives in client Lua.
        { path = "ComputerModPower.hasComputerPower", kind = "object", consumer = "ComputerModDesktop",
          side = "client" },
        -- The power button ends with ComputerModComputerTypes.transmitData(computer)
        -- (client/ComputerMod_UI_System.lua:3983-3996, shared/ComputerMod_ComputerTypes.lua:119), also
        -- called for other data: only a change of the power state is reported (ADR-004).
        { kind = "notify", path = "ComputerModComputerTypes.transmitData", consumer = "ComputerModDesktop",
          state = poweredOn, side = "client" },
    },
})
