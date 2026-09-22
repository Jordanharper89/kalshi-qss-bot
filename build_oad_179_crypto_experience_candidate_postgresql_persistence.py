from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_179_CRYPTO_EXPERIENCE_CANDIDATE_POSTGRESQL_PERSISTENCE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.crypto_experience_candidates"\nPRIORITY=20\nSOURCE_PREFIX="source.crypto.experience."\n\n@dataclass(frozen=True,slots=True)\nclass CryptoExperiencePersistenceResult:\n    candidates:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    observation_ids:tuple\n    execution_authority:bool=False\n\ndef canonicalize_crypto_experience_candidate(candidate,lineage,acquisition_batch_id="oad179.crypto-experience"):\n    observed_at=datetime.fromisoformat(str(candidate.snapshot_at).replace("Z","+00:00"))\n    if observed_at.tzinfo is None: observed_at=observed_at.replace(tzinfo=timezone.utc)\n    source_id=f"{SOURCE_PREFIX}{candidate.asset.lower()}"\n    raw=RawSourceObservation.create(\n        source_observation_id=candidate.experience_id,\n        observed_at=observed_at,\n        observation_type="crypto_historical_experience_candidate",\n        payload={\n            "experience_id":candidate.experience_id,"asset":candidate.asset,\n            "snapshot_at":candidate.snapshot_at,"cohort_state":candidate.cohort_state,\n            "condition_vector":candidate.condition_vector,"temporal_vector":candidate.temporal_vector,\n            "evidence_state":candidate.evidence_state,"consistency_state":candidate.consistency_state,\n            "market_native_metrics":candidate.market_native_metrics,\n            "independent_chain_metrics":candidate.independent_chain_metrics,\n            "comparable_temporal_metrics":candidate.comparable_temporal_metrics,\n            "evidence_hash":candidate.evidence_hash,"condition_hash":candidate.condition_hash,\n            "experience_hash":candidate.experience_hash,"lineage_hash":lineage.lineage_hash,\n            "outcome_attached":False,"probability":None,"direction":None,\n        },\n        provenance={"producer":PRODUCER,"lineage_hash":lineage.lineage_hash,"read_only":True},\n    )\n    return CanonicalObservation.create(source_id=source_id,raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)\n\ndef persist_crypto_experience_candidates(pairs,root=None,timeout_seconds=120.0):\n    root=Path(root or Path.cwd()).resolve()\n    canonical=tuple(canonicalize_crypto_experience_candidate(c,l) for c,l in tuple(pairs))\n    backend=_backend(root); missing=[]; existing=0\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None: missing.append(x)\n        else: existing+=1\n    committed=0\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing): raise RuntimeError("crypto experience single-writer commit mismatch")\n        committed=len(accepted)\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root)) if ids else tuple()\n    if len(rows)!=len(ids): raise RuntimeError("crypto experience exact readback mismatch")\n    return CryptoExperiencePersistenceResult(len(canonical),existing,committed,len(rows),ids,False)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_179_crypto_experience_candidate_postgresql_persistence import canonicalize_crypto_experience_candidate\nclass T(unittest.TestCase):\n    def test_canonical(self):\n        c=SimpleNamespace(experience_id="crypto-exp:BTC:abc",asset="BTC",snapshot_at="2026-08-29T02:00:00+00:00",cohort_state="FULL_COVERAGE",\n            condition_vector=(("bitcoin","x",1.0,"OBSERVED"),),temporal_vector=(("bitcoin","x","UNCHANGED",0.0,0.0,True),),\n            evidence_state="CROSS_SOURCE_PRESENT",consistency_state="NO_EXPLICIT_CONTRADICTION",market_native_metrics=3,independent_chain_metrics=7,\n            comparable_temporal_metrics=1,evidence_hash="a"*64,condition_hash="b"*64,experience_hash="c"*64)\n        l=SimpleNamespace(lineage_hash="d"*64)\n        x=canonicalize_crypto_experience_candidate(c,l)\n        p=dict(x.payload)\n        print("[SOURCE_ID]",x.source_id)\n        print("[OUTCOME_ATTACHED]",p["outcome_attached"])\n        self.assertEqual(x.source_id,"source.crypto.experience.btc")\n        self.assertFalse(p["outcome_attached"])\n        self.assertIsNone(p["probability"])\n        self.assertFalse(x.execution_allowed)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-179 immutable PostgreSQL experience-candidate contract certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_179_crypto_experience_candidate_postgresql_persistence.py'; test=r/'test_oad_179_crypto_experience_candidate_postgresql_persistence.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-179 CRYPTO EXPERIENCE CANDIDATE POSTGRESQL PERSISTENCE INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_068_exact_postgresql_independent_readback.py', 'oad_177_crypto_historical_experience_candidate.py', 'oad_178_crypto_experience_evidence_lineage.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_179_crypto_experience_candidate_postgresql_persistence import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-179 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
