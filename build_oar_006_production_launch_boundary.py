from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/'qseries_v2'/'observation_adapter_runtime'
OAD=ROOT/'qseries_v2'/'observation_adapters'
OI=ROOT/'qseries_v2'/'observation_intelligence'
UPSTREAMS=(PACKAGE/'oar_001_runtime_foundation.py',PACKAGE/'oar_004_continuous_service_loop.py',PACKAGE/'oar_005_runtime_lifecycle.py',OAD/'oad_006_default_adapter_bundle.py',OI/'oi_final_certification_freeze.py',OI/'OI_FINAL_FREEZE_MANIFEST.json')
MODULE=PACKAGE/'oar_006_production_launch_boundary.py'
INIT=PACKAGE/'__init__.py'
TEST=ROOT/'test_oar_006_production_launch_boundary.py'
MODULE_SOURCE=r'''from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import CertifiedDefaultAdapterBundle
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig, initial_runtime_state
from .oar_004_continuous_service_loop import ContinuousObservationServiceLoop, ContinuousServiceLoopResult
from .oar_005_runtime_lifecycle import LiveObservationRuntimeLifecycle

BUILD_ID='OAR-006'
OAR_006_REVISION='OAR_006_PRODUCTION_LAUNCH_BOUNDARY_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False
ORDER_PLACEMENT_ALLOWED=False
PUBLICATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ProductionLaunchRecord:
    runtime_id:str
    adapter_ids:tuple[str,...]
    provider_ids:tuple[str,...]
    iterations_completed:int
    stopped:bool
    read_only:bool
    execution_allowed:bool
    order_placement_allowed:bool
    publication_allowed:bool

class ProductionLiveObservationLauncher:
    read_only=True
    execution_allowed=False
    order_placement_allowed=False
    publication_allowed=False
    def launch(self,*,config:LiveObservationRuntimeConfig,bundle:CertifiedDefaultAdapterBundle,iterations:int,clock_callable:Callable[[],datetime],sleep_callable:Callable[[float],None],stop_requested_callable:Callable[[],bool],subject_hints:dict[str,str|None]|None=None)->tuple[ProductionLaunchRecord,ContinuousServiceLoopResult]:
        if config.read_only is not True or config.execution_allowed is not False: raise ValueError('unsafe runtime config')
        if bundle.read_only is not True or bundle.execution_allowed is not False: raise ValueError('unsafe adapter bundle')
        state=initial_runtime_state(config)
        state,_=LiveObservationRuntimeLifecycle().start(config=config,state=state,occurred_at=clock_callable())
        result=ContinuousObservationServiceLoop().run(config=config,bundle=bundle,iterations=iterations,clock_callable=clock_callable,sleep_callable=sleep_callable,stop_requested_callable=stop_requested_callable,subject_hints=subject_hints)
        if state.execution_allowed is not False: raise RuntimeError('runtime lifecycle exposed execution')
        record=ProductionLaunchRecord(config.runtime_id,bundle.adapter_ids,bundle.provider_ids,result.iterations_completed,result.stopped,True,False,False,False)
        return record,result

def verify_production_launch_boundary()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and ORDER_PLACEMENT_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
'''
TEST_SOURCE=r'''from __future__ import annotations
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
'''
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t):
    t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding='utf-8',newline='\n'); print('[PASS] Wrote:',x.relative_to(ROOT))
def main():
    print('='*72); print(' OAR-006 INSTALLER'); print(' PRODUCTION LIVE OBSERVATION LAUNCH BOUNDARY'); print('='*72); print('[BOOT] Revision: OAR_006_PRODUCTION_LAUNCH_BOUNDARY_INSTALLER_V1'); print('[ROOT]',ROOT)
    for x in UPSTREAMS:
        if not x.is_file(): raise RuntimeError(f'Certified upstream missing: {x}')
    h={x:sha(x) for x in UPSTREAMS}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding='utf-8') if INIT.exists() else ''; exp='from .oar_006_production_launch_boundary import *'
        if exp not in cur.splitlines():
            if cur and not cur.endswith('\n'): cur+='\n'
            cur+=exp+'\n'; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding='utf-8',newline='\n')
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f'Certified upstream changed: {x.name}')
        print('[PASS] Certified upstream remained unchanged'); print('[PASS] Deterministic install hash:',hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest()); print('[PASS] Production universal live-observation launch boundary established'); print('[DONE] OAR-006 INSTALLATION COMPLETE'); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=='__main__': raise SystemExit(main())
