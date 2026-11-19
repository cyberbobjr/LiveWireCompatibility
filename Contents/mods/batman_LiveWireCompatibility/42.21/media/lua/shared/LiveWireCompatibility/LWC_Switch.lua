-- LiveWire Compatibility: on/off switch of a placed machine (ADR-002, D01, D02, D04).
-- The state lives in the ModData of the placed object: LWC_off = true while off; no key = on,
-- so machines placed before this version stay on. Only consumers whose profile declares
-- `switch = true` get one (machines with a switch of their own keep theirs).
--   isOff(o)          the machine was switched off
--   powered(o)        LiveWire gives it current (circuits and breakers included) AND it is on
--   switchable(o)     the object is a registered consumer whose profile gives it a switch
--   request(p, o, off)  player asks: a command to the server in MP, applied at once otherwise
--   handle(p, args)   authority: checks the request, writes the ModData and sends it
-- No event loop: everything happens on a call (ADR-002, D05).
LiveWireCompat = LiveWireCompat or {}
local S = LiveWireCompat.Switch or { ids = {} }
LiveWireCompat.Switch = S

S.KEY = "LWC_off"
S.MODULE, S.COMMAND = "LWC", "setSwitch"
-- Reach of the player, in squares, from the machine (a player next to it, diagonals included).
S.REACH = 2.5

function S.isOff(o)
    return o ~= nil and o:hasModData() and o:getModData()[S.KEY] == true
end

function S.powered(o)
    return LiveWire.API.consumerPowered(o) == true and not S.isOff(o)
end

-- Called by the profile loader for each consumer of an active profile with a switch.
function S.enable(id)
    S.ids[id] = true
end

function S.switchable(o)
    local id = o ~= nil and LiveWire.API.consumer(o) or nil
    return id ~= nil and S.ids[id] == true
end

local function spriteName(o)
    local sprite = o:getSprite()
    return sprite and sprite:getName() or nil
end

function S.request(player, o, off)
    local sq = o:getSquare()
    if not sq then return end
    local args = { x = sq:getX(), y = sq:getY(), z = sq:getZ(), sprite = spriteName(o), off = off == true }
    if isClient() then
        sendClientCommand(player, S.MODULE, S.COMMAND, args)
    else
        S.handle(player, args)
    end
end

local function machineAt(args)
    local sq = getCell():getGridSquare(args.x, args.y, args.z)
    local objects = sq and sq:getObjects()
    if not objects then return nil end
    for i = 0, objects:size() - 1 do
        local o = objects:get(i)
        if spriteName(o) == args.sprite and S.switchable(o) then return o end
    end
    return nil
end

local function inReach(player, args)
    if not player or math.abs(player:getZ() - args.z) >= 1 then return false end
    local dx, dy = player:getX() - (args.x + 0.5), player:getY() - (args.y + 0.5)
    return dx * dx + dy * dy <= S.REACH * S.REACH
end

-- Returns true, or false and a reason ("bad_request", "no_machine", "out_of_reach").
function S.handle(player, args)
    if type(args) ~= "table" or type(args.x) ~= "number" or type(args.y) ~= "number"
        or type(args.z) ~= "number" or type(args.sprite) ~= "string" then
        return false, "bad_request"
    end
    local o = machineAt(args)
    if not o then return false, "no_machine" end
    if not inReach(player, args) then return false, "out_of_reach" end
    local md = o:getModData()
    if args.off == true then md[S.KEY] = true else md[S.KEY] = nil end
    if isServer() then o:transmitModData() end
    return true
end

return S
