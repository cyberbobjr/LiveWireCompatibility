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
--     shared    optional id of a vanilla tile group several profiles give a use to: registered once,
--               each object belongs to the member whose owns(o) is true (ADR-005)
--     owns      optional function(o) -> bool, with shared; the member without it is the fallback
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
require "LiveWireCompatibility/LWC_SourcePatch"

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
        and (c.shared == nil or (type(c.shared) == "string" and c.shared ~= ""))
        and (c.owns == nil or type(c.owns) == "function")
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

-- ---------------------------------------------------------------------------- shared tiles (ADR-005)
-- A vanilla tile two mods give a use to is registered once to LiveWire, under its `shared` id;
-- each placed object belongs to the first member (profile order) whose owns(o) is true, else to
-- the member without `owns`. That member decides draw, switch, gates and name.
P.shared = P.shared or {} -- shared id -> { members = { consumer... }, sprites = { name... }, seen = set }

-- The member of a shared group an object belongs to, or nil. Never asks LiveWire: the group's own
-- couldBePowered runs inside LiveWire's consumer lookup (asking it again would recurse).
function P.memberIn(group, o)
    local fallback
    for i = 1, #group.members do
        local m = group.members[i]
        if m.owns then
            if m.owns(o) == true then return m end
        elseif not fallback then
            fallback = m
        end
    end
    return fallback
end

-- The profile consumer an object belongs to, or nil (not one of ours).
function P.memberOf(o)
    local id = o ~= nil and LiveWire.API.consumer(o) or nil
    if id == nil then return nil end
    local group = P.shared[id]
    if not group then return P.consumers[id] end
    return P.memberIn(group, o)
end

-- Id of the profile consumer an object belongs to (gates, switch, names), or nil.
function P.consumerIdOf(o)
    local m = P.memberOf(o)
    return m and m.id or nil
end

-- W the machine draws while it runs (for the switch tooltip), or nil when unknown.
function P.ratedWatts(id, o)
    local c = P.consumers[id]
    if not c then return nil end
    if type(c.watts) == "function" then return c.watts(o) end
    return c.watts
end

-- Draw now of an object of consumer description `c`: 0 switched off, idle when not running.
function P.draw(c, o)
    if c.switch and Switch.isOff(o) then return 0 end
    if c.running and c.running(o) ~= true then return c.idle or 0 end
    if type(c.watts) == "function" then return c.watts(o) end
    return c.watts
end

-- registerConsumer definition of one consumer description.
function P.definition(c)
    return {
        sprites = c.sprites,
        powerConsumption = function(o) return P.draw(c, o) end,
        couldBePowered = c.couldBePowered,
        category = c.category,
        circuit = c.circuit,
    }
end

-- registerConsumer definition of a shared tile group: the object's member decides.
local function sharedDefinition(group)
    local first = group.members[1]
    local refine = false
    for i = 1, #group.members do
        if group.members[i].couldBePowered then refine = true end
    end
    return {
        sprites = group.sprites,
        powerConsumption = function(o)
            local m = P.memberIn(group, o)
            return m and P.draw(m, o) or 0
        end,
        couldBePowered = refine and function(o)
            local m = P.memberIn(group, o)
            return m ~= nil and (m.couldBePowered == nil or m.couldBePowered(o) == true)
        end or nil,
        category = first.category,
        circuit = first.circuit,
    }
end

-- Collects the shared groups of the active profiles, then registers each group once.
local function registerShared(active)
    for i = 1, #active do
        for _, c in ipairs(active[i].consumers) do
            if c.shared then
                local group = P.shared[c.shared] or { members = {}, sprites = {}, seen = {} }
                P.shared[c.shared] = group
                local known = false
                for j = 1, #group.members do
                    if group.members[j] == c then known = true end
                end
                if not known then
                    group.members[#group.members + 1] = c
                    for _, s in ipairs(c.sprites) do
                        if not group.seen[s] then
                            group.seen[s] = true
                            group.sprites[#group.sprites + 1] = s
                        end
                    end
                end
            end
        end
    end
    for id, group in pairs(P.shared) do
        if group.registered == nil then
            local ok, reason = LiveWire.API.registerConsumer(id, sharedDefinition(group))
            group.registered = (ok or reason == "duplicate_consumer") and true or reason
            if group.registered ~= true then
                log("shared tiles " .. id .. " not registered (" .. tostring(reason) .. ")")
            end
        end
    end
end

-- Applies one active profile: registers its consumers, then installs its gates.
function P.apply(profile)
    local done = P.applied[profile.name] or {}
    P.applied[profile.name] = done
    for i = 1, #profile.consumers do
        local c = profile.consumers[i]
        if not done[c.id] then
            local ok, reason
            if c.shared then
                local group = P.shared[c.shared]
                ok = group ~= nil and group.registered == true
                reason = group and group.registered or "not_collected"
            else
                ok, reason = LiveWire.API.registerConsumer(c.id, P.definition(c))
            end
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
    local active = {}
    for i = 1, #P.list do
        if P.isActive(P.list[i]) then active[#active + 1] = P.list[i] end
    end
    registerShared(active)
    for i = 1, #active do P.apply(active[i]) end
    LiveWireCompat.SourcePatch.report()
end

if not P.hooked and Events and Events.OnInitWorld then
    P.hooked = true
    Events.OnInitWorld.Add(P.applyAll)
end
