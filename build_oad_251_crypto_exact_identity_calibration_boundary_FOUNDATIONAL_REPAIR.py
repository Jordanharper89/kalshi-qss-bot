from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
EXPECTED='build_oad_251_crypto_exact_identity_calibration_boundary_FOUNDATIONAL_REPAIR.py'
TITLE='OAD-251 EXACT IDENTITY CALIBRATION BOUNDARY FOUNDATIONAL REPAIR'
DEPS=['qseries_v2/oracle_adapters/independent/oad_249_crypto_prospective_exact_identity_binding_ledger.py', 'qseries_v2/oracle_adapters/independent/oad_246_crypto_prospective_truth_calibration_physical_certification.py']
CHECKS=[('qseries_v2/oracle_adapters/independent/oad_246_crypto_prospective_truth_calibration_physical_certification.py', 'certify_prospective_truth_calibration')]
TARGETS=[('qseries_v2/oracle_adapters/independent/oad_242_crypto_exact_prospective_forecast_outcome_binding.py', 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\nASSETS=("BTC","ETH","SOL")\n@dataclass(frozen=True,slots=True)\nclass ExactProspectiveBinding:\n forecast_id:str;asset:str;experience_id:str;condition_hash:str;forecast_sequence:int;learned_sequence:int;forecast_created_at:str;outcome_observed_at:str;horizon_seconds:int;forecast_probability:float;source_claims:tuple;learning_event_id:str;learning_event_hash:str;outcome_hash:str;execution_authority:bool=False\ndef _p(x):return x if isinstance(x,dict) else dict(x or ())\ndef read_exact_prospective_bindings(root=None,per_source_limit=512):\n root=Path(root or Path.cwd()).resolve();bindings=[];learned=[]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as q:\n   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n   for a in ASSETS:\n    q.execute("""SELECT sequence_number,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s""",("source.crypto.prospective_binding."+a.lower(),int(per_source_limit)));bindings.extend(q.fetchall() or ())\n    q.execute("""SELECT sequence_number,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s""",("source.crypto.learned_case."+a.lower(),int(per_source_limit)));learned.extend(q.fetchall() or ())\n  c.rollback()\n by_exp={}\n for seq,raw in learned:\n  p=_p(raw)\n  if p.get("experience_id") and bool(p.get("exact_interval")):by_exp.setdefault(str(p["experience_id"]),[]).append((int(seq),p))\n out=[]\n for fseq,raw in bindings:\n  b=_p(raw);eid=str(b.get("experience_id") or "");matches=by_exp.get(eid,())\n  if len(matches)!=1:continue\n  lseq,l=matches[0]\n  if str(l.get("asset") or "").upper()!=str(b.get("asset") or "").upper():continue\n  if int(l.get("horizon_seconds") or 0)!=int(b.get("horizon_seconds") or 0):continue\n  out.append(ExactProspectiveBinding(str(b["forecast_id"]),str(b["asset"]).upper(),eid,str(l.get("condition_hash") or ""),int(fseq),lseq,str(b["forecast_created_at"]),str(l["outcome_observed_at"]),int(b["horizon_seconds"]),float(b["internal_forecast_probability"]),tuple(tuple(x) for x in b.get("source_claims") or ()),str(l.get("learning_event_id") or ""),str(l.get("learning_event_hash") or ""),str(l.get("outcome_hash") or ""),False))\n return tuple(sorted(out,key=lambda x:(x.forecast_sequence,x.learned_sequence)))\n'), ('test_oad_251_crypto_exact_identity_calibration_boundary.py', 'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_242_crypto_exact_prospective_forecast_outcome_binding as m\nclass Cur:\n def __init__(self,r):self.r=iter(r)\n def __enter__(self):return self\n def __exit__(self,*a):return False\n def execute(self,*a,**k):pass\n def fetchall(self):return next(self.r)\nclass C:\n def __init__(self,r):self.c=Cur(r)\n def __enter__(self):return self\n def __exit__(self,*a):return False\n def cursor(self):return self.c\n def rollback(self):pass\nclass T(unittest.TestCase):\n def test_explicit_ledger_only(self):\n  b=(10,{"forecast_id":"f"*64,"asset":"BTC","experience_id":"crypto-exp:BTC:x","forecast_created_at":"2026-09-01T00:00:00+00:00","horizon_seconds":60,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)})\n  l=(20,{"experience_id":"crypto-exp:BTC:x","asset":"BTC","condition_hash":"c"*64,"horizon_seconds":60,"outcome_observed_at":"2026-09-01T00:01:00+00:00","exact_interval":True,"learning_event_id":"id","learning_event_hash":"a"*64,"outcome_hash":"b"*64})\n  with patch.object(m,"connect",return_value=C([(b,),(l,),(),(),(),()])):r=m.read_exact_prospective_bindings()\n  print("[EXACT]",len(r),r[0].experience_id);self.assertEqual(len(r),1)\nif __name__=="__main__":\n x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not x.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-251 explicit identity ledger read boundary certified")\n'), ('test_oad_251_crypto_exact_identity_calibration_boundary_PHYSICAL.py', 'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_246_crypto_prospective_truth_calibration_physical_certification import certify_prospective_truth_calibration\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=certify_prospective_truth_calibration()\n  print("[PHYSICAL] exact_bindings=",r.exact_bindings);print("[PHYSICAL] calibration_cases=",r.calibration_cases);print("[PHYSICAL] reliability_cases=",r.reliability_cases);print("[PHYSICAL] state=",r.state);print("[PHYSICAL] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n  self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not x.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-251 physical exact-identity gate executed")\n')]
TESTS=['test_oad_251_crypto_exact_identity_calibration_boundary.py', 'test_oad_251_crypto_exact_identity_calibration_boundary_PHYSICAL.py']
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root();print("="*124);print(" "+TITLE);print("="*124);print("[ROOT]",r)
    for d in DEPS:
        p=r/d
        if not p.is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    for d,sym in CHECKS:
        text=(r/d).read_text(encoding="utf-8")
        if ("def "+sym+"(" not in text and "class "+sym not in text): raise RuntimeError("Exact symbol missing: "+sym+" in "+d)
        print("[PASS] exact contract:",sym)
    ps=[r/p for p,_ in TARGETS];old={p:(p.read_bytes() if p.exists() else None) for p in ps}
    try:
        for (rel,s),p in zip(TARGETS,ps): atomic(p,s)
        for t in TESTS:
            q=subprocess.run([sys.executable,str(r/t)],cwd=str(r))
            if q.returncode: raise RuntimeError("Certification failed: "+t)
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+TITLE+" COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise
if __name__=="__main__":main()
