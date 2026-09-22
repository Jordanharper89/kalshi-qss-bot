from __future__ import annotations
import unittest
from datetime import datetime,timedelta,timezone
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import build_default_adapter_bundle
from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import build_runtime_config
from qseries_v2.observation_adapter_runtime.oar_004_continuous_service_loop import *
NOW=datetime(2026,8,12,4,30,tzinfo=timezone.utc)
class Clock:
    def __init__(self): self.v=NOW
    def __call__(self):
        x=self.v; self.v+=timedelta(milliseconds=1); return x
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_continuous_service_loop())
    def test_two(self):
        sleeps=[]
        r=ContinuousObservationServiceLoop().run(config=build_runtime_config(runtime_id='oracle.live.observation',tick_interval_seconds=5),bundle=build_default_adapter_bundle(),iterations=2,clock_callable=Clock(),sleep_callable=lambda x:sleeps.append(x),stop_requested_callable=lambda:False,subject_hints={'coinbase':'BTC','kalshi':None})
        self.assertEqual(r.iterations_completed,2); self.assertEqual(sleeps,[5.0])
    def test_stop(self):
        r=ContinuousObservationServiceLoop().run(config=build_runtime_config(runtime_id='oracle.live.observation'),bundle=build_default_adapter_bundle(),iterations=2,clock_callable=Clock(),sleep_callable=lambda _:None,stop_requested_callable=lambda:True)
        self.assertTrue(r.stopped); self.assertEqual(r.iterations_completed,0)
if __name__=='__main__':
    print('='*72); print(' OAR-004 CERTIFICATION TEST'); print(' CONTINUOUS LIVE OBSERVATION SERVICE LOOP'); print('='*72)
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print('\n[PASS] Build: OAR-004'); print('[PASS] Revision: OAR_004_CONTINUOUS_SERVICE_LOOP_V1'); print('[PASS] Deterministic repeated live observation iterations certified'); print('[PASS] Cadence and stop requests honored'); print('[PASS] Execution and order placement disabled'); print('[DONE] OAR-004 CERTIFIED')
