from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
EXPECTED='build_oad_249_crypto_prospective_exact_identity_binding_ledger.py'
TITLE='OAD-249 PROSPECTIVE EXACT IDENTITY BINDING LEDGER'
DEPS=['qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py', 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py']
CHECKS=[('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py', 'submit_observation_batch')]
TARGETS=[('qseries_v2/oracle_adapters/independent/oad_249_crypto_prospective_exact_identity_binding_ledger.py', 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\nPRODUCER="oracle.crypto_prospective_identity";PRIORITY=20;SOURCE_PREFIX="source.crypto.prospective_binding."\n@dataclass(frozen=True,slots=True)\nclass BindingPersistence:\n bindings:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False\ndef _asset_from_experience_id(x):\n p=str(x).split(":")\n if len(p)<3 or p[0]!="crypto-exp":raise RuntimeError("invalid experience identity")\n return p[1].upper()\ndef canonicalize_binding(forecast_row,experience_id,cycle_sequence,acquisition_batch_id="oad249.prospective-binding"):\n p=dict(forecast_row.payload);asset=str(p["asset"]).upper()\n if _asset_from_experience_id(experience_id)!=asset:raise RuntimeError("forecast/experience asset mismatch")\n fid=str(p["forecast_id"]);created=str(p["created_at"]);h=int(p["horizon_seconds"])\n raw=RawSourceObservation.create(source_observation_id=f"{fid}:{experience_id}",observed_at=datetime.now(timezone.utc),observation_type="crypto_prospective_exact_identity_binding",payload={"forecast_id":fid,"forecast_observation_id":str(forecast_row.observation_id),"asset":asset,"forecast_created_at":created,"experience_id":str(experience_id),"cycle_sequence":int(cycle_sequence),"horizon_seconds":h,"training_snapshot_hash":str(p["training_snapshot_hash"]),"internal_forecast_probability":float(p["internal_forecast_probability"]),"source_claims":tuple(p.get("source_claims") or ()),"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False},provenance={"producer":PRODUCER,"binding_mode":"same_production_cycle_explicit_identity","read_only":True})\n return CanonicalObservation.create(source_id=SOURCE_PREFIX+asset.lower(),raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)\ndef persist_cycle_bindings(forecast_observation_ids,experience_ids,cycle_sequence,root=None,timeout_seconds=120.0):\n root=Path(root or Path.cwd()).resolve();backend=_backend(root);fr=tuple(exact_postgresql_readback(tuple(forecast_observation_ids),root))\n by_asset={}\n for r in fr:by_asset[str(dict(r.payload)["asset"]).upper()]=r\n xs=[]\n for eid in tuple(experience_ids):\n  a=_asset_from_experience_id(eid)\n  if a in by_asset:xs.append(canonicalize_binding(by_asset[a],eid,cycle_sequence))\n missing=[];existing=0\n for i,x in enumerate(xs):\n  if _query_one(backend,x.observation_id,i) is None:missing.append(x)\n  else:existing+=1\n committed=0\n if missing:\n  s=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root);ev=tuple(await_request(str(s.request_id),root,float(timeout_seconds)));accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)\n  if len(accepted)!=len(missing):raise RuntimeError("prospective binding commit mismatch")\n  committed=len(accepted)\n ids=tuple(x.observation_id for x in xs);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()\n if len(rows)!=len(ids):raise RuntimeError("prospective binding exact readback mismatch")\n return BindingPersistence(len(ids),existing,committed,len(rows),ids,False)\n'), ('test_oad_249_crypto_prospective_exact_identity_binding_ledger.py', 'import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_249_crypto_prospective_exact_identity_binding_ledger import canonicalize_binding\nclass T(unittest.TestCase):\n def test_explicit_identity(self):\n  r=SimpleNamespace(observation_id="o"*64,payload={"forecast_id":"f"*64,"asset":"BTC","created_at":"2026-09-01T00:00:00+00:00","horizon_seconds":60,"training_snapshot_hash":"s"*64,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)})\n  x=canonicalize_binding(r,"crypto-exp:BTC:abc",12);p=dict(x.payload);print("[BIND]",p["forecast_id"],"->",p["experience_id"]);self.assertEqual(p["cycle_sequence"],12);self.assertFalse(x.execution_allowed)\nif __name__=="__main__":\n x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not x.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-249 immutable explicit identity binding ledger certified")\n')]
TESTS=['test_oad_249_crypto_prospective_exact_identity_binding_ledger.py']
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
