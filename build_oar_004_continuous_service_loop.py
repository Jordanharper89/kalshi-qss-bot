from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/'qseries_v2'/'observation_adapter_runtime'
OAD=ROOT/'qseries_v2'/'observation_adapters'
OI=ROOT/'qseries_v2'/'observation_intelligence'
UPSTREAMS=(PACKAGE/'oar_001_runtime_foundation.py',PACKAGE/'oar_002_adapter_scheduler.py',PACKAGE/'oar_003_multi_adapter_runner.py',OAD/'oad_006_default_adapter_bundle.py',OI/'oi_final_certification_freeze.py')
MODULE=PACKAGE/'oar_004_continuous_service_loop.py'
INIT=PACKAGE/'__init__.py'
TEST=ROOT/'test_oar_004_continuous_service_loop.py'
MODULE_SOURCE=r'''from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import CertifiedDefaultAdapterBundle
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig
from .oar_002_adapter_scheduler import DeterministicAdapterScheduler
from .oar_003_multi_adapter_runner import MultiAdapterObservationRunner, MultiAdapterRunResult

BUILD_ID='OAR-004'
OAR_004_REVISION='OAR_004_CONTINUOUS_SERVICE_LOOP_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False
ORDER_PLACEMENT_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ContinuousServiceLoopResult:
    runtime_id:str
    iterations_requested:int
    iterations_completed:int
    run_results:tuple[MultiAdapterRunResult,...]
    stopped:bool
    read_only:bool
    execution_allowed:bool

class ContinuousObservationServiceLoop:
    read_only=True
    execution_allowed=False
    order_placement_allowed=False

    def run(self,*,config:LiveObservationRuntimeConfig,bundle:CertifiedDefaultAdapterBundle,iterations:int,clock_callable:Callable[[],datetime],sleep_callable:Callable[[float],None],stop_requested_callable:Callable[[],bool],subject_hints:dict[str,str|None]|None=None)->ContinuousServiceLoopResult:
        if not isinstance(config,LiveObservationRuntimeConfig): raise TypeError('config must be LiveObservationRuntimeConfig')
        if not isinstance(bundle,CertifiedDefaultAdapterBundle): raise TypeError('bundle must be CertifiedDefaultAdapterBundle')
        if not isinstance(iterations,int) or iterations<1: raise ValueError('iterations must be positive')
        if not callable(clock_callable) or not callable(sleep_callable) or not callable(stop_requested_callable): raise TypeError('runtime callables must be callable')
        scheduler=DeterministicAdapterScheduler(); runner=MultiAdapterObservationRunner(); results=[]; stopped=False
        for n in range(1,iterations+1):
            if stop_requested_callable(): stopped=True; break
            at=clock_callable()
            if not isinstance(at,datetime) or at.tzinfo is None: raise ValueError('clock must return timezone-aware datetime')
            schedule=scheduler.schedule(bundle=bundle,iteration_number=n,scheduled_at=at.astimezone(timezone.utc),subject_hints=subject_hints)
            results.append(runner.run(bundle=bundle,schedule=schedule,clock_callable=clock_callable))
            if n<iterations:
                if stop_requested_callable(): stopped=True; break
                sleep_callable(float(config.tick_interval_seconds))
        return ContinuousServiceLoopResult(config.runtime_id,iterations,len(results),tuple(results),stopped,True,False)

def verify_continuous_service_loop()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and ORDER_PLACEMENT_ALLOWED is False
    return True
'''
TEST_SOURCE=r'''from __future__ import annotations
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
'''
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t):
    t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding='utf-8',newline='\n'); print('[PASS] Wrote:',x.relative_to(ROOT))
def main():
    print('='*72); print(' OAR-004 INSTALLER'); print(' CONTINUOUS LIVE OBSERVATION SERVICE LOOP'); print('='*72); print('[BOOT] Revision: OAR_004_CONTINUOUS_SERVICE_LOOP_INSTALLER_V1'); print('[ROOT]',ROOT)
    for x in UPSTREAMS:
        if not x.is_file(): raise RuntimeError(f'Certified upstream missing: {x}')
    h={x:sha(x) for x in UPSTREAMS}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding='utf-8') if INIT.exists() else ''; exp='from .oar_004_continuous_service_loop import *'
        if exp not in cur.splitlines():
            if cur and not cur.endswith('\n'): cur+='\n'
            cur+=exp+'\n'; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding='utf-8',newline='\n')
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f'Certified upstream changed: {x.name}')
        print('[PASS] Certified upstream remained unchanged'); print('[PASS] Deterministic install hash:',hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest()); print('[DONE] OAR-004 INSTALLATION COMPLETE'); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=='__main__': raise SystemExit(main())
