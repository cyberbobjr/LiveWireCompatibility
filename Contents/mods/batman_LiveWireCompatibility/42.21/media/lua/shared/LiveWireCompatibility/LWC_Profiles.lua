-- LiveWire Compatibility: registry of profiles and their loader (ADR-001, D02, D04).
-- A profile describes the electric machines of ONE other mod. It is a plain table, added by
-- its own file under Profiles/, and applied only when one of its mods is active. Everything
-- goes through LiveWire's public API (revision 6): nothing of LiveWire's internals is used.
--
-- Profile:
--   name       string, used in log lines
--   mods       array of mod.info ids; the profile applies if one of them is active
--   consumers  array of consumer descriptions:
--     id        unique consumer id given to LiveWire.API.registerConsumer
--     sprites   array of sprite names (one piece per multi-tile furniture)
--     watts     number, or function(o) -> W, while the machine runs
--     running   optional function(o) -> bool; when it says false the machine draws idle W
--     idle      optional number, W drawn while not running (default 0)
--     category, circuit   optional, as in registerConsumer
--     couldBePowered      optional function(o) -> bool, as in registerConsumer
--   gates      optional array of power checks of the target mod to make circuit-aware:
--     path      dotted path from a global to a function ("PMK.Well.isPowered")
--     arg       position of the argument that identifies the machine (default 1)
--     kind      "object" (that argument is the machine) or "square" (a square holding it)
--     consumer  id of the consumer (above) the machine belongs to, or an array of ids when one
--               power check serves several machines of the profile
--     side      optional "client": the check lives in the target's client Lua, so it is not
--               wrapped (nor reported missing) on a dedicated server
--   A gated function keeps its own answer and adds "and LiveWire.API.consumerPowered(machine)".
LiveWireCompat = LiveWireCompat or {}
local P = LiveWireCompat.Profiles or { list = {}, applied = {}, wrappers = {} }
LiveWireCompat.Profiles = P

local API_REVISION = 6

local function log(msg)
    print("[LiveWireCompat] " .. msg)
end

local function isStringArray(t)
    if type(t) ~= "table" or #t == 0 then return false end
    for i = 1, #t do
        if type(t[i]) ~= "string" or t[i] == "" then return false end
    end
    return true
end

local function validConsumer(c)
    return type(c) == "table" and type(c.id) == "string" and isStringArray(c.sprites)
        and (type(c.watts) == "number" or type(c.watts) == "function")
        and (c.running == nil or type(c.running) == "function")
        and (c.idle == nil or type(c.idle) == "number")
end

local function validGate(g)
    return type(g) == "table" and type(g.path) == "string"
        and ((type(g.consumer) == "string" and g.consumer ~= "") or isStringArray(g.consumer))
        and (g.arg == nil or type(g.arg) == "number")
        and (g.kind == "object" or g.kind == "square")
        and (g.side == nil or g.side == "client")
end

-- Consumer ids of a gate, as a set.
local function gateIds(g)
    if type(g.consumer) == "string" then return { [g.consumer] = true } end
    local ids = {}
    for i = 1, #g.consumer do ids[g.consumer[i]] = true end
    return ids
end

-- Adds a profile (normally at file load). Returns true, or false and a reason.
function P.add(profile)
    if type(profile) ~= "table" or type(profile.name) ~= "string" or not isStringArray(profile.mods)
        or type(profile.consumers) ~= "table" then
        return false, "invalid_profile"
    end
    for i = 1, #profile.consumers do
        if not validConsumer(profile.consumers[i]) then return false, "invalid_profile" end
    end
    for i = 1, #(profile.gates or {}) do
        if not validGate(profile.gates[i]) then return false, "invalid_profile" end
    end
    for i = 1, #P.list do
        if P.list[i].name == profile.name then return false, "duplicate_profile" end
    end
    P.list[#P.list + 1] = profile
    return true
end

function P.isActive(profile)
    local mods = getActivatedMods and getActivatedMods()
    if not mods then return false end
    for i = 1, #profile.mods do
        if mods:contains(profile.mods[i]) then return true end
    end
    return false
end

local function apiReady()
    local api = LiveWire and LiveWire.API
    return api ~= nil and (api.revision or 0) >= API_REVISION and api.registerConsumer ~= nil
end

-- registerConsumer definition of one consumer description.
function P.definition(c)
    local watts, running, idle = c.watts, c.running, c.idle or 0
    return {
        sprites = c.sprites,
        powerConsumption = function(o)
            if running and running(o) ~= true then return idle end
            if type(watts) == "function" then return watts(o) end
            return watts
        end,
        couldBePowered = c.couldBePowered,
        category = c.category,
        circuit = c.circuit,
    }
end

-- Function at a dotted path from a global: the table holding it, its key and the function.
local function resolve(path)
    local holder, key = _G, nil
    for part in string.gmatch(path, "[^%.]+") do
        if key ~= nil then
            holder = holder[key]
            if type(holder) ~= "table" then return nil end
        end
        key = part
    end
    if key == nil or type(holder[key]) ~= "function" then return nil end
    return holder, key, holder[key]
end

-- The machine of one of the consumers `ids` on a square, if any.
local function machineOn(square, ids)
    local objects = square and square.getObjects and square:getObjects()
    if not objects then return nil end
    for i = 0, objects:size() - 1 do
        local o = objects:get(i)
        local id = LiveWire.API.consumer(o)
        if id ~= nil and ids[id] then return o end
    end
    return nil
end

-- Wraps the power check named by `gate`, once: original answer, then the circuits' answer.
function P.wrapGate(gate)
    local holder, key, current = resolve(gate.path)
    if not holder then return false, "gate_not_found" end
    if P.wrappers[gate.path] == current then return true end
    local original, arg, kind, ids = current, gate.arg or 1, gate.kind, gateIds(gate)
    local wrapper = function(...)
        local result = original(...)
        if not result then return result end
        local subject = select(arg, ...)
        local machine = subject
        if kind == "square" then machine = machineOn(subject, ids) end
        local id = machine ~= nil and LiveWire.API.consumer(machine) or nil
        if id == nil or not ids[id] then return result end
        if LiveWire.API.consumerPowered(machine) then return result end
        return false
    end
    holder[key] = wrapper
    P.wrappers[gate.path] = wrapper
    return true
end

-- Applies one active profile: registers its consumers, then wraps its gates.
function P.apply(profile)
    local done = P.applied[profile.name] or {}
    P.applied[profile.name] = done
    for i = 1, #profile.consumers do
        local c = profile.consumers[i]
        if not done[c.id] then
            local ok, reason = LiveWire.API.registerConsumer(c.id, P.definition(c))
            if ok or reason == "duplicate_consumer" then
                done[c.id] = true
            else
                done[c.id] = reason
                log(profile.name .. ": consumer " .. c.id .. " not registered (" .. tostring(reason) .. ")")
            end
        end
    end
    for i = 1, #(profile.gates or {}) do
        local g = profile.gates[i]
        if not (g.side == "client" and isServer and isServer()) then
            local ok, reason = P.wrapGate(g)
            if not ok then log(profile.name .. ": power check " .. g.path .. " not wrapped (" .. reason .. ")") end
        end
    end
end

function P.applyAll()
    if not apiReady() then
        log("LiveWire API revision " .. API_REVISION .. " or later not found: nothing registered")
        return
    end
    for i = 1, #P.list do
        if P.isActive(P.list[i]) then P.apply(P.list[i]) end
    end
end

if not P.hooked and Events and Events.OnInitWorld then
    P.hooked = true
    Events.OnInitWorld.Add(P.applyAll)
end
