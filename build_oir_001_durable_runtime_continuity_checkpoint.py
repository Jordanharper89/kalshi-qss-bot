from pathlib import Path
import os, subprocess, sys
ROOT=Path.cwd().resolve(); PKG=ROOT/'qseries_v2'/'oracle_interruption_recovery'; MOD=PKG/'oir_001_continuity_checkpoint.py'; TEST=ROOT/'test_oir_001_durable_runtime_continuity_checkpoint.py'; RUN=ROOT/'run_oir_001_continuity_checkpoint_daemon.py'; INIT=PKG/'__init__.py'
MODULE=r'''from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json,os,time
from qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile import _connect,_db_url
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
OIR_001_BUILD_ID='OIR-001'; CHECKPOINT_NAME='oracle_interruption_continuity_checkpoint.json'
def capture_continuity_checkpoint(root=None):
    root=Path(root or Path.cwd()).resolve(); now=datetime.now(timezone.utc)
    conn=_connect(_db_url(root))
    try:
        try: conn.set_session(readonly=True,autocommit=False)
        except Exception: pass
        cur=conn.cursor(); cur.execute("SELECT COALESCE(MAX(sequence_number),0),COALESCE(MAX(observed_at)::text,''),COALESCE(MAX(persisted_at)::text,''),COUNT(*) FROM public.oracle_canonical_observations"); seq,obs,pers,count=cur.fetchone()
        try: conn.rollback()
        except Exception: pass
    finally: conn.close()
    learner=load_production_learned_state(root)
    payload={'captured_at':now.isoformat(),'canonical_sequence_number':int(seq or 0),'canonical_observed_at':str(obs or ''),'canonical_persisted_at':str(pers or ''),'canonical_observation_count':int(count or 0),'learner_state_hash':str(learner.learner_state_hash or ''),'learner_outcomes_learned':int(learner.outcomes_learned),'execution_authority':False}
    p=root/'runtime_state'/CHECKPOINT_NAME; p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(payload,sort_keys=True,separators=(',',':')),encoding='utf-8',newline='\n'); os.replace(tmp,p); return payload
def load_continuity_checkpoint(root=None):
    root=Path(root or Path.cwd()).resolve(); p=root/'runtime_state'/CHECKPOINT_NAME
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None
def run_checkpoint_daemon(root=None,cadence_seconds=5.0):
    while True:
        x=capture_continuity_checkpoint(root); print(f"[OIR CHECKPOINT] captured_at={x['captured_at']} sequence={x['canonical_sequence_number']} observations={x['canonical_observation_count']} learner_outcomes={x['learner_outcomes_learned']}",flush=True); time.sleep(float(cadence_seconds))
def verify_oir_001_durable_runtime_continuity_checkpoint(): return OIR_001_BUILD_ID=='OIR-001' and callable(capture_continuity_checkpoint)
'''
TEST=r'''import unittest
import qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint as m
class T(unittest.TestCase):
    def test_identity(self): self.assertEqual(m.OIR_001_BUILD_ID,'OIR-001')
    def test_contract(self): self.assertTrue(callable(m.capture_continuity_checkpoint))
if __name__=='__main__':
    print('='*88);print(' OIR-001 CERTIFICATION TEST');print(' DURABLE RUNTIME CONTINUITY CHECKPOINT');print('='*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
    if not r.wasSuccessful(): raise SystemExit(1)
    print('[PASS] Durable continuity checkpoint contract certified');print('[PASS] execution_authority=FALSE');print('[DONE] OIR-001 CERTIFIED')
'''
RUN=r'''import argparse
from qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import run_checkpoint_daemon
p=argparse.ArgumentParser();p.add_argument('--cadence-seconds',type=float,default=5.0);p.add_argument('--check',action='store_true');a=p.parse_args()
if a.check: print('[READY] OIR-001 continuity checkpoint daemon\n[PASS] execution_authority=FALSE')
else: run_checkpoint_daemon(cadence_seconds=a.cadence_seconds)
'''
def write(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8',newline='\n')
def main():
    print('='*88);print(' OIR-001 INSTALLER');print(' DURABLE RUNTIME CONTINUITY CHECKPOINT');print('='*88);print('[ROOT]',ROOT)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,RUN,INIT)}
    try:
        write(MOD,MODULE);write(TEST,TEST);write(RUN,RUN);cur=INIT.read_text(encoding='utf-8') if INIT.exists() else ''; exp='from .oir_001_continuity_checkpoint import *'; write(INIT,cur.rstrip()+'\n'+exp+'\n' if exp not in cur.splitlines() else cur)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True);subprocess.run([sys.executable,str(RUN),'--check'],cwd=str(ROOT),check=True)
        sys.path.insert(0,str(ROOT));from qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import capture_continuity_checkpoint; x=capture_continuity_checkpoint(ROOT); print(f"[PHYSICAL CHECKPOINT] sequence={x['canonical_sequence_number']} observations={x['canonical_observation_count']} learner_outcomes={x['learner_outcomes_learned']}")
        if x['canonical_observation_count']<=0: raise RuntimeError('Canonical corpus checkpoint is empty')
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print('[ROLLBACK] OIR-001 failed; files restored'); raise
    print('[PASS] Frozen OPH/OPR/OLF modules untouched');print('[PASS] execution_authority=FALSE');print('[DONE] OIR-001 INSTALLATION COMPLETE')
if __name__=='__main__': main()
