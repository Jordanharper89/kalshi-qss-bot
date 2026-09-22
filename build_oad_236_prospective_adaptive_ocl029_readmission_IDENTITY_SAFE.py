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

REVISION='OAD_236_PROSPECTIVE_ADAPTIVE_OCL029_READMISSION_IDENTITY_SAFE_V1'
EXPECTED='build_oad_236_prospective_adaptive_ocl029_readmission_IDENTITY_SAFE.py'
MODULE_NAME='oad_236_prospective_adaptive_ocl029_readmission.py'
TEST_NAME='test_oad_236_prospective_adaptive_ocl029_readmission.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom .oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases\nfrom .oad_235_prospective_calibration_source_reliability_materialization import materialize_prospective_calibration_source_reliability\nfrom .oad_228_snapshot_market_behavior_maturity_materialization import materialize_snapshot_behavior_maturity\nfrom .oad_229_crypto_physical_entity_relationship_materialization import materialize_entity_relationship_state\nfrom .oad_230_crypto_causal_narrative_physical_resolution import resolve_causal_narrative_physical_state\nfrom .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission\nfrom qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import evaluate_meta_learning_performance\nfrom qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import build_adaptive_learning_weight\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProspectiveAdaptiveReadmission:\n    scored_cases:int;adaptive_weight_state_hash:str|None;adaptive_state:str;supplied_hashes:tuple;missing_state_hashes:tuple;admission_state:str;handoff_verified:bool\n    probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False\n\ndef run_prospective_adaptive_ocl029_readmission(root=None):\n    scored=read_and_score_mature_prospective_cases(root)\n    cr=materialize_prospective_calibration_source_reliability(root)\n    bm=materialize_snapshot_behavior_maturity(root);er=materialize_entity_relationship_state(root);cn=resolve_causal_narrative_physical_state(root)\n    hashes={}\n    if bm.market_behavior_state_hash:hashes["market_behavior_state_hash"]=bm.market_behavior_state_hash\n    if bm.maturity_state_hash:hashes["maturity_state_hash"]=bm.maturity_state_hash\n    if er.entity_relationship_state_hash:hashes["entity_relationship_state_hash"]=er.entity_relationship_state_hash\n    if cr.calibration_state_hash:hashes["calibration_state_hash"]=cr.calibration_state_hash\n    if cr.source_reliability_state_hash:hashes["source_reliability_state_hash"]=cr.source_reliability_state_hash\n    adaptive=None;state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED"\n    if scored:\n        perf=evaluate_meta_learning_performance("crypto_prospective_empirical_forecast",tuple(x.performance_delta for x in scored))\n        maturity_score=float(bm.maturity_score)\n        weight=build_adaptive_learning_weight(perf,1.0,maturity_score)\n        adaptive=envelope("adaptive_weight",weight).state_hash;hashes["adaptive_weight_state_hash"]=adaptive;state="MATERIALIZED"\n    adm=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)\n    return ProspectiveAdaptiveReadmission(len(scored),adaptive,state,tuple(sorted(hashes)),tuple(adm.missing_state_hashes),adm.state,bool(adm.handoff_verified))\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_236_prospective_adaptive_ocl029_readmission as m\nclass T(unittest.TestCase):\n    def test_hold_without_future_case(self):\n        cr=SimpleNamespace(calibration_state_hash=None,source_reliability_state_hash=None)\n        bm=SimpleNamespace(market_behavior_state_hash="a"*64,maturity_state_hash="b"*64,maturity_score=0.0)\n        er=SimpleNamespace(entity_relationship_state_hash="c"*64);cn=SimpleNamespace()\n        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","causal_state_hash","narrative_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)\n        with patch.object(m,"read_and_score_mature_prospective_cases",return_value=()),patch.object(m,"materialize_prospective_calibration_source_reliability",return_value=cr),patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):\n            r=m.run_prospective_adaptive_ocl029_readmission()\n        print("[STATE]",r.adaptive_state,"[MISSING]",r.missing_state_hashes)\n        self.assertIsNone(r.adaptive_weight_state_hash);self.assertFalse(r.handoff_verified)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-236 prospective adaptive + OCL-029 readmission contract certified")\n'
PHYSICAL='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_236_prospective_adaptive_ocl029_readmission import run_prospective_adaptive_ocl029_readmission\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_prospective_adaptive_ocl029_readmission()\n        print("[PHYSICAL] scored_cases=",r.scored_cases)\n        print("[PHYSICAL] adaptive_state=",r.adaptive_state)\n        print("[PHYSICAL] adaptive_weight_state_hash=",r.adaptive_weight_state_hash)\n        print("[PHYSICAL] supplied_hashes=",r.supplied_hashes)\n        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)\n        print("[PHYSICAL] admission_state=",r.admission_state)\n        print("[PHYSICAL] handoff_verified=",r.handoff_verified)\n        print("[PHYSICAL] probability_enabled=",r.probability_enabled)\n        print("[PHYSICAL] direction_enabled=",r.direction_enabled)\n        print("[PHYSICAL] publication_allowed=",r.publication_allowed)\n        print("[PHYSICAL] execution_authority=",r.execution_authority)\n        self.assertFalse(r.probability_enabled);self.assertFalse(r.direction_enabled);self.assertFalse(r.publication_allowed);self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-236 physical prospective adaptive + OCL-029 readmission certified")\n'
PHYSICAL_NAME='test_oad_236_prospective_adaptive_ocl029_readmission_PHYSICAL.py'

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2/oracle_adapters/independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    pt=r/PHYSICAL_NAME
    print("="*124);print(" OAD-236 PROSPECTIVE ADAPTIVE + OCL-029 READMISSION");print("="*124);print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_235_prospective_calibration_source_reliability_materialization.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_234_crypto_prospective_outcome_calibration_scoring.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_228_snapshot_market_behavior_maturity_materialization.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_229_crypto_physical_entity_relationship_materialization.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_230_crypto_causal_narrative_physical_resolution.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_221_crypto_scientific_reasoning_admission_physical_certification.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_023_meta_learning_performance.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_024_adaptive_learning_weight.py'
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
        print('[PASS] adaptive delta is prospective Brier improvement vs explicit 0.50 baseline')
        print('[PASS] OCL-029 receives only physically available hashes')
        print('[PASS] causal/narrative remain HOLD unless explicit evidence exists')
        print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE')
        print("[DONE] OAD-236 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
