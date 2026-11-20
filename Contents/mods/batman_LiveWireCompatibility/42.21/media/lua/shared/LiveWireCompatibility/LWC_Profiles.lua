-- LiveWire Compatibility: registry of profiles and their loader (ADR-001, D02, D04; ADR-002).
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
--     switch    optional true: the machine gets our on/off switch (LWC_Switch); off = 0 W
--     category, circuit   optional, as in registerConsumer
--     couldBePowered      optional function(o) -> bool, as in registerConsumer
--   gates      optional array of entry points of the target mod that must refuse to work for a
--              machine that is not powered (LWC_Gates; one kind per file under Gates/):
--     kind      "object", "square", "action", "call", "menu", "custom" or "notify" (tells LiveWire
--               that a machine was switched on or off by the target mod, ADR-004)
--     consumer  id of the consumer (above) the machine belongs to, or an array of ids
--     side      optional "client" or "server": installed on that side only
--     ...       fields of the kind (see Gates/LWC_Gate<Kind>.lua)
LiveWireCompat = LiveWireCompat or {}
require "LiveWireCompatibility/LWC_Switch"
require "LiveWireCompatibility/LWC_Gates"
-- Gate kinds, one file each.
require "LiveWireCompatibility/Gates/LWC_GateCheck"
require "LiveWireCompatibility/Gates/LWC_GateAction"
require "LiveWireCompatibility/Gates/LWC_GateCall"
require "LiveWireCompatibility/Gates/LWC_GateMenu"
require "LiveWireCompatibility/Gates/LWC_GateCustom"
require "LiveWireCompatibility/Gates/LWC_GateNotify"

local P = LiveWireCompat.Profiles or { list = {}, applied = {}, consumers = {} }
LiveWireCompat.Profiles = P
local Switch, Gates = LiveWireCompat.Switch, LiveWireCompat.Gates

local API_REVISION = 6

local function log(msg)
    print("[LiveWireCompat] " .. msg)
end

local function validConsumer(c)
    return type(c) == "table" and type(c.id) == "string" and Gates.isStringArray(c.sprites)
        and (type(c.watts) == "number" or type(c.watts) == "function")
        and (c.running == nil or type(c.running) == "function")
        and (c.idle == nil or type(c.idle) == "number")
        and (c.switch == nil or type(c.switch) == "boolean")
end

-- Adds a profile (normally at file load). Returns true, or false and a reason.
function P.add(profile)
    if type(profile) ~= "table" or type(profile.name) ~= "string" or not Gates.isStringArray(profile.mods)
        or type(profile.consumers) ~= "table" then
        return false, "invalid_profile"
    end
    for i = 1, #profile.consumers do
        if not validConsumer(profile.consumers[i]) then return false, "invalid_profile" end
    end
    for i = 1, #(profile.gates or {}) do
        if not Gates.validate(profile.gates[i]) then return false, "invalid_profile" end
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

-- W the machine draws while it runs (for the switch tooltip), or nil when unknown.
function P.ratedWatts(id, o)
    local c = P.consumers[id]
    if not c then return nil end
    if type(c.watts) == "function" then return c.watts(o) end
    return c.watts
end

-- registerConsumer definition of one consumer description.
function P.definition(c)
    local watts, running, idle, switch = c.watts, c.running, c.idle or 0, c.switch == true
    return {
        sprites = c.sprites,
        powerConsumption = function(o)
            if switch and Switch.isOff(o) then return 0 end
            if running and running(o) ~= true then return idle end
            if type(watts) == "function" then return watts(o) end
            return watts
        end,
        couldBePowered = c.couldBePowered,
        category = c.category,
        circuit = c.circuit,
    }
end

-- Applies one active profile: registers its consumers, then installs its gates.
function P.apply(profile)
    local done = P.applied[profile.name] or {}
    P.applied[profile.name] = done
    for i = 1, #profile.consumers do
        local c = profile.consumers[i]
        if not done[c.id] then
            local ok, reason = LiveWire.API.registerConsumer(c.id, P.definition(c))
            if ok or reason == "duplicate_consumer" then
                done[c.id] = true
                P.consumers[c.id] = c
                if c.switch then Switch.enable(c.id) end
            else
                done[c.id] = reason
                log(profile.name .. ": consumer " .. c.id .. " not registered (" .. tostring(reason) .. ")")
            end
        end
    end
    for i = 1, #(profile.gates or {}) do
        local g = profile.gates[i]
        if Gates.onThisSide(g) then
            local ok, reason = Gates.install(g)
            if not ok then
                log(profile.name .. ": power check " .. Gates.label(g) .. " not wrapped (" .. tostring(reason) .. ")")
            end
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
