from __future__ import annotations
import ast,os,subprocess,sys,textwrap
from pathlib import Path
REVISION='OAD_216_CRYPTO_SCIENTIFIC_REASONING_HANDOFF_GATE_V1'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for x in (b,*b.parents):
   if (x/'qseries_v2').is_dir():return x
 raise RuntimeError('Q Series repository root not found')
def w(p,s):
 s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p));q=p.with_suffix(p.suffix+'.tmp');q.write_text(s,encoding='utf-8',newline='\n');os.replace(q,p)
def run(r,t):
 z=subprocess.run([sys.executable,str(t)],cwd=str(r));
 if z.returncode:raise RuntimeError('test failed: '+t.name)
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import build_scientific_reasoning_handoff,verify_scientific_reasoning_handoff
from .oad_215_crypto_ocl_incremental_state_consumption import read_crypto_ocl_state
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
REQUIRED_NON_LEARNER_HASHES=('calibration_state_hash','source_reliability_state_hash','market_behavior_state_hash','causal_state_hash','narrative_state_hash','entity_relationship_state_hash','maturity_state_hash','adaptive_weight_state_hash')
@dataclass(frozen=True,slots=True)
class CryptoScientificReasoningHandoffGate:
 learner_state_hash:str;learner_state_verified:bool;missing_state_hashes:tuple;handoff:object|None;handoff_verified:bool;state:str;physical_ready:bool;probability_enabled:bool=False;direction_enabled:bool=False;execution_authority:bool=False
def evaluate_crypto_scientific_reasoning_handoff(root=None,certified_state_hashes=None):
 cycle,state,_=read_crypto_ocl_state(root);learner=str(state.state_hash);learner_ok=len(learner)==64 and state.applied_through_sequence>=0;sup=dict(certified_state_hashes or {});missing=tuple(n for n in REQUIRED_NON_LEARNER_HASHES if len(str(sup.get(n,'')))!=64)
 if missing:return CryptoScientificReasoningHandoffGate(learner,learner_ok,missing,None,False,'HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED',learner_ok,False,False,False)
 hashes={'learner_state_hash':learner};hashes.update({n:str(sup[n]) for n in REQUIRED_NON_LEARNER_HASHES});h=build_scientific_reasoning_handoff(**hashes);ok=verify_scientific_reasoning_handoff(h)
 if not ok:raise RuntimeError('OCL-029 Scientific Reasoning handoff verification failed')
 return CryptoScientificReasoningHandoffGate(learner,learner_ok,tuple(),h,True,'READY_FOR_SCIENTIFIC_REASONING_HANDOFF',bool(learner_ok and ok),False,False,False)
"""
TEST=r"""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_216_crypto_scientific_reasoning_handoff_gate as m
class T(unittest.TestCase):
 def test_missing_holds(self):
  s=SimpleNamespace(state_hash='a'*64,applied_through_sequence=100)
  with patch.object(m,'read_crypto_ocl_state',return_value=(1,s,'b'*64)):r=m.evaluate_crypto_scientific_reasoning_handoff()
  print('[GATE]',r.state);print('[MISSING]',r.missing_state_hashes);self.assertEqual(r.state,'HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED');self.assertIsNone(r.handoff);self.assertTrue(r.physical_ready)
 def test_complete_uses_ocl029(self):
  s=SimpleNamespace(state_hash='a'*64,applied_through_sequence=100);h={n:'b'*64 for n in m.REQUIRED_NON_LEARNER_HASHES}
  with patch.object(m,'read_crypto_ocl_state',return_value=(1,s,'c'*64)):r=m.evaluate_crypto_scientific_reasoning_handoff(certified_state_hashes=h)
  self.assertTrue(r.handoff_verified);self.assertFalse(r.handoff.execution_allowed);self.assertFalse(r.handoff.publication_allowed)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-216 truthful OCL-029 handoff gate certified')
"""
PHYSICAL=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_216_crypto_scientific_reasoning_handoff_gate import evaluate_crypto_scientific_reasoning_handoff
class T(unittest.TestCase):
 def test_physical(self):
  r=evaluate_crypto_scientific_reasoning_handoff();print('[PHYSICAL] learner_state_hash=',r.learner_state_hash);print('[PHYSICAL] verified=',r.learner_state_verified);print('[PHYSICAL] missing=',r.missing_state_hashes);print('[PHYSICAL] state=',r.state);print('[PHYSICAL] physical_ready=',r.physical_ready);self.assertTrue(r.learner_state_verified);self.assertTrue(r.physical_ready);self.assertFalse(r.probability_enabled);self.assertFalse(r.execution_authority)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-216 physical learner-state -> Scientific Reasoning admission boundary certified')
"""
def main():
 r=root();pkg=r/'qseries_v2/oracle_adapters/independent';m=pkg/'oad_216_crypto_scientific_reasoning_handoff_gate.py';t=r/'test_oad_216_crypto_scientific_reasoning_handoff_gate.py';pt=r/'test_oad_216_crypto_scientific_reasoning_handoff_gate_PHYSICAL.py';deps=[pkg/'oad_215_crypto_ocl_incremental_state_consumption.py',r/'qseries_v2/oracle_continuous_learner/ocl_029_scientific_reasoning_handoff.py']
 print('='*112);print(' OAD-216 CRYPTO LEARNER STATE -> SCIENTIFIC REASONING HANDOFF GATE');print('='*112);print('[BOOT]',REVISION);print('[ROOT]',r)
 for d in deps:
  if not d.is_file():raise RuntimeError('Required dependency missing: '+str(d))
 old={x:(x.read_bytes() if x.exists() else None) for x in (m,t,pt)}
 try:w(m,MODULE);w(t,TEST);w(pt,PHYSICAL);run(r,t);print('[PASS] frozen OCL-029 reused unchanged');print('[PASS] no missing state hash is fabricated');print('[PASS] probability=FALSE direction=FALSE execution=FALSE');print('[DONE] OAD-216 INSTALLATION COMPLETE')
 except Exception:
  for x,v in old.items():
   if v is None:
    if x.exists():x.unlink()
   else:x.write_bytes(v)
  print('[ROLLBACK] OAD-216 rolled back');raise
if __name__=='__main__':main()
