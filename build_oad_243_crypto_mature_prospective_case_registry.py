from pathlib import Path
import os,sys,subprocess
EXPECTED='build_oad_243_crypto_mature_prospective_case_registry.py'; MODULE='from dataclasses import dataclass\nfrom .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass MatureProspectiveCase:\n forecast_id:str;asset:str;experience_id:str;condition_hash:str;forecast_probability:float;source_claims:tuple;learning_event_id:str;learning_event_hash:str;outcome_hash:str;state:str="MATURE_EXACT";execution_authority:bool=False\ndef build_mature_prospective_case_registry(root=None):\n return tuple(MatureProspectiveCase(x.forecast_id,x.asset,x.experience_id,x.condition_hash,x.forecast_probability,x.source_claims,x.learning_event_id,x.learning_event_hash,x.outcome_hash) for x in read_exact_prospective_bindings(root) if x.learning_event_id and len(x.learning_event_hash)==64 and len(x.outcome_hash)==64)\n'; TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_243_crypto_mature_prospective_case_registry as m\nclass T(unittest.TestCase):\n def test_lineage_gate(self):\n  g=SimpleNamespace(forecast_id="f",asset="BTC",experience_id="e",condition_hash="c"*64,forecast_probability=.6,source_claims=(),learning_event_id="id",learning_event_hash="a"*64,outcome_hash="b"*64);b=SimpleNamespace(**{**g.__dict__,"learning_event_hash":"bad"})\n  with patch.object(m,"read_exact_prospective_bindings",return_value=(g,b)):r=m.build_mature_prospective_case_registry()\n  print("[MATURE]",len(r));self.assertEqual(len(r),1)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-243 mature exact registry certified")\n'; PHYSICAL=None; DEPS=[('qseries_v2/oracle_adapters/independent/oad_242_crypto_exact_prospective_forecast_outcome_binding.py', ('read_exact_prospective_bindings',))]
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
 print("="*120); print(" OAD-243 CRYPTO MATURE PROSPECTIVE CASE REGISTRY"); print("="*120); print("[ROOT]",r)
 for rel,symbols in DEPS:
  p=r/rel
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+rel)
  s=p.read_text(encoding="utf-8")
  for sym in symbols:
   if ("def "+sym+"(") not in s and ("class "+sym) not in s: raise RuntimeError("Exact symbol missing: "+sym)
  print("[PASS] dependency verified:",rel)
 targets=[pkg/'oad_243_crypto_mature_prospective_case_registry.py',r/'test_oad_243_crypto_mature_prospective_case_registry.py']
 if PHYSICAL: targets.append(r/None)
 old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  w(targets[0],MODULE); w(targets[1],TEST); run(r,targets[1])
  if PHYSICAL: w(targets[2],PHYSICAL); run(r,targets[2])
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] OAD-243 INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] OAD-243 rolled back"); raise
if __name__=="__main__": main()
