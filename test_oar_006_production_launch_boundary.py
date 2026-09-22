from __future__ import annotations
import unittest
from datetime import datetime,timedelta,timezone
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import build_default_adapter_bundle
from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import build_runtime_config
from qseries_v2.observation_adapter_runtime.oar_006_production_launch_boundary import *
NOW=datetime(2026,8,12,4,40,tzinfo=timezone.utc)
class Clock:
    def __init__(self): self.v=NOW
    def __call__(self): x=self.v; self.v+=timedelta(milliseconds=1); return x
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_production_launch_boundary())
    def test_launch(self):
        rec,res=ProductionLiveObservationLauncher().launch(config=build_runtime_config(runtime_id='oracle.live.observation.production'),bundle=build_default_adapter_bundle(),iterations=1,clock_callable=Clock(),sleep_callable=lambda _:None,stop_requested_callable=lambda:False,subject_hints={'coinbase':'BTC','kalshi':None})
        self.assertEqual(rec.iterations_completed,1); self.assertEqual(rec.adapter_ids,('adapter.crypto.observe.v1','adapter.kalshi.observe.v1')); self.assertEqual(res.iterations_completed,1)
    def test_safety(self):
        rec,_=ProductionLiveObservationLauncher().launch(config=build_runtime_config(runtime_id='oracle.live.observation.production'),bundle=build_default_adapter_bundle(),iterations=1,clock_callable=Clock(),sleep_callable=lambda _:None,stop_requested_callable=lambda:True)
        self.assertTrue(rec.read_only); self.assertFalse(rec.execution_allowed); self.assertFalse(rec.order_placement_allowed); self.assertFalse(rec.publication_allowed)
if __name__=='__main__':
    print('='*72); print(' OAR-006 CERTIFICATION TEST'); print(' PRODUCTION LIVE OBSERVATION LAUNCH BOUNDARY'); print('='*72)
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print('\n[PASS] Build: OAR-006'); print('[PASS] Revision: OAR_006_PRODUCTION_LAUNCH_BOUNDARY_V1'); print('[PASS] Kalshi and crypto enter one production live-observation launch boundary'); print('[PASS] Continuous service loop reachable through production launcher'); print('[PASS] Publication, execution, and order placement disabled'); print('[DONE] OAR-006 CERTIFIED')
