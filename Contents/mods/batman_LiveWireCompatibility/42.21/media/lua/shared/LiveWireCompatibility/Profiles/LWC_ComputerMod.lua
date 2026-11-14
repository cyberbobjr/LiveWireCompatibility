-- LiveWire Compatibility: Computer Mod (Workshop 3725497089, mod id ComputerModkum).
-- Analysis: docs/annexes/recherches/computer-mod.md. Desktop computers are the vanilla tiles
-- appliances_com_01_72..79 (no container, no LiveWire family): free power without this profile.
-- 120 W while switched on (a 486 PC with a CRT screen, estimate), nothing when off.
-- The laptop addon (Workshop 3798992436) is an inventory item: not billable.
-- Power check: ComputerModPower.hasComputerPower lives in the client Lua, so the cut applies to
-- the client side only; the dedicated server keeps its own local check (not reachable).
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "ComputerMod",
    workshop = "3725497089",
    mods = { "ComputerModkum" },
    consumers = {
        { id = "ComputerModDesktop", watts = 120,
          sprites = { "appliances_com_01_72", "appliances_com_01_73", "appliances_com_01_74", "appliances_com_01_75",
                      "appliances_com_01_76", "appliances_com_01_77", "appliances_com_01_78", "appliances_com_01_79" },
          running = function(o)
              local md = o:getModData()
              return md ~= nil and md.ComputerModPowerOn == true
          end },
    },
    gates = {
        { path = "ComputerModPower.hasComputerPower", kind = "object", consumer = "ComputerModDesktop",
          side = "client" },
    },
})
