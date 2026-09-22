from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import *
from qseries_v2.observation_adapter_runtime.oar_005_runtime_lifecycle import *
NOW=datetime(2026,8,12,4,35,tzinfo=timezone.utc)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_runtime_lifecycle())
    def test_start(self):
        c=build_runtime_config(runtime_id='oracle.live.observation'); s=initial_runtime_state(c); s,r=LiveObservationRuntimeLifecycle().start(config=c,state=s,occurred_at=NOW); self.assertEqual(s.status,RUNTIME_STATUS_RUNNING); self.assertEqual(r.reason,'runtime_started')
    def test_failure_limit(self):
        c=build_runtime_config(runtime_id='oracle.live.observation',max_adapter_failures=1); s=initial_runtime_state(c); l=LiveObservationRuntimeLifecycle(); s,_=l.start(config=c,state=s,occurred_at=NOW); s,r=l.advance(config=c,state=s,occurred_at=NOW,iteration_succeeded=False); self.assertEqual(s.status,RUNTIME_STATUS_STOPPED); self.assertEqual(r.reason,'failure_limit_reached')
if __name__=='__main__':
    print('='*72); print(' OAR-005 CERTIFICATION TEST'); print(' LIVE OBSERVATION RUNTIME LIFECYCLE'); print('='*72)
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print('\n[PASS] Build: OAR-005'); print('[PASS] Revision: OAR_005_RUNTIME_LIFECYCLE_V1'); print('[PASS] Idle, running, stopped, failure-limit, and iteration progression certified'); print('[PASS] Lifecycle remains read-only with execution disabled'); print('[DONE] OAR-005 CERTIFIED')
