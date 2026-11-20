-- LiveWire Compatibility: gate kind "action" (ADR-002, D05). The game asks isValid of a running
-- timed action at every update (LuaTimedActionNew.java:110), so wrapping the class methods both
-- refuses a new action and stops one in progress when its machine is not powered.
--   path     dotted path of the timed action class ("UseHotDogMachine")
--   field    field of the action holding the machine ("machine"), or
--   machine  function(action) -> machine, when no single field holds it
-- isValid and isValidStart of the class (inherited ones included) are wrapped; the player is told
-- once per action why it stopped.
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local METHODS = { "isValidStart", "isValid" }

local function validate(g)
    return type(g.path) == "string"
        and ((type(g.field) == "string" and g.machine == nil) or (g.field == nil and type(g.machine) == "function"))
end

local function install(g)
    local _, _, class = G.resolve(g.path)
    if type(class) ~= "table" then return false, "gate_not_found" end
    local ids, field, machineOf = G.ids(g), g.field, g.machine
    for i = 1, #METHODS do
        local method = METHODS[i]
        local ok = G.wrap(G.wrapName(g, ":" .. method), class, method, function(original)
            return function(self, ...)
                local machine
                if field then machine = self[field] else machine = machineOf(self) end
                if G.blocked(machine, ids) then
                    if not self.lwcRefused then
                        self.lwcRefused = true
                        G.notify(self.character, machine)
                    end
                    return false
                end
                return original(self, ...)
            end
        end)
        if not ok then return false, "gate_not_found" end
    end
    return true
end

G.register("action", { validate = validate, install = install })
