from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s.lstrip("\n"),encoding="utf-8",newline="\n");os.replace(t,p)

def run_test(r,p):
    q=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if q.returncode: raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_233_CRYPTO_PROSPECTIVE_FORECAST_SINGLE_WRITER_PERSISTENCE_IDENTITY_SAFE_V1'
EXPECTED='build_oad_233_crypto_prospective_forecast_single_writer_persistence_IDENTITY_SAFE.py'
MODULE_NAME='oad_233_crypto_prospective_forecast_single_writer_persistence.py'
TEST_NAME='test_oad_233_crypto_prospective_forecast_single_writer_persistence.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_232_crypto_prospective_empirical_forecast_foundation import build_prospective_crypto_forecasts\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\nPRODUCER="oracle.crypto_prospective_learning";PRIORITY=20;SOURCE_PREFIX="source.crypto.prospective_forecast."\n\n@dataclass(frozen=True,slots=True)\nclass ForecastPersistence:\n    forecasts:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False\n\ndef canonicalize_prospective_forecast(f,acquisition_batch_id="oad233.prospective"):\n    payload={"forecast_id":f.forecast_id,"asset":f.asset,"created_at":f.created_at,"training_as_of_sequence":f.training_as_of_sequence,\n             "training_snapshot_hash":f.training_snapshot_hash,"sample_size":f.sample_size,"positive_count":f.positive_count,\n             "negative_or_flat_count":f.negative_or_flat_count,"internal_forecast_probability":f.internal_forecast_probability,\n             "source_claims":f.source_claims,"horizon_seconds":f.horizon_seconds,\n             "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}\n    raw=RawSourceObservation.create(source_observation_id=f.forecast_id,observed_at=datetime.fromisoformat(f.created_at.replace("Z","+00:00")),\n        observation_type="crypto_prospective_internal_forecast",payload=payload,\n        provenance={"producer":PRODUCER,"read_only":True,"operator_probability":False})\n    return CanonicalObservation.create(source_id=SOURCE_PREFIX+f.asset.lower(),raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)\n\ndef persist_prospective_forecasts(root=None,timeout_seconds=120.0):\n    root=Path(root or Path.cwd()).resolve();fs=build_prospective_crypto_forecasts(root);xs=tuple(canonicalize_prospective_forecast(f) for f in fs)\n    backend=_backend(root);missing=[];existing=0\n    for i,x in enumerate(xs):\n        if _query_one(backend,x.observation_id,i) is None:missing.append(x)\n        else:existing+=1\n    committed=0\n    if missing:\n        s=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        ev=tuple(await_request(str(s.request_id),root,float(timeout_seconds)))\n        accepted=tuple(x for x in ev if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing):raise RuntimeError("prospective forecast commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in xs);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()\n    if len(rows)!=len(ids):raise RuntimeError("prospective forecast exact readback mismatch")\n    return ForecastPersistence(len(ids),existing,committed,len(rows),ids,False)\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_233_crypto_prospective_forecast_single_writer_persistence import canonicalize_prospective_forecast\nclass T(unittest.TestCase):\n    def test_canonical(self):\n        f=SimpleNamespace(forecast_id="a"*64,asset="BTC",created_at="2026-08-31T20:00:00+00:00",training_as_of_sequence=10,training_snapshot_hash="b"*64,sample_size=5,positive_count=3,negative_or_flat_count=2,internal_forecast_probability=.57,source_claims=(("bitcoin",5,.6,True),),horizon_seconds=60)\n        x=canonicalize_prospective_forecast(f);p=dict(x.payload)\n        print("[SOURCE]",x.source_id,"[P_INTERNAL]",p["internal_forecast_probability"])\n        self.assertFalse(p["probability_enabled"]);self.assertFalse(p["publication_allowed"]);self.assertFalse(x.execution_allowed)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-233 prospective forecast single-writer persistence contract certified")\n'

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2/oracle_adapters/independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-233 CRYPTO PROSPECTIVE FORECAST SINGLE-WRITER PERSISTENCE");print("="*124);print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_232_crypto_prospective_empirical_forecast_foundation.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_068_exact_postgresql_independent_readback.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] prospective forecasts use canonical single-writer path')
        print('[PASS] persisted internal probability remains non-published/non-executable')
        print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE')
        print("[DONE] OAD-233 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
