-- LiveWire Compatibility: gate kind "notify" (ADR-004, D03). It refuses nothing: after a function of
-- the target mod that switches a machine on or off (or changes its draw) has run, LiveWire is told
-- (LWC_Switch.changed), so the inverter screens follow at once instead of at the next ten-minute
-- measure. Arguments and return values are kept.
--   path     dotted path of the function ("TMJukebox.transmit")
--   arg      position of the machine argument (default 1), or
--   machine  function(...) -> machine
--   state    optional function(machine) -> value: only a change of this value is reported (for a
--            function the target mod also calls for other small updates)
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local function validate(g)
    return type(g.path) == "string" and (g.arg == nil or type(g.arg) == "number")
        and (g.machine == nil or (type(g.machine) == "function" and g.arg == nil))
        and (g.state == nil or type(g.state) == "function")
end

local function install(g)
    local holder, key = G.resolve(g.path)
    local arg, ids, machineOf, stateOf = g.arg or 1, G.ids(g), g.machine, g.state
    local last = {} -- "x,y,z" -> last state reported
    local function report(machine)
        local t = type(machine)
        if t ~= "userdata" and t ~= "table" then return end
        local billed = G.billed(machine)
        local id = billed and G.idOf(billed)
        if id == nil or not ids[id] then return end
        local sq = billed.getSquare and billed:getSquare()
        if not sq then return end
        if stateOf then
            local k = sq:getX() .. "," .. sq:getY() .. "," .. sq:getZ()
            local v = tostring(stateOf(billed))
            if last[k] == v then return end
            last[k] = v
        end
        LiveWireCompat.Switch.changed(billed)
    end
    local function finish(machine, ...)
        report(machine)
        return ...
    end
    return G.wrap(G.wrapName(g, ":notify"), holder, key, function(original)
        return function(...)
            local machine
            if machineOf then machine = machineOf(...) else machine = select(arg, ...) end
            return finish(machine, original(...))
        end
    end)
end

G.register("notify", { validate = validate, install = install })
