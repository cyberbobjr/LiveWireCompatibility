"""Offline tests of the Artel Manufactory profile (ADR-002, D03, D06), embedded Lua 5.1 (pip install lupa).

Doubles of the Artel globals the profile reads or wraps, with the shape of the real ones
(Workshop 3794133594, variant 42/):
- PMK.Well.isPowered, PMK.Trade.gridPowered / powerSource, PMK.QBase.squarePowered / hasPower /
  rebuild (rebuild puts a NEW object on the square, without the old ModData: PMK_87c:613-616);
- PMK.dryPause.freeze / thaw / isHeld keyed by the batch (CraftRecipeData), PMK_54p:168-196;
- PMK_StationApplyStage and the two kind globals that call it (PMK_54s:234, :293; PMK_58s:55);
- tick(): one pass of the server watchdog in the order of PMK_58z_SublimatorServer.lua:417-475
  (per station: freeze or thaw every batch, then the stage global of its kind looked up in _G);
- PMK_CraftBenchPanel, a class whose instances get their methods through a metatable
  (PMK_57:1896, :2568-2578), with isUsable as a method (:2145).
Run: python tests/test_artel.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_profiles as tp  # noqa: E402
import test_profile_files as tpf  # noqa: E402

ARTEL = r"""
GRID = true
ComponentType = { DryingCraftLogic = "DryingCraftLogic" }
PMK = {
    Well = { isPowered = function(obj) return GRID end },
    Trade = { gridPowered = function(obj) return GRID end },
    QBase = { squarePowered = function(sq) return GRID end },
}
function PMK.Trade.powerSource(obj)
    if PMK.Trade.gridPowered(obj) then return "grid" end
    if obj.battery then return "batt" end
    return "none"
end
function PMK.QBase.hasPower(obj)
    if not obj then return false end
    return PMK.QBase.squarePowered(obj:getSquare())
end
function PMK.QBase.rebuild(sq, obj, cells, powered, face)
    if powered == nil then powered = PMK.QBase.squarePowered(sq) end
    local o = machine(obj.cid, obj.cut, powered and "Artel_113" or "Artel_117")
    o.sq = sq
    return o
end

-- Batch pause, keyed by the batch object.
local rec = {}
PMK.dryPause = {}
function PMK.dryPause.freeze(crd)
    if not crd then return end
    local e = rec[crd]
    if not e then rec[crd] = { held = true, leases = 1 }; return end
    e.held = true
    e.leases = e.leases + 1
end
function PMK.dryPause.thaw(crd)
    if not crd then return end
    local e = rec[crd]
    if not e then return end
    e.held = false
end
function PMK.dryPause.isHeld(crd)
    local e = crd and rec[crd]
    return (e and e.held) and true or false
end
function leases(crd) return rec[crd] and rec[crd].leases or 0 end

STAGED = {}
function PMK_StationApplyStage(obj, comp, cfg) STAGED[#STAGED + 1] = obj end
function PMK_SublimatorApplyStage(obj, comp)
    if PMK_StationApplyStage then PMK_StationApplyStage(obj, comp, {}) end
end
function PMK_ElectricDryerApplyStage(obj, comp) PMK_StationApplyStage(obj, comp, {}) end

-- One watchdog pass: stations = { { obj, stage = global name, powered, batches = { crd... } } }.
function tick(stations)
    local Pause = PMK and PMK.dryPause
    for _, s in ipairs(stations) do
        for _, crd in ipairs(s.batches) do
            if s.powered then Pause.thaw(crd) else Pause.freeze(crd) end
        end
        local applyStage = _G[s.stage]
        if applyStage then applyStage(s.obj, nil) end
    end
end

-- Drying station: a world object with a DryingCraftLogic component.
function station(id, cut, active, noPower)
    local o = machine(id, cut, id == "ArtelSublimator" and "Artel_52" or "Artel_36")
    local comp = { getActiveCraftCount = function(self) return active end }
    o.hasComponent = function(self, t) return t == ComponentType.DryingCraftLogic end
    o.getComponent = function(self, t) if t == ComponentType.DryingCraftLogic then return comp end end
    if noPower then o:getModData().PMK_EDryerNoPower = true end
    return o
end

-- Chemistry table panel (client).
HALO = {}
function hero() return { setHaloNote = function(self, text) HALO[#HALO + 1] = text end } end
PMK_CraftBenchPanel = {}
PMK_CraftBenchPanel.__index = PMK_CraftBenchPanel
function PMK_CraftBenchPanel:getIsVisible() return self.visible end
function PMK_CraftBenchPanel:isUsable()
    if not self:getIsVisible() then return false end
    if not (self.entity and self.logic and self.component) then return false end
    if not self.powered then return false end
    return true
end
function PMK_CraftBenchPanel:new(player, entity)
    local o = setmetatable({}, self)
    self.__index = self
    o.player, o.entity, o.component, o.logic = player, entity, {}, {}
    o.visible, o.powered = true, GRID
    return o
end
function off(o) o:getModData().LWC_off = true; return o end
"""


def make(side="sp"):
    lua = tp.make(active=False)
    lua.execute(ARTEL + "ACTIVE.ArtelManufactory = true")
    lua.execute('SIDE = "%s"' % side)
    tpf.load_all(lua)
    lua.execute("fire()")
    return lua


class ArtelConsumers(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def watts(self, cid, obj):
        return self.lua.eval("REGISTERED.%s.powerConsumption(%s)" % (cid, obj))

    def test_all_consumers_registered_with_a_switch(self):
        for cid in ("ArtelWellMotor", "ArtelElectricDryer", "ArtelSublimator", "ArtelChemTable",
                    "ArtelTradePost", "ArtelQuantumBase"):
            self.assertIsNotNone(self.lua.eval("REGISTERED.%s" % cid), cid)
            self.assertEqual(self.lua.eval("LiveWireCompat.Switch.ids.%s" % cid), True, cid)

    def test_switched_off_machine_draws_nothing(self):
        self.assertEqual(self.watts("ArtelTradePost", "off(machine('ArtelTradePost'))"), 0)
        self.assertEqual(self.watts("ArtelElectricDryer", "off(station('ArtelElectricDryer', false, 1))"), 0)

    def test_trade_post_draws_only_on_grid(self):
        self.assertEqual(self.watts("ArtelTradePost", "machine('ArtelTradePost')"), 75)
        self.lua.execute("GRID = false")
        self.assertEqual(self.watts("ArtelTradePost", "(function() local m = machine('ArtelTradePost'); m.battery = true; return m end)()"), 0)

    def test_chemistry_table_both_faces(self):
        sprites = list(self.lua.eval("REGISTERED.ArtelChemTable.sprites").values())
        self.assertEqual(sorted(sprites), ["Artel_56", "Artel_58"])

    def test_dryer_bills_heater_only_during_a_batch(self):
        self.assertEqual(self.watts("ArtelElectricDryer", "station('ArtelElectricDryer', false, 0)"), 5)
        self.assertEqual(self.watts("ArtelElectricDryer", "station('ArtelElectricDryer', false, 2)"), 2000)

    def test_sublimator_bills_its_cycle_only_during_a_batch(self):
        self.assertEqual(self.watts("ArtelSublimator", "station('ArtelSublimator', false, 0)"), 5)
        self.assertEqual(self.watts("ArtelSublimator", "station('ArtelSublimator', false, 1)"), 700)

    def test_batch_held_by_artel_bills_idle(self):
        self.assertEqual(self.watts("ArtelSublimator", "station('ArtelSublimator', false, 1, true)"), 5)


class ArtelGates(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_cut_circuit_stops_the_gated_machines(self):
        self.assertEqual(self.lua.eval("PMK.Well.isPowered(machine('ArtelWellMotor', true))"), False)
        self.assertEqual(self.lua.eval("PMK.Trade.gridPowered(machine('ArtelTradePost', true))"), False)
        self.assertEqual(self.lua.eval(
            "(function() local m = machine('ArtelQuantumBase', true); m.sq = square(m); "
            "return PMK.QBase.hasPower(m) end)()"), False)

    def test_switched_off_well_runs_at_hand_pump_speed(self):
        self.assertEqual(self.lua.eval("PMK.Well.isPowered(off(machine('ArtelWellMotor')))"), False)
        self.assertEqual(self.lua.eval("PMK.Well.isPowered(machine('ArtelWellMotor'))"), True)

    def test_trade_post_battery_survives_a_cut(self):
        self.assertEqual(self.lua.eval(
            "PMK.Trade.powerSource((function() local m = machine('ArtelTradePost', true); m.battery = true; return m end)())"),
            "batt")

    def test_other_well_stages_keep_artel_answer(self):
        self.assertEqual(self.lua.eval("PMK.Well.isPowered({ cut = true })"), True)


class ArtelQuantumBase(unittest.TestCase):
    def setUp(self):
        self.lua = make()

    def test_lit_and_dark_sprites_are_the_same_consumer(self):
        sprites = list(self.lua.eval("REGISTERED.ArtelQuantumBase.sprites").values())
        for s in ("Artel_112", "Artel_116", "Artel_117", "Artel_120", "Artel_130", "Artel_142", "Artel_143"):
            self.assertIn(s, sprites)
        self.assertNotIn("Artel_121", sprites)
        self.assertEqual(len(sprites), 28)

    def test_switched_off_base_locks_its_cells(self):
        self.assertEqual(self.lua.eval(
            "(function() local m = off(machine('ArtelQuantumBase')); m.sq = square(m); "
            "return PMK.QBase.hasPower(m) end)()"), False)

    def test_rebuild_keeps_the_switch_off(self):
        self.lua.execute("OLD = off(machine('ArtelQuantumBase')); OLD.sq = square(OLD)")
        self.assertEqual(self.lua.eval("PMK.QBase.rebuild(OLD.sq, OLD, {}).sprite"), "Artel_117")
        self.assertEqual(self.lua.eval("LiveWireCompat.Switch.isOff(PMK.QBase.rebuild(OLD.sq, OLD, {}))"), True)

    def test_rebuild_of_a_base_that_is_on_adds_nothing(self):
        self.lua.execute("OLD = machine('ArtelQuantumBase'); OLD.sq = square(OLD)")
        self.assertEqual(self.lua.eval("PMK.QBase.rebuild(OLD.sq, OLD, {}):hasModData()"), False)

    def test_rebuild_keeps_artel_arguments_and_result(self):
        self.lua.execute("OLD = machine('ArtelQuantumBase'); OLD.sq = square(OLD)")
        self.assertEqual(self.lua.eval("PMK.QBase.rebuild(OLD.sq, OLD, {}, false).sprite"), "Artel_117")


class ArtelDryingPause(unittest.TestCase):
    def setUp(self):
        self.lua = make(side="server")
        self.lua.execute("CRD = {}")

    def held(self, crd="CRD"):
        return self.lua.eval("PMK.dryPause.isHeld(%s)" % crd)

    def test_running_batch_of_a_switched_off_dryer_pauses(self):
        self.lua.execute("tick({ { obj = off(station('ArtelElectricDryer')), stage = 'PMK_ElectricDryerApplyStage',"
                         " powered = true, batches = { CRD } } })")
        self.assertTrue(self.held())

    def test_cut_sublimator_keeps_its_batch_paused_and_renews_the_lease(self):
        self.lua.execute("S = { obj = station('ArtelSublimator', true), stage = 'PMK_SublimatorApplyStage',"
                         " powered = true, batches = { CRD } }")
        self.lua.execute("tick({ S }); tick({ S })")
        self.assertTrue(self.held())
        self.assertEqual(self.lua.eval("leases(CRD)"), 2)

    def test_batch_resumes_when_switched_back_on(self):
        self.lua.execute("S = { obj = off(station('ArtelElectricDryer')), stage = 'PMK_ElectricDryerApplyStage',"
                         " powered = true, batches = { CRD } }")
        self.lua.execute("tick({ S }); S.obj:getModData().LWC_off = nil; tick({ S })")
        self.assertFalse(self.held())

    def test_each_station_decides_for_its_own_batches(self):
        self.lua.execute("A, B = {}, {}; PMK.dryPause.freeze(A); PMK.dryPause.freeze(B)")
        self.lua.execute("tick({ { obj = off(station('ArtelSublimator')), stage = 'PMK_SublimatorApplyStage',"
                         " powered = true, batches = { A } },"
                         " { obj = station('ArtelElectricDryer'), stage = 'PMK_ElectricDryerApplyStage',"
                         " powered = true, batches = { B } } })")
        self.assertTrue(self.held("A"))
        self.assertFalse(self.held("B"))

    def test_artel_freeze_without_power_is_untouched(self):
        self.lua.execute("tick({ { obj = station('ArtelElectricDryer'), stage = 'PMK_ElectricDryerApplyStage',"
                         " powered = false, batches = { CRD } } })")
        self.assertTrue(self.held())

    def test_stage_global_still_runs_with_its_arguments(self):
        self.lua.execute("S = station('ArtelElectricDryer'); tick({ { obj = S, stage = 'PMK_ElectricDryerApplyStage',"
                         " powered = true, batches = {} } })")
        self.assertEqual(self.lua.eval("STAGED[1] == S"), True)

    def test_installed_once(self):
        self.lua.execute("T1, A1 = PMK.dryPause.thaw, PMK_StationApplyStage; fire()")
        self.assertEqual(self.lua.eval("PMK.dryPause.thaw == T1 and PMK_StationApplyStage == A1"), True)

    def test_not_installed_on_a_client(self):
        lua = make(side="client")
        lua.execute("CRD = {}; PMK.dryPause.freeze(CRD); PMK.dryPause.thaw(CRD)")
        self.assertEqual(lua.eval("PMK.dryPause.isHeld(CRD)"), False)


class ArtelChemistryTable(unittest.TestCase):
    def setUp(self):
        self.lua = make(side="client")

    def usable(self, entity):
        return self.lua.eval("PMK_CraftBenchPanel:new(hero(), %s):isUsable()" % entity)

    def test_powered_table_is_usable(self):
        self.assertEqual(self.usable("machine('ArtelChemTable')"), True)

    def test_cut_table_refuses_and_says_why(self):
        self.assertEqual(self.usable("machine('ArtelChemTable', true)"), False)
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_NoPower")

    def test_switched_off_table_refuses_and_says_why(self):
        self.assertEqual(self.usable("off(machine('ArtelChemTable'))"), False)
        self.assertEqual(self.lua.eval("HALO[1]"), "IGUI_LWC_MachineOff")

    def test_artel_refusal_is_kept(self):
        self.lua.execute("GRID = false")
        self.assertEqual(self.usable("machine('ArtelChemTable')"), False)
        self.assertEqual(self.lua.eval("#HALO"), 0)

    def test_not_installed_on_the_server(self):
        lua = make(side="server")
        self.assertEqual(lua.eval("PMK_CraftBenchPanel:new(hero(), machine('ArtelChemTable', true)):isUsable()"), True)


if __name__ == "__main__":
    unittest.main()
