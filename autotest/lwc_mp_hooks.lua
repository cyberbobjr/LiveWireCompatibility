-- LiveWire Compatibility, multiplayer check of the switch (ADR-002, D04, D07; plan 002 I10).
-- Server: places a Functional Appliances 2 hot dog roller next to the player (authority).
-- Client: finds it, chooses "Turn off" in the real world context menu (walk, then the switch
-- action sends LWC/setSwitch); the client never writes the state itself, so seeing it off proves
-- the round trip (server ModData + transmitModData). Then FA2's use is refused on the client and
-- its options are greyed. The server checks its own copy: off, 0 W billed.
local H = { server = {}, client = {} }
local S = { lines = {}, ok = true }
local MODULE = "LWCTest"
local HOTDOG = "location_shop_fossoil_01_10"

local function rec(ok, name, detail)
    if not ok then S.ok = false end
    S.lines[#S.lines + 1] = (ok and "PASS " or "FAIL ") .. name .. " - " .. tostring(detail or "")
end

local function clearZombies()
    local list = getCell():getZombieList()
    for i = list:size() - 1, 0, -1 do
        local z = list:get(i)
        z:removeFromWorld(); z:removeFromSquare()
    end
end

local function freeIndoor(p)
    local x0, y0 = math.floor(p:getX()), math.floor(p:getY())
    for r = 1, 6 do
        for dy = -r, r do
            for dx = -r, r do
                local sq = getCell():getGridSquare(x0 + dx, y0 + dy, 0)
                if sq and sq:isFree(false) and sq:isSolidFloor() and sq:getRoom() and sq:getObjects():size() <= 1 then
                    return sq
                end
            end
        end
    end
    return nil
end

local function rollerNear(p)
    local x0, y0 = math.floor(p:getX()), math.floor(p:getY())
    for dy = -8, 8 do
        for dx = -8, 8 do
            local sq = getCell():getGridSquare(x0 + dx, y0 + dy, 0)
            local objects = sq and sq:getObjects()
            for i = 0, objects and objects:size() - 1 or -1 do
                local o = objects:get(i)
                if LiveWire.API.consumer(o) == "FA2HotDogMachine" then return o end
            end
        end
    end
    return nil
end

-- ---------------------------------------------------------------- server
function H.server.start(ctx)
    local players = ctx.players()
    S.player = players and players[1]
    if not S.player then rec(false, "a connected player"); return true end
    S.player:setGodMod(true)
    clearZombies()
    Events.OnClientCommand.Add(function(module, command, player, args)
        if module == MODULE and command == "report" then S.report = args end
    end)
    local sq = freeIndoor(S.player)
    if not sq then rec(false, "free indoor square next to the player"); return true end
    local props = ISMoveableSpriteProps.new(getSprite(HOTDOG))
    S.obj = props:placeMoveableInternal(S.player, sq, props:instanceItem(HOTDOG), HOTDOG)
    rec(S.obj and LiveWire.API.consumer(S.obj) == "FA2HotDogMachine", "server placed the hot dog roller",
        sq:getX() .. "," .. sq:getY())
    S.at = getTimestampMs()
    return true
end

function H.server.done(ctx)
    clearZombies()
    if not S.obj then return true end
    if S.report then return true end
    return getTimestampMs() - S.at > 240000
end

function H.server.result(ctx)
    if S.obj then
        local Switch = LiveWireCompat.Switch
        rec(Switch.isOff(S.obj), "server copy switched off by the client's request")
        rec(LiveWire.Consumers.of(S.obj).powerConsumption(S.obj) == 0, "server bills 0 W")
        rec(S.report ~= nil, "client report received")
        if S.report then
            rec(S.report.off == "true", "client received the off state from the server")
            rec(S.report.refused == "true", "client: FA2 use refused while off")
            rec(S.report.greyed == "true", "client: FA2 options greyed", S.report.greyedDetail)
        end
    end
    return { ok = S.ok, summary = "LiveWire Compatibility MP server", lines = S.lines }
end

-- ---------------------------------------------------------------- client
local C = { phase = "find" }

function H.client.start(ctx)
    C.t0 = getTimestampMs()
    getPlayer():getInventory():AddItem("Base.BunsHotdog_single")
    getPlayer():getInventory():AddItem("Base.Sausage")
    return true
end

-- Options carrying the machine (menus and submenus), and how many are greyed.
local function carriesGreyed(context, obj, acc, depth)
    acc, depth = acc or { 0, 0 }, depth or 1
    if not context or depth > 4 then return acc[1], acc[2] end
    for i = 1, context.numOptions - 1 do
        local o = context.options[i]
        if o and not o.lwcSwitch and (o.target == obj or o.param2 == obj) then
            acc[1] = acc[1] + 1
            if o.notAvailable then acc[2] = acc[2] + 1 end
        end
        if o and o.subOption then carriesGreyed(context:getSubMenu(o.subOption), obj, acc, depth + 1) end
    end
    return acc[1], acc[2]
end

function H.client.done(ctx)
    local now, p = getTimestampMs(), getPlayer()
    if now - C.t0 > 200000 then rec(false, "client finished in time", C.phase); return true end
    if C.phase == "find" then
        C.obj = rollerNear(p)
        if not C.obj then return false end
        rec(true, "client sees the hot dog roller")
        local menu = ISWorldObjectContextMenu.createMenu(0, { C.obj }, getMouseX(), getMouseY(), false)
        local off
        for i = 1, menu.numOptions - 1 do
            local o = menu.options[i]
            if o and o.lwcSwitch and o.name == getText("ContextMenu_LWC_TurnOff") then off = o end
        end
        rec(off ~= nil, "client menu offers Turn off")
        if not off then menu:closeAll(); return true end
        off.onSelect(off.target, off.param1, off.param2)
        menu:closeAll()
        C.phase, C.at = "waitOff", now
        return false
    end
    if C.phase == "waitOff" then
        local isOff = LiveWireCompat.Switch.isOff(C.obj)
        if not isOff and now - C.at < 60000 then return false end
        rec(isOff, "client received the off state", (now - C.at) .. " ms")
        ISTimedActionQueue.clear(p)
        local before = #ISTimedActionQueue.getTimedActionQueue(p).queue
        FAHotDogMachine.onUseHotDogMachine(nil, p, C.obj, "HotDogMachine_sound", "Hotdog")
        local refused = #ISTimedActionQueue.getTimedActionQueue(p).queue == before
        rec(refused, "client: FA2 use refused while off")
        local menu = ISWorldObjectContextMenu.createMenu(0, { C.obj }, getMouseX(), getMouseY(), false)
        local carried, greyed = carriesGreyed(menu, C.obj)
        menu:closeAll()
        rec(carried > 0 and carried == greyed, "client: FA2 options greyed", greyed .. "/" .. carried)
        sendClientCommand(p, MODULE, "report", { off = tostring(isOff), refused = tostring(refused),
            greyed = tostring(carried > 0 and carried == greyed), greyedDetail = greyed .. "/" .. carried })
        return true
    end
    return true
end

function H.client.result(ctx)
    return { ok = S.ok, summary = "LiveWire Compatibility MP client", lines = S.lines }
end
return H
