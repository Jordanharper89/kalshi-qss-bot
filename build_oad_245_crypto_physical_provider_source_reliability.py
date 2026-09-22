from pathlib import Path
import os,sys,subprocess
EXPECTED='build_oad_245_crypto_physical_provider_source_reliability.py'; MODULE='from dataclasses import dataclass\nfrom .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import update_source_reliability\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\nPROVIDERS=frozenset(("coinbase","bitcoin","ethereum","solana"))\n@dataclass(frozen=True,slots=True)\nclass ExactReliabilityState:\n scored_cases:int;source_states:tuple;source_reliability_state_hash:str|None;rejected_non_provider_claims:int;state:str;probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False\ndef materialize_exact_provider_source_reliability(root=None):\n by={x.experience_id:x for x in read_crypto_learned_case_history(root=root,per_asset_limit=512)};states={};reject=0;cases=0\n for b in read_exact_prospective_bindings(root):\n  x=by.get(b.experience_id)\n  if x is None:continue\n  y=float(x.return_fraction)>0;used=False\n  for c in b.source_claims:\n   if len(c)<4 or str(c[0]).lower() not in PROVIDERS:reject+=1;continue\n   s=str(c[0]).lower();states[s]=update_source_reliability(states.get(s),s,bool(c[3])==y);used=True\n  cases+=1 if used else 0\n ss=tuple(states[k] for k in sorted(states))\n if not ss:return ExactReliabilityState(0,(),None,reject,"HOLD_PROVIDER_OUTCOME_EVIDENCE_REQUIRED")\n return ExactReliabilityState(cases,ss,envelope("prospective_provider_source_reliability",ss).state_hash,reject,"MATERIALIZED")\n'; TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_245_crypto_physical_provider_source_reliability as m\nclass T(unittest.TestCase):\n def test_provider_only(self):\n  b=SimpleNamespace(experience_id="e",source_claims=(("coinbase",1,.6,True),("condition_family",1,.8,True)));h=SimpleNamespace(experience_id="e",return_fraction=.01)\n  with patch.object(m,"read_exact_prospective_bindings",return_value=(b,)),patch.object(m,"read_crypto_learned_case_history",return_value=(h,)),patch.object(m,"envelope",return_value=SimpleNamespace(state_hash="a"*64)):r=m.materialize_exact_provider_source_reliability()\n  print("[SOURCES]",tuple(x.source_id for x in r.source_states),"[REJECTED]",r.rejected_non_provider_claims);self.assertEqual(tuple(x.source_id for x in r.source_states),("coinbase",));self.assertEqual(r.rejected_non_provider_claims,1)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-245 provider-only OCL-007 reliability certified")\n'; PHYSICAL=None; DEPS=[('qseries_v2/oracle_adapters/independent/oad_242_crypto_exact_prospective_forecast_outcome_binding.py', ('read_exact_prospective_bindings',)), ('qseries_v2/oracle_adapters/independent/oad_189_crypto_learned_case_exact_history_readback.py', ('read_crypto_learned_case_history',)), ('qseries_v2/oracle_adapters/independent/oad_218_existing_ocl_state_hash_envelope.py', ('envelope',)), ('qseries_v2/oracle_continuous_learner/ocl_007_source_reliability.py', ('update_source_reliability',))]
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,b/"kalshi-qss-bot",*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def w(p,s):
 compile(s,str(p),"exec"); q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def run(r,p):
 q=subprocess.run([sys.executable,str(p)],cwd=str(r))
 if q.returncode: raise RuntimeError("Certification failed: "+p.name)
def main():
 if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
 print("="*120); print(" OAD-245 CRYPTO PHYSICAL PROVIDER SOURCE RELIABILITY"); print("="*120); print("[ROOT]",r)
 for rel,symbols in DEPS:
  p=r/rel
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+rel)
  s=p.read_text(encoding="utf-8")
  for sym in symbols:
   if ("def "+sym+"(") not in s and ("class "+sym) not in s: raise RuntimeError("Exact symbol missing: "+sym)
  print("[PASS] dependency verified:",rel)
 targets=[pkg/'oad_245_crypto_physical_provider_source_reliability.py',r/'test_oad_245_crypto_physical_provider_source_reliability.py']
 if PHYSICAL: targets.append(r/None)
 old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  w(targets[0],MODULE); w(targets[1],TEST); run(r,targets[1])
  if PHYSICAL: w(targets[2],PHYSICAL); run(r,targets[2])
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] OAD-245 INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] OAD-245 rolled back"); raise
if __name__=="__main__": main()
