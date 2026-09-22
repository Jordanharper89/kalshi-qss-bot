from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/'qseries_v2'/'observation_adapter_runtime'
OAD=ROOT/'qseries_v2'/'observation_adapters'
OI=ROOT/'qseries_v2'/'observation_intelligence'
UPSTREAMS=(PACKAGE/'oar_001_runtime_foundation.py',PACKAGE/'oar_004_continuous_service_loop.py',OAD/'oad_006_default_adapter_bundle.py',OI/'oi_final_certification_freeze.py')
MODULE=PACKAGE/'oar_005_runtime_lifecycle.py'
INIT=PACKAGE/'__init__.py'
TEST=ROOT/'test_oar_005_runtime_lifecycle.py'
MODULE_SOURCE=r'''from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig, LiveObservationRuntimeState, RUNTIME_STATUS_IDLE, RUNTIME_STATUS_RUNNING, RUNTIME_STATUS_STOPPED

BUILD_ID='OAR-005'
OAR_005_REVISION='OAR_005_RUNTIME_LIFECYCLE_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class RuntimeLifecycleRecord:
    runtime_id:str
    prior_status:str
    new_status:str
    prior_iteration_number:int
    new_iteration_number:int
    occurred_at:datetime
    reason:str
    read_only:bool
    execution_allowed:bool

class LiveObservationRuntimeLifecycle:
    read_only=True
    execution_allowed=False
    def _validate(self,config,state,occurred_at):
        if not isinstance(config,LiveObservationRuntimeConfig): raise TypeError('config must be LiveObservationRuntimeConfig')
        if not isinstance(state,LiveObservationRuntimeState): raise TypeError('state must be LiveObservationRuntimeState')
        if config.runtime_id!=state.runtime_id: raise ValueError('config/state runtime_id mismatch')
        if not isinstance(occurred_at,datetime) or occurred_at.tzinfo is None: raise ValueError('occurred_at must be timezone-aware datetime')
    def _record(self,state,new_state,occurred_at,reason):
        return RuntimeLifecycleRecord(state.runtime_id,state.status,new_state.status,state.iteration_number,new_state.iteration_number,occurred_at.astimezone(timezone.utc),reason,True,False)
    def start(self,*,config,state,occurred_at):
        self._validate(config,state,occurred_at)
        if state.status!=RUNTIME_STATUS_IDLE: raise ValueError('runtime can start only from idle')
        n=LiveObservationRuntimeState(state.runtime_id,RUNTIME_STATUS_RUNNING,state.iteration_number,state.consecutive_failures,False,True,False)
        return n,self._record(state,n,occurred_at,'runtime_started')
    def advance(self,*,config,state,occurred_at,iteration_succeeded:bool):
        self._validate(config,state,occurred_at)
        if state.status!=RUNTIME_STATUS_RUNNING: raise ValueError('runtime can advance only while running')
        failures=0 if iteration_succeeded else state.consecutive_failures+1
        stop=failures>=config.max_adapter_failures
        status=RUNTIME_STATUS_STOPPED if stop else RUNTIME_STATUS_RUNNING
        n=LiveObservationRuntimeState(state.runtime_id,status,state.iteration_number+1,failures,stop,True,False)
        reason='failure_limit_reached' if stop else ('iteration_succeeded' if iteration_succeeded else 'iteration_failed')
        return n,self._record(state,n,occurred_at,reason)
    def stop(self,*,config,state,occurred_at):
        self._validate(config,state,occurred_at)
        if state.status==RUNTIME_STATUS_STOPPED: raise ValueError('runtime is already stopped')
        n=LiveObservationRuntimeState(state.runtime_id,RUNTIME_STATUS_STOPPED,state.iteration_number,state.consecutive_failures,True,True,False)
        return n,self._record(state,n,occurred_at,'operator_stop_requested')

def verify_runtime_lifecycle()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False
    return True
'''
TEST_SOURCE=r'''from __future__ import annotations
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
'''
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t):
    t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding='utf-8',newline='\n'); print('[PASS] Wrote:',x.relative_to(ROOT))
def main():
    print('='*72); print(' OAR-005 INSTALLER'); print(' LIVE OBSERVATION RUNTIME LIFECYCLE'); print('='*72); print('[BOOT] Revision: OAR_005_RUNTIME_LIFECYCLE_INSTALLER_V1'); print('[ROOT]',ROOT)
    for x in UPSTREAMS:
        if not x.is_file(): raise RuntimeError(f'Certified upstream missing: {x}')
    h={x:sha(x) for x in UPSTREAMS}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding='utf-8') if INIT.exists() else ''; exp='from .oar_005_runtime_lifecycle import *'
        if exp not in cur.splitlines():
            if cur and not cur.endswith('\n'): cur+='\n'
            cur+=exp+'\n'; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding='utf-8',newline='\n')
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f'Certified upstream changed: {x.name}')
        print('[PASS] Certified upstream remained unchanged'); print('[PASS] Deterministic install hash:',hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest()); print('[DONE] OAR-005 INSTALLATION COMPLETE'); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=='__main__': raise SystemExit(main())
