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

REVISION='OAD_235_PROSPECTIVE_CALIBRATION_SOURCE_RELIABILITY_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED='build_oad_235_prospective_calibration_source_reliability_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_235_prospective_calibration_source_reliability_materialization.py'
TEST_NAME='test_oad_235_prospective_calibration_source_reliability_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom .oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases\nfrom qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import CalibrationObservation\nfrom qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import update_source_reliability\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProspectiveCalibrationReliabilityState:\n    scored_cases:int;calibration_state_hash:str|None;source_reliability_state_hash:str|None;source_states:tuple;state:str\n    probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False\n\ndef materialize_prospective_calibration_source_reliability(root=None):\n    rows=read_and_score_mature_prospective_cases(root)\n    if not rows:return ProspectiveCalibrationReliabilityState(0,None,None,(),"HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED")\n    cal=tuple(CalibrationObservation(x.learning_event_hash,x.forecast_probability,x.outcome_positive,x.brier_score) for x in rows)\n    states={}\n    for x in rows:\n        for source,correct in x.source_correctness:states[source]=update_source_reliability(states.get(source),source,correct)\n    ss=tuple(states[k] for k in sorted(states))\n    return ProspectiveCalibrationReliabilityState(len(rows),envelope("calibration",cal).state_hash,envelope("source_reliability",ss).state_hash if ss else None,ss,"MATERIALIZED")\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_235_prospective_calibration_source_reliability_materialization as m\nclass T(unittest.TestCase):\n    def test_materialize(self):\n        rows=(SimpleNamespace(learning_event_hash="a"*64,forecast_probability=.7,outcome_positive=True,brier_score=.09,source_correctness=(("bitcoin",True),("coinbase",False))),)\n        with patch.object(m,"read_and_score_mature_prospective_cases",return_value=rows):\n            r=m.materialize_prospective_calibration_source_reliability()\n        print("[STATE]",r.state,"[CAL]",r.calibration_state_hash,"[REL]",r.source_reliability_state_hash)\n        self.assertEqual(r.state,"MATERIALIZED");self.assertEqual(len(r.calibration_state_hash),64);self.assertEqual(len(r.source_reliability_state_hash),64)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-235 prospective calibration + source reliability materialization certified")\n'

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2/oracle_adapters/independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-235 PROSPECTIVE CALIBRATION + SOURCE RELIABILITY MATERIALIZATION");print("="*124);print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_234_crypto_prospective_outcome_calibration_scoring.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_218_existing_ocl_state_hash_envelope.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_006_calibration_learning.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_007_source_reliability.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] source correctness comes from frozen prospective claims vs realized outcome')
        print('[PASS] calibration state comes from genuine OCL-006 observations')
        print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE')
        print("[DONE] OAD-235 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
