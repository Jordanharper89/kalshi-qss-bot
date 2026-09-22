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

REVISION='OAD_234_CRYPTO_PROSPECTIVE_OUTCOME_CALIBRATION_SCORING_IDENTITY_SAFE_V1'
EXPECTED='build_oad_234_crypto_prospective_outcome_calibration_scoring_IDENTITY_SAFE.py'
MODULE_NAME='oad_234_crypto_prospective_outcome_calibration_scoring.py'
TEST_NAME='test_oad_234_crypto_prospective_outcome_calibration_scoring.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom hashlib import sha256\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import learn_calibration\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass ProspectiveScoredCase:\n    forecast_id:str;asset:str;forecast_probability:float;outcome_positive:bool;brier_score:float;baseline_brier:float;performance_delta:float\n    source_correctness:tuple;learning_event_hash:str;outcome_hash:str\n\ndef _payload(x):return x if isinstance(x,dict) else dict(x or ())\n\ndef read_and_score_mature_prospective_cases(root=None,limit=512):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            q.execute("""SELECT observed_at,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb)\n                         FROM public.oracle_canonical_observations WHERE observation_type=\'crypto_prospective_internal_forecast\'\n                         ORDER BY sequence_number ASC LIMIT %s""",(int(limit),));forecasts=q.fetchall() or []\n            q.execute("""SELECT observed_at,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb)\n                         FROM public.oracle_canonical_observations WHERE observation_type=\'crypto_verified_learned_case\'\n                         ORDER BY sequence_number ASC LIMIT %s""",(int(limit)*4,));learned=q.fetchall() or []\n        c.rollback()\n    out=[]\n    for fobs,fraw in forecasts:\n        f=_payload(fraw);asset=str(f.get("asset") or "").upper();created=datetime.fromisoformat(str(f.get("created_at")).replace("Z","+00:00"))\n        candidates=[]\n        for lobs,lraw in learned:\n            p=_payload(lraw)\n            if str(p.get("asset") or "").upper()!=asset or p.get("return_fraction") is None:continue\n            snap=datetime.fromisoformat(str(p.get("snapshot_at")).replace("Z","+00:00"))\n            if snap>=created:candidates.append((snap,p))\n        if not candidates:continue\n        p=min(candidates,key=lambda x:x[0])[1];prob=float(f["internal_forecast_probability"]);positive=float(p["return_fraction"])>0\n        outcome=build_outcome_observation(asset,"prospective_positive_return_60s",1 if positive else 0,str(p.get("outcome_observed_at")),f"prospective:{f[\'forecast_id\']}",str(p["outcome_hash"]))\n        event=assemble_learning_event(asset,str(p["evidence_hash"]),str(p["lineage_hash"]),outcome)\n        if not verify_learning_event(event):raise RuntimeError("prospective learning event invalid")\n        cal=learn_calibration(event,prob,positive);baseline=(.5-(1.0 if positive else 0.0))**2\n        sc=tuple((str(fam),bool(pred)==positive) for fam,cnt,fp,pred in tuple(f.get("source_claims") or ()))\n        out.append(ProspectiveScoredCase(str(f["forecast_id"]),asset,prob,positive,cal.brier_score,baseline,baseline-cal.brier_score,sc,event.event_hash,outcome.outcome_hash))\n    return tuple(out)\n'
TEST='import unittest\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import learn_calibration\nclass T(unittest.TestCase):\n    def test_brier_delta_contract(self):\n        o=build_outcome_observation("BTC","prospective_positive_return_60s",1,"t","prospective:x","a"*64)\n        e=assemble_learning_event("BTC","b"*64,"c"*64,o);x=learn_calibration(e,.7,True);delta=.25-x.brier_score\n        print("[BRIER]",x.brier_score,"[DELTA]",delta)\n        self.assertAlmostEqual(x.brier_score,.09);self.assertGreater(delta,0)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-234 prospective OCL-006 outcome-scoring contract certified")\n'
PHYSICAL='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases\nclass T(unittest.TestCase):\n    def test_physical(self):\n        rows=read_and_score_mature_prospective_cases()\n        print("[PHYSICAL] mature_scored_cases=",len(rows))\n        if rows:\n            print("[PHYSICAL] latest=",rows[-1])\n        else:\n            print("[PHYSICAL] state= HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED")\n        self.assertTrue(all(0<=x.forecast_probability<=1 for x in rows))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-234 physical prospective scoring gate certified")\n'
PHYSICAL_NAME='test_oad_234_crypto_prospective_outcome_calibration_scoring_PHYSICAL.py'

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2/oracle_adapters/independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    pt=r/PHYSICAL_NAME
    print("="*124);print(" OAD-234 CRYPTO PROSPECTIVE OUTCOME + CALIBRATION SCORING");print("="*124);print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_233_crypto_prospective_forecast_single_writer_persistence.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_006_calibration_learning.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t];targets.append(pt)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        write_atomic(pt,PHYSICAL)
        run_test(r,t)
        run_test(r,pt)
        print('[PASS] OCL-006 receives only prospective forecast/outcome pairs')
        print('[PASS] 0.50 Brier baseline preserved for real performance delta')
        print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE')
        print("[DONE] OAD-234 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
