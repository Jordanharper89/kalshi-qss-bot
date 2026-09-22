from pathlib import Path
import os,sys,subprocess
EXPECTED='build_oad_242_crypto_exact_prospective_forecast_outcome_binding.py'; MODULE='from dataclasses import dataclass\nfrom datetime import datetime\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\nASSETS=("BTC","ETH","SOL")\n@dataclass(frozen=True,slots=True)\nclass ExactProspectiveBinding:\n forecast_id:str;asset:str;experience_id:str;condition_hash:str;forecast_sequence:int;learned_sequence:int;forecast_created_at:str;outcome_observed_at:str;horizon_seconds:int;forecast_probability:float;source_claims:tuple;learning_event_id:str;learning_event_hash:str;outcome_hash:str;execution_authority:bool=False\ndef _dt(x): return x if isinstance(x,datetime) else datetime.fromisoformat(str(x).replace("Z","+00:00"))\ndef _p(x): return x if isinstance(x,dict) else dict(x or ())\ndef read_exact_prospective_bindings(root=None,per_source_limit=512):\n root=Path(root or Path.cwd()).resolve();fs=[];ls=[]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as q:\n   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n   for a in ASSETS:\n    for prefix,target in (("source.crypto.prospective_forecast.",fs),("source.crypto.learned_case.",ls)):\n     q.execute("""SELECT sequence_number,observed_at,observation_type,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb) FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s""",(prefix+a.lower(),int(per_source_limit)));target.extend(q.fetchall() or ())\n  c.rollback()\n forecasts=[]\n for seq,obs,typ,raw in fs:\n  p=_p(raw);ch=str(p.get("condition_hash") or p.get("training_snapshot_hash") or "")\n  if str(typ)=="crypto_prospective_internal_forecast" and len(ch)==64: forecasts.append((int(seq),p,ch))\n learned=[]\n for seq,obs,typ,raw in ls:\n  p=_p(raw)\n  if str(typ)=="crypto_verified_learned_case" and bool(p.get("exact_interval")) and p.get("experience_id") and len(str(p.get("condition_hash") or ""))==64: learned.append((int(seq),p))\n out=[]\n for fseq,f,ch in forecasts:\n  a=str(f.get("asset") or "").upper();created=_dt(f["created_at"]);h=int(f.get("horizon_seconds") or 0)\n  cand=[(s,p) for s,p in learned if str(p.get("asset") or "").upper()==a and str(p.get("condition_hash"))==ch and int(p.get("horizon_seconds") or 0)==h and p.get("outcome_observed_at") and _dt(p["outcome_observed_at"])>created]\n  if len(cand)!=1: continue\n  lseq,l=cand[0]\n  out.append(ExactProspectiveBinding(str(f["forecast_id"]),a,str(l["experience_id"]),ch,fseq,lseq,str(f["created_at"]),str(l["outcome_observed_at"]),h,float(f["internal_forecast_probability"]),tuple(tuple(x) for x in f.get("source_claims") or ()),str(l.get("learning_event_id") or ""),str(l.get("learning_event_hash") or ""),str(l.get("outcome_hash") or ""),False))\n return tuple(sorted(out,key=lambda x:(x.forecast_sequence,x.learned_sequence)))\n'; TEST='import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_242_crypto_exact_prospective_forecast_outcome_binding as m\nclass Cur:\n def __init__(self,rows):self.rows=iter(rows)\n def __enter__(self):return self\n def __exit__(self,*a):return False\n def execute(self,*a,**k):pass\n def fetchall(self):return next(self.rows)\nclass C:\n def __init__(self,r):self.c=Cur(r)\n def __enter__(self):return self\n def __exit__(self,*a):return False\n def cursor(self):return self.c\n def rollback(self):pass\nclass T(unittest.TestCase):\n def test_exact_unique(self):\n  ch="c"*64;f=(10,None,"crypto_prospective_internal_forecast",{"forecast_id":"f"*64,"asset":"BTC","created_at":"2026-09-01T00:00:00+00:00","training_snapshot_hash":ch,"horizon_seconds":60,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)});l=(20,None,"crypto_verified_learned_case",{"asset":"BTC","experience_id":"e1","condition_hash":ch,"horizon_seconds":60,"outcome_observed_at":"2026-09-01T00:01:00+00:00","exact_interval":True,"learning_event_id":"id","learning_event_hash":"a"*64,"outcome_hash":"b"*64})\n  with patch.object(m,"connect",return_value=C([(f,),(),(),(),(),(l,)])):r=m.read_exact_prospective_bindings()\n  print("[BINDINGS]",len(r));self.assertEqual(len(r),1)\n  with patch.object(m,"connect",return_value=C([(f,),(),(),(),(),(l,l)])):self.assertEqual(m.read_exact_prospective_bindings(),())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-242 unique identity binding; ambiguity rejected")\n'; PHYSICAL=None; DEPS=[('qseries_v2/oracle_adapters/independent/oad_233_crypto_prospective_forecast_single_writer_persistence.py', ('persist_prospective_forecasts',)), ('qseries_v2/oracle_adapters/independent/oad_189_crypto_learned_case_exact_history_readback.py', ('read_crypto_learned_case_history',)), ('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', ('connect',))]
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
 print("="*120); print(" OAD-242 CRYPTO EXACT PROSPECTIVE FORECAST OUTCOME BINDING"); print("="*120); print("[ROOT]",r)
 for rel,symbols in DEPS:
  p=r/rel
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+rel)
  s=p.read_text(encoding="utf-8")
  for sym in symbols:
   if ("def "+sym+"(") not in s and ("class "+sym) not in s: raise RuntimeError("Exact symbol missing: "+sym)
  print("[PASS] dependency verified:",rel)
 targets=[pkg/'oad_242_crypto_exact_prospective_forecast_outcome_binding.py',r/'test_oad_242_crypto_exact_prospective_forecast_outcome_binding.py']
 if PHYSICAL: targets.append(r/None)
 old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  w(targets[0],MODULE); w(targets[1],TEST); run(r,targets[1])
  if PHYSICAL: w(targets[2],PHYSICAL); run(r,targets[2])
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] OAD-242 INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] OAD-242 rolled back"); raise
if __name__=="__main__": main()
