-- LiveWire Compatibility: gate kind "menu" (ADR-002, D05, D04 bis), client only. After the
-- target mods have filled the world context menu, every option whose target or parameters hold
-- a machine of the gate that is not powered stays visible but greyed, with the reason as tooltip.
-- It stops a use before anything is paid or started. Submenus are searched too.
--   name   label used in log lines (required)
-- Our own switch options are marked `lwcSwitch` and never greyed.
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local M = G.menu or { ids = {}, hooked = false }
G.menu = M
local PARAMS = { "target", "param1", "param2", "param3", "param4", "param5", "param6", "param7", "param8",
    "param9", "param10" }
-- Submenu depth searched (vanilla menus nest two or three levels).
local MAX_DEPTH = 4

local function blockedMachine(option)
    for i = 1, #PARAMS do
        local v = option[PARAMS[i]]
        if v ~= nil and G.blocked(v, M.ids) then return v end
    end
    return nil
end

local function grey(context, option, machine)
    option.notAvailable = true
    local tip = ISWorldObjectContextMenu.addToolTip()
    tip:setName(option.name)
    tip.description = getText(G.reasonKey(machine))
    option.toolTip = tip
end

function M.scan(context, depth)
    if not context or depth > MAX_DEPTH then return end
    for i = 1, context.numOptions - 1 do
        local option = context.options[i]
        if option and not option.lwcSwitch then
            local machine = blockedMachine(option)
            if machine then
                grey(context, option, machine)
            elseif option.subOption then
                M.scan(context:getSubMenu(option.subOption), depth + 1)
            end
        end
    end
end

function M.onFill(playerNum, context, worldObjects, test)
    if test then return end
    M.scan(context, 1)
end

local function validate(g)
    return type(g.name) == "string" and g.name ~= ""
end

local function install(g)
    if isServer and isServer() then return true end
    for id in pairs(G.ids(g)) do M.ids[id] = true end
    if not M.hooked and Events and Events.OnFillWorldObjectContextMenu then
        M.hooked = true
        Events.OnFillWorldObjectContextMenu.Add(M.onFill)
    end
    return true
end

G.register("menu", { validate = validate, install = install })
