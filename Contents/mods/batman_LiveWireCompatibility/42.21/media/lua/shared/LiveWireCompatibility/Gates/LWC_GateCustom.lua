-- LiveWire Compatibility: gate kind "custom" (ADR-002, D05), for an entry point no other kind
-- fits. The profile gives the installer; it receives the gate and the shared helpers.
--   name     label used in log lines (required)
--   install  function(gate, G) -> true, or false and a reason; it must be safe to call twice
--            (use G.wrap, which wraps once)
require "LiveWireCompatibility/LWC_Gates"
local G = LiveWireCompat.Gates

local function validate(g)
    return type(g.name) == "string" and g.name ~= "" and type(g.install) == "function"
end

local function install(g)
    return g.install(g, G)
end

G.register("custom", { validate = validate, install = install })
