-- LiveWire Compatibility: the server applies the switch requests of the clients (ADR-002, D04) and
-- the changes they report (ADR-004, D01).
-- media/lua/server is also loaded by an MP client: nothing to do there.
if isClient() then return end
require "LiveWireCompatibility/LWC_Switch"

local Switch = LiveWireCompat.Switch

local HANDLERS = {
    [Switch.COMMAND] = { fn = Switch.handle, label = "switch request" },
    [Switch.CHANGED] = { fn = Switch.handleChanged, label = "change report" },
}

local function onClientCommand(module, command, player, args)
    if module ~= Switch.MODULE then return end
    local h = HANDLERS[command]
    if not h then return end
    local ok, reason = h.fn(player, args)
    if not ok then
        print("[LiveWireCompat] " .. h.label .. " refused (" .. tostring(reason) .. ")")
    end
end

Events.OnClientCommand.Add(onClientCommand)
