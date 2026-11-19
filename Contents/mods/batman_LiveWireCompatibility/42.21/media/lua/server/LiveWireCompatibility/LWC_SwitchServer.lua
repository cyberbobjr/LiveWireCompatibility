-- LiveWire Compatibility: the server applies the switch requests of the clients (ADR-002, D04).
-- media/lua/server is also loaded by an MP client: nothing to do there.
if isClient() then return end
require "LiveWireCompatibility/LWC_Switch"

local Switch = LiveWireCompat.Switch

local function onClientCommand(module, command, player, args)
    if module ~= Switch.MODULE or command ~= Switch.COMMAND then return end
    local ok, reason = Switch.handle(player, args)
    if not ok then
        print("[LiveWireCompat] switch request refused (" .. tostring(reason) .. ")")
    end
end

Events.OnClientCommand.Add(onClientCommand)
