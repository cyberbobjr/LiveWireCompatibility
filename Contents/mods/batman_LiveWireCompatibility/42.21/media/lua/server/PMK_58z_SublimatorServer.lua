-- LiveWire Compatibility (ADR-006): stands in for Artel Manufactory's file of the same path and holds
-- none of Artel's code. It runs Artel's own file, read from Artel's folder, with the power check of
-- its drying stations routed through LiveWire (profile LWC_Artel). Without Artel, nothing runs.
require "LiveWireCompatibility/Profiles/LWC_Artel"
return LiveWireCompat.SourcePatch.run("media/lua/server/PMK_58z_SublimatorServer.lua")
