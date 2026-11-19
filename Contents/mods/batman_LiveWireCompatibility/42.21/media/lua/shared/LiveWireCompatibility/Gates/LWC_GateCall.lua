-- LiveWire Compatibility: gate kind "call" (ADR-002, D05). A global function of the target mod
-- that starts or allows a use of the machine is not run while the machine is not powered.
--   path     dotted path of the function ("FAHotDogMachine.onUseHotDogMachine")
--   arg      position of the machine argument (default 1); for a method (a:b()) count self
--   machine  optional function(...) -> machine, instead of `arg` (a panel method whose machine is
--            a field of self)
--   player   optional position of the player argument, to tell the player why
--   allow    optional function(...) -> true to let a call through anyway (switching a mode off)
--   refuse   value returned instead of running the function (default nil)
--   instead  optional function(original, ...) run instead of refusing (its results are returned)
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local function validate(g)
    return type(g.path) == "string" and (g.arg == nil or type(g.arg) == "number")
        and (g.machine == nil or (type(g.machine) == "function" and g.arg == nil))
        and (g.player == nil or type(g.player) == "number")
        and (g.allow == nil or type(g.allow) == "function")
        and (g.instead == nil or type(g.instead) == "function")
end

local function install(g)
    local holder, key = G.resolve(g.path)
    local arg, ids, playerArg, allow, refuse, instead = g.arg or 1, G.ids(g), g.player, g.allow, g.refuse, g.instead
    local machineOf = g.machine
    return G.wrap(g.path, holder, key, function(original)
        return function(...)
            local machine
            if machineOf then machine = machineOf(...) else machine = select(arg, ...) end
            if not G.blocked(machine, ids) or (allow and allow(...) == true) then return original(...) end
            if instead then return instead(original, ...) end
            if playerArg then G.notify(select(playerArg, ...), machine) end
            return refuse
        end
    end)
end

G.register("call", { validate = validate, install = install })
