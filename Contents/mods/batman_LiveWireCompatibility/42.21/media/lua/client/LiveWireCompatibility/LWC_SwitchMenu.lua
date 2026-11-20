-- LiveWire Compatibility: "Turn on" / "Turn off" in the context menu of a machine with our switch
-- (ADR-002, D01, D04). The player walks to the machine, then a short action sends the request
-- (LWC_Switch.request: a command to the server in MP). Available even without current. The
-- option is marked lwcSwitch so that the menu gate never greys it.
require "TimedActions/ISBaseTimedAction"
require "LiveWireCompatibility/LWC_Switch"
require "LiveWireCompatibility/LWC_Profiles"

local Switch = LiveWireCompat.Switch

-- Short action (no complete(): the switch is written by the server through the command).
LWC_SwitchAction = ISBaseTimedAction:derive("LWC_SwitchAction")

function LWC_SwitchAction:isValid()
    return self.machine:getObjectIndex() ~= -1
end

function LWC_SwitchAction:update()
    self.character:faceThisObject(self.machine)
end

function LWC_SwitchAction:start()
end

function LWC_SwitchAction:stop()
    ISBaseTimedAction.stop(self)
end

function LWC_SwitchAction:perform()
    Switch.request(self.character, self.machine, self.off)
    ISBaseTimedAction.perform(self)
end

function LWC_SwitchAction:new(character, machine, off)
    local o = ISBaseTimedAction.new(self, character)
    o.machine, o.off = machine, off
    o.maxTime = 10
    return o
end

local Menu = {}

function Menu.onSelect(playerObj, machine, off)
    if luautils.walkAdj(playerObj, machine:getSquare()) then
        ISTimedActionQueue.add(LWC_SwitchAction:new(playerObj, machine, off))
    end
end

-- The machines with our switch among the clicked objects and the objects of their squares.
local function machinesOf(worldObjects)
    local found, seen = {}, {}
    for i = 1, #worldObjects do
        local sq = worldObjects[i]:getSquare()
        local objects = sq and sq:getObjects()
        for j = 0, objects and objects:size() - 1 or -1 do
            local o = objects:get(j)
            if not seen[o] and Switch.switchable(o) then
                seen[o] = true
                found[#found + 1] = o
            end
        end
    end
    return found
end

local function addOption(context, playerObj, machine)
    local off = not Switch.isOff(machine)
    local key = off and "ContextMenu_LWC_TurnOff" or "ContextMenu_LWC_TurnOn"
    local option = context:addOption(getText(key), playerObj, Menu.onSelect, machine, off)
    option.lwcSwitch = true
    local watts = LiveWireCompat.Profiles.ratedWatts(LiveWireCompat.Profiles.consumerIdOf(machine), machine)
    if type(watts) == "number" and watts > 0 then
        local tip = ISWorldObjectContextMenu.addToolTip()
        tip:setName(getText(key))
        tip.description = getText("IGUI_LWC_RatedWatts", math.floor(watts + 0.5))
        option.toolTip = tip
    end
end

function Menu.onFill(playerNum, context, worldObjects, test)
    if test then return end
    local playerObj = getSpecificPlayer(playerNum)
    if not playerObj or playerObj:isDead() then return end
    local machines = machinesOf(worldObjects)
    for i = 1, #machines do addOption(context, playerObj, machines[i]) end
end

Events.OnFillWorldObjectContextMenu.Add(Menu.onFill)

LiveWireCompat.SwitchMenu = Menu
