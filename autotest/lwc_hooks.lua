-- LiveWire Compatibility, nominal in-game check of ADR-002 (solo, plan 002 I10).
-- 1. Profiles of the loaded target mods are applied: every consumer registered, every gate installed.
-- 2. A Functional Appliances 2 hot dog roller placed next to the player: the context menu offers
--    "Turn off" (our option), choosing it walks and switches the machine off (real menu callback and
--    timed action); it then bills 0 W, FA2's own menu options carrying it are greyed, its use
--    function queues nothing; "Turn on" switches it back and the use is queued again when powered.
-- 3. Machinery drill press and Project Arcade cabinet placed: switched off (fixture: direct write
--    of the authority, LWC_Switch.write), Machinery.Service.isPowered says false and the arcade play
--    option is greyed in the real Project Arcade menu.
-- Fixtures: objects placed with ISMoveableSpriteProps (no crafting), food given to the player.
local H = {}
local lines, okAll = {}, true
local S = { phase = "start" }
local HOTDOG, DRILL, CABINET = "location_shop_fossoil_01_10", "industry_02_268", "pa_arcades_0"

local function rec(ok, msg, detail)
    if not ok then okAll = false end
    lines[#lines + 1] = (ok and "PASS " or "FAIL ") .. msg .. (detail ~= nil and (" - " .. tostring(detail)) or "")
end

local function clearZombies()
    local list = getCell():getZombieList()
    for i = list:size() - 1, 0, -1 do
        local z = list:get(i)
        z:removeFromWorld(); z:removeFromSquare()
    end
end

-- Free indoor squares around the player, nearest first (the public grid powers rooms only).
local function freeSquares(n)
    local out, x0, y0 = {}, math.floor(S.p:getX()), math.floor(S.p:getY())
    for r = 1, 8 do
        for dy = -r, r do
            for dx = -r, r do
                if math.max(math.abs(dx), math.abs(dy)) == r then
                    local sq = getCell():getGridSquare(x0 + dx, y0 + dy, 0)
                    if sq and sq:isFree(false) and sq:isSolidFloor() and sq:getRoom() and sq:getObjects():size() <= 1 then
                        out[#out + 1] = sq
                        if #out >= n then return out end
                    end
                end
            end
        end
    end
    return out
end

local function place(sq, sprite)
    local props = ISMoveableSpriteProps.new(getSprite(sprite))
    return props:placeMoveableInternal(S.p, sq, props:instanceItem(sprite), sprite)
end

local function menuOf(obj)
    return ISWorldObjectContextMenu.createMenu(0, { obj }, getMouseX(), getMouseY(), false)
end

-- Options of a menu and its submenus.
local function eachOption(context, fn, depth)
    depth = depth or 1
    if not context or depth > 4 then return end
    for i = 1, context.numOptions - 1 do
        local o = context.options[i]
        if o then
            fn(o)
            if o.subOption then eachOption(context:getSubMenu(o.subOption), fn, depth + 1) end
        end
    end
end

local function carries(option, obj)
    if option.target == obj then return true end
    for i = 1, 10 do if option["param" .. i] == obj then return true end end
    return false
end

local function closeMenu(context)
    if context and context.closeAll then context:closeAll() end
end

local function queueSize()
    return #ISTimedActionQueue.getTimedActionQueue(S.p).queue
end

local function checkProfiles()
    local P, G = LiveWireCompat.Profiles, LiveWireCompat.Gates
    for _, name in ipairs({ "Artel", "FunctionalAppliances2", "Machinery", "ProjectArcade" }) do
        local profile
        for _, p in ipairs(P.list) do if p.name == name then profile = p end end
        local done, missing = P.applied[name] or {}, {}
        for _, c in ipairs(profile and profile.consumers or {}) do
            if done[c.id] ~= true then missing[#missing + 1] = c.id .. "=" .. tostring(done[c.id]) end
        end
        rec(profile ~= nil and #missing == 0, name .. ": every consumer registered", table.concat(missing, ","))
        local notWrapped = {}
        for _, g in ipairs(profile and profile.gates or {}) do
            if g.path and (g.kind == "object" or g.kind == "square" or g.kind == "call") then
                local _, _, current = G.resolve(g.path)
                if current == nil or G.wrappers[g.path] ~= current then notWrapped[#notWrapped + 1] = g.path end
            elseif g.kind == "action" then
                local _, _, class = G.resolve(g.path)
                if not class or G.wrappers[g.path .. ":isValid"] ~= class.isValid then
                    notWrapped[#notWrapped + 1] = g.path
                end
            end
        end
        rec(#notWrapped == 0, name .. ": every object/square/call/action gate installed", table.concat(notWrapped, ","))
    end
    local custom = {}
    for _, key in ipairs({ "PMK_StationApplyStage", "PMK.dryPause.thaw", "PMK.QBase.rebuild" }) do
        if not G.wrappers[key] then custom[#custom + 1] = key end
    end
    rec(#custom == 0, "Artel: custom gates installed (drying pause, Quantum Base rebuild)", table.concat(custom, ","))
    rec(G.menu and G.menu.hooked == true, "menu gate hooked on the world context menu")
end

local function findOption(context, key)
    local found
    eachOption(context, function(o) if o.lwcSwitch and o.name == getText(key) then found = o end end)
    return found
end

local function choose(option)
    option.onSelect(option.target, option.param1, option.param2, option.param3, option.param4)
end

function H.start(ctx)
    S.p = getPlayer()
    S.p:setGodMod(true); S.p:setInvisible(true)
    clearZombies()
    S.errors = getLuaDebuggerErrorCount()
    checkProfiles()
    local squares = freeSquares(3)
    if #squares < 3 then rec(false, "three free indoor squares near the player", #squares); S.phase = "end"; return true end
    S.hotdog = place(squares[1], HOTDOG)
    S.drill = place(squares[2], DRILL)
    S.cabinet = place(squares[3], CABINET)
    local API = LiveWire.API
    rec(S.hotdog and API.consumer(S.hotdog) == "FA2HotDogMachine", "hot dog roller placed and recognised",
        S.hotdog and API.consumer(S.hotdog))
    rec(S.drill and API.consumer(S.drill) == "MachineryDrillPress", "drill press placed and recognised",
        S.drill and API.consumer(S.drill))
    rec(S.cabinet and API.consumer(S.cabinet) == "PAArcadeCabinet", "arcade cabinet placed and recognised",
        S.cabinet and API.consumer(S.cabinet))
    if not (S.hotdog and S.drill and S.cabinet) then S.phase = "end"; return true end
    S.grid = squares[1]:haveElectricity()
    rec(true, "hot dog square has current (public grid)", tostring(S.grid))
    -- Food so that FA2 queues its action when the machine works.
    S.p:getInventory():AddItem("Base.BunsHotdog_single")
    S.p:getInventory():AddItem("Base.Sausage")
    local menu = menuOf(S.hotdog)
    local off = findOption(menu, "ContextMenu_LWC_TurnOff")
    rec(off ~= nil, "context menu offers Turn off", off and off.name)
    rec(off and off.toolTip and off.toolTip.description == getText("IGUI_LWC_RatedWatts", 500),
        "Turn off tooltip gives the draw", off and off.toolTip and off.toolTip.description)
    if not off then closeMenu(menu); S.phase = "end"; return true end
    choose(off)
    closeMenu(menu)
    S.t0, S.phase = getTimestampMs(), "switchingOff"
    return true
end

local function checkOff()
    local Switch, Cons = LiveWireCompat.Switch, LiveWire.Consumers
    rec(Switch.isOff(S.hotdog), "hot dog roller switched off by the menu and the walk action")
    rec(Cons.of(S.hotdog).powerConsumption(S.hotdog) == 0, "switched off: bills 0 W")
    rec(not Switch.powered(S.hotdog), "switched off: not powered")
    local menu = menuOf(S.hotdog)
    local greyed, carried = 0, 0
    eachOption(menu, function(o)
        if carries(o, S.hotdog) and not o.lwcSwitch then
            carried = carried + 1
            if o.notAvailable then greyed = greyed + 1 end
        end
    end)
    rec(carried > 0 and greyed == carried, "FA2 options of the switched-off roller are greyed", greyed .. "/" .. carried)
    rec(findOption(menu, "ContextMenu_LWC_TurnOn") ~= nil, "context menu now offers Turn on")
    closeMenu(menu)
    local before = queueSize()
    FAHotDogMachine.onUseHotDogMachine(nil, S.p, S.hotdog, "HotDogMachine_sound", "Hotdog")
    rec(queueSize() == before, "FA2 use function queues nothing while off", queueSize() - before)
    ISTimedActionQueue.clear(S.p)
    -- Machinery and Project Arcade (fixture: authority write).
    Switch.write(S.drill, true)
    Switch.write(S.cabinet, true)
    rec(Machinery.Service.isPowered(S.drill) == false, "Machinery drill press switched off: isPowered false")
    menu = menuOf(S.cabinet)
    local arcade, arcadeGreyed = 0, 0
    eachOption(menu, function(o)
        if carries(o, S.cabinet) and not o.lwcSwitch then
            arcade = arcade + 1
            if o.notAvailable then arcadeGreyed = arcadeGreyed + 1 end
        end
    end)
    rec(arcade > 0 and arcadeGreyed == arcade, "Project Arcade play option greyed while off", arcadeGreyed .. "/" .. arcade)
    closeMenu(menu)
    Switch.write(S.drill, false)
    -- Back on: Machinery's answer again (generator, or public grid in a room), which here is
    -- LiveWire's (ItemContainer.isObjectPowered: same rule for the grid in a room).
    local dsq = S.drill:getSquare()
    local machineryOwn = dsq:haveElectricity() or (dsq:hasGridPower() and dsq:getRoom() ~= nil)
    rec(Machinery.Service.isPowered(S.drill) == machineryOwn,
        "Machinery drill press back on: Machinery's own answer", tostring(machineryOwn))
    local on = findOption(menuOf(S.hotdog), "ContextMenu_LWC_TurnOn")
    if on then choose(on) end
end

function H.done(ctx)
    clearZombies()
    local now = getTimestampMs()
    if S.phase == "end" then return true end
    if S.phase == "switchingOff" then
        if not LiveWireCompat.Switch.isOff(S.hotdog) and now - S.t0 < 15000 then return false end
        checkOff()
        S.t0, S.phase = now, "switchingOn"
        return false
    end
    if S.phase == "switchingOn" then
        local Switch = LiveWireCompat.Switch
        if Switch.isOff(S.hotdog) and now - S.t0 < 15000 then return false end
        rec(not Switch.isOff(S.hotdog), "hot dog roller switched back on by the menu")
        rec(LiveWire.Consumers.of(S.hotdog).powerConsumption(S.hotdog) == 500, "switched on: bills 500 W")
        ISTimedActionQueue.clear(S.p)
        local before = queueSize()
        FAHotDogMachine.onUseHotDogMachine(nil, S.p, S.hotdog, "HotDogMachine_sound", "Hotdog")
        if S.grid then
            rec(queueSize() > before, "switched on and powered: FA2 queues its use again", queueSize() - before)
        else
            rec(queueSize() == before, "switched on without current: FA2 use still refused")
        end
        ISTimedActionQueue.clear(S.p)
        rec(getLuaDebuggerErrorCount() == S.errors, "no Lua error", getLuaDebuggerErrorCount() - S.errors)
        return true
    end
    return true
end

function H.result(ctx)
    return { ok = okAll, summary = "LiveWire Compatibility switch and gates" .. (okAll and " PASS" or " FAIL"),
             lines = lines }
end
return H
