-- LiveWire Compatibility: registry of gate kinds (ADR-002, D05). A gate makes one entry point of
-- a target mod refuse to work for a machine that is not powered (LWC_Switch.powered: LiveWire's
-- current AND the machine is on). Each kind lives in its own file under Gates/ and registers here:
--   G.register(kind, { validate = function(gate) -> bool, install = function(gate) -> ok, reason })
-- Shared helpers keep the kinds short: path resolution, one-time wrapping, the consumer ids of a
-- gate, the blocked test and the message shown to the player.
require "LiveWireCompatibility/LWC_Switch"
LiveWireCompat = LiveWireCompat or {}
local G = LiveWireCompat.Gates or { kinds = {}, wrappers = {} }
LiveWireCompat.Gates = G

G.SIDES = { client = true, server = true }

function G.register(kind, impl)
    G.kinds[kind] = impl
end

local function isStringArray(t)
    if type(t) ~= "table" or #t == 0 then return false end
    for i = 1, #t do
        if type(t[i]) ~= "string" or t[i] == "" then return false end
    end
    return true
end
G.isStringArray = isStringArray

-- Common fields, then the fields of the kind.
function G.validate(g)
    if type(g) ~= "table" or type(g.kind) ~= "string" then return false end
    local impl = G.kinds[g.kind]
    if not impl then return false end
    if not ((type(g.consumer) == "string" and g.consumer ~= "") or isStringArray(g.consumer)) then return false end
    if g.side ~= nil and not G.SIDES[g.side] then return false end
    return impl.validate(g) == true
end

-- Name used in log lines and as the one-time key of a gate.
function G.label(g)
    return g.path or g.name or g.kind
end

-- Consumer ids of a gate, as a set.
function G.ids(g)
    if type(g.consumer) == "string" then return { [g.consumer] = true } end
    local ids = {}
    for i = 1, #g.consumer do ids[g.consumer[i]] = true end
    return ids
end

-- Value at a dotted path from a global: the table holding it, its key and the value.
function G.resolve(path)
    local holder, key = _G, nil
    for part in string.gmatch(path, "[^%.]+") do
        if key ~= nil then
            holder = holder[key]
            if type(holder) ~= "table" then return nil end
        end
        key = part
    end
    if key == nil or holder[key] == nil then return nil end
    return holder, key, holder[key]
end

-- Replaces holder[key] (a function) by make(original), once: a second call for the same `name`
-- while our wrapper is still in the chain of holder[key] does nothing, even with other wrappers of
-- ours stacked on it (several gates on one function). Returns true, or false and "gate_not_found".
G.inner = G.inner or {} -- wrapper -> the function it wraps
function G.wrap(name, holder, key, make)
    local current = holder and holder[key]
    if type(current) ~= "function" then return false, "gate_not_found" end
    local f = current
    while f do
        if G.wrappers[name] == f then return true end
        f = G.inner[f]
    end
    local wrapper = make(current)
    holder[key] = wrapper
    G.wrappers[name] = wrapper
    G.inner[wrapper] = current
    return true
end

-- One list reused for every lookup (no allocation on calls made at every frame).
local pieces

local function billedIn(list)
    for i = 0, list:size() - 1 do
        local o = list:get(i)
        if LiveWire.API.consumer(o) ~= nil then return o end
    end
    return nil
end

-- The billed piece of the furniture `o` belongs to: `o` itself when it is a registered consumer,
-- else another piece of the same sprite grid (IsoObject.getSpriteGridObjectsIncludingSelf) or of
-- the same multi-square entity (SpriteConfig.getAllMultiSquareObjects, B42 built furniture).
-- A profile bills one piece per furniture, but a target mod may hand any piece to its checks.
function G.billed(o)
    if LiveWire.API.consumer(o) ~= nil then return o end
    if not o.getSpriteGrid or not o:getSquare() then return nil end
    pieces = pieces or ArrayList.new()
    local found
    if o:getSpriteGrid() then
        o:getSpriteGridObjectsIncludingSelf(pieces)
        found = billedIn(pieces)
    end
    local config = not found and o.getSpriteConfig and o:getSpriteConfig()
    if config then
        pieces:clear()
        config:getAllMultiSquareObjects(pieces)
        found = billedIn(pieces)
    end
    pieces:clear()
    return found
end

-- The machine (any piece of it) is one of `ids` and is not powered (off, cut, or no current).
function G.blocked(machine, ids)
    local t = type(machine)
    if t ~= "userdata" and t ~= "table" then return false end
    local billed = G.billed(machine)
    local id = billed and LiveWire.API.consumer(billed)
    if id == nil or not ids[id] then return false end
    return not LiveWireCompat.Switch.powered(billed)
end

-- The machine of one of `ids` on a square, if any.
function G.machineOn(square, ids)
    local objects = square and square.getObjects and square:getObjects()
    if not objects then return nil end
    for i = 0, objects:size() - 1 do
        local o = objects:get(i)
        local id = LiveWire.API.consumer(o)
        if id ~= nil and ids[id] then return o end
    end
    return nil
end

-- Translation key of the reason a machine refuses to work.
function G.reasonKey(machine)
    if LiveWireCompat.Switch.isOff(G.billed(machine) or machine) then return "IGUI_LWC_MachineOff" end
    return "IGUI_LWC_NoPower"
end

-- Tells the player, on the client only, why the machine refused.
function G.notify(player, machine)
    if not player or (isServer and isServer()) or not player.setHaloNote then return end
    player:setHaloNote(getText(G.reasonKey(machine)), 255, 140, 120, 300)
end

-- Should the gate be installed on this side?
function G.onThisSide(g)
    if g.side == "client" then return not (isServer and isServer()) end
    if g.side == "server" then return not (isClient and isClient()) end
    return true
end

function G.install(g)
    return G.kinds[g.kind].install(g)
end

return G
