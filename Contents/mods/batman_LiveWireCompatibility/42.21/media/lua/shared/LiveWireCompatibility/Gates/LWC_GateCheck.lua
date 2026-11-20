-- LiveWire Compatibility: gate kinds "object" and "square" (ADR-001 D04, ADR-002 D05).
-- A power check of the target mod keeps its own answer and adds "and the machine is powered".
--   path   dotted path of the check ("PMK.Well.isPowered")
--   arg    position of the argument that identifies the machine (default 1)
--   kind   "object": that argument is the machine; "square": a square holding it
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local function validate(g)
    return type(g.path) == "string" and (g.arg == nil or type(g.arg) == "number")
end

local function installer(onSquare)
    return function(g)
        local holder, key = G.resolve(g.path)
        local arg, ids = g.arg or 1, G.ids(g)
        return G.wrap(G.wrapName(g), holder, key, function(original)
            return function(...)
                local result = original(...)
                if not result then return result end
                local machine = select(arg, ...)
                if onSquare then machine = G.machineOn(machine, ids) end
                if G.blocked(machine, ids) then return false end
                return result
            end
        end)
    end
end

G.register("object", { validate = validate, install = installer(false) })
G.register("square", { validate = validate, install = installer(true) })
