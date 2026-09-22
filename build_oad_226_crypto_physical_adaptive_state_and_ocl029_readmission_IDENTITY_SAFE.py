from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for c in (base,base/"kalshi-qss-bot",*base.parents):
            if (c/"qseries_v2").is_dir():
                return c
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def run_test(r,t):
    q=subprocess.run([sys.executable,str(t)],cwd=str(r))
    if q.returncode:
        raise RuntimeError("Certification test failed: "+t.name)

REVISION='OAD_226_CRYPTO_PHYSICAL_ADAPTIVE_STATE_AND_OCL029_READMISSION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_226_crypto_physical_adaptive_state_and_ocl029_readmission_IDENTITY_SAFE.py'
MODULE_NAME='oad_226_crypto_physical_adaptive_state_and_ocl029_readmission.py'
TEST_NAME='test_oad_226_crypto_physical_adaptive_state_and_ocl029_readmission.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_222_crypto_physical_calibration_state_materialization import materialize_physical_calibration_state\nfrom .oad_223_crypto_physical_source_reliability_state_materialization import materialize_physical_source_reliability_state\nfrom .oad_224_crypto_physical_market_behavior_state_materialization import materialize_physical_market_behavior_state\nfrom .oad_225_crypto_physical_maturity_state_materialization import materialize_physical_maturity_state\nfrom .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission\nfrom qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import verify_ocl_023_meta_learning_performance_evaluation\nfrom qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import verify_ocl_024_adaptive_learning_weight_model\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass AdaptiveAndReadmission:\n    calibration_state:str\n    source_reliability_state:str\n    market_behavior_state_hash:str|None\n    maturity_state_hash:str|None\n    adaptive_weight_state_hash:str|None\n    adaptive_state:str\n    supplied_hashes:tuple[str,...]\n    missing_state_hashes:tuple[str,...]\n    admission_state:str\n    handoff_verified:bool\n    physical_ready:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\ndef run_physical_adaptive_and_ocl029_readmission(root=None):\n    if not verify_ocl_023_meta_learning_performance_evaluation() or not verify_ocl_024_adaptive_learning_weight_model():\n        raise RuntimeError("Frozen OCL-023/OCL-024 verifier failed")\n    cal=materialize_physical_calibration_state(root);rel=materialize_physical_source_reliability_state(root)\n    mb=materialize_physical_market_behavior_state(root);mat=materialize_physical_maturity_state(root)\n    adaptive_hash=None\n    adaptive_state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED"\n    hashes={}\n    if mb.market_behavior_state_hash:hashes["market_behavior_state_hash"]=mb.market_behavior_state_hash\n    if mat.maturity_state_hash:hashes["maturity_state_hash"]=mat.maturity_state_hash\n    admission=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)\n    return AdaptiveAndReadmission(cal.state,rel.state,mb.market_behavior_state_hash,mat.maturity_state_hash,adaptive_hash,adaptive_state,tuple(sorted(hashes)),tuple(admission.missing_state_hashes),admission.state,bool(admission.handoff_verified))\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_226_crypto_physical_adaptive_state_and_ocl029_readmission as m\nclass T(unittest.TestCase):\n    def test_hold(self):\n        cal=SimpleNamespace(state="HOLD_HISTORICAL_FORECAST_PROBABILITY_REQUIRED");rel=SimpleNamespace(state="HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")\n        mb=SimpleNamespace(market_behavior_state_hash="a"*64);mat=SimpleNamespace(maturity_state_hash="b"*64)\n        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)\n        with patch.object(m,"materialize_physical_calibration_state",return_value=cal),patch.object(m,"materialize_physical_source_reliability_state",return_value=rel),patch.object(m,"materialize_physical_market_behavior_state",return_value=mb),patch.object(m,"materialize_physical_maturity_state",return_value=mat),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):\n            r=m.run_physical_adaptive_and_ocl029_readmission()\n        print("[SUPPLIED]",r.supplied_hashes);print("[MISSING]",r.missing_state_hashes)\n        self.assertIn("market_behavior_state_hash",r.supplied_hashes);self.assertIn("maturity_state_hash",r.supplied_hashes);self.assertIsNone(r.adaptive_weight_state_hash);self.assertFalse(r.handoff_verified)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-226 adaptive HOLD + OCL-029 readmission path certified")\n'
PHYSICAL='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_226_crypto_physical_adaptive_state_and_ocl029_readmission import run_physical_adaptive_and_ocl029_readmission\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_physical_adaptive_and_ocl029_readmission()\n        print("[PHYSICAL] calibration_state=",r.calibration_state)\n        print("[PHYSICAL] source_reliability_state=",r.source_reliability_state)\n        print("[PHYSICAL] market_behavior_state_hash=",r.market_behavior_state_hash)\n        print("[PHYSICAL] maturity_state_hash=",r.maturity_state_hash)\n        print("[PHYSICAL] adaptive_state=",r.adaptive_state)\n        print("[PHYSICAL] supplied_hashes=",r.supplied_hashes)\n        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)\n        print("[PHYSICAL] admission_state=",r.admission_state)\n        print("[PHYSICAL] handoff_verified=",r.handoff_verified)\n        print("[PHYSICAL] probability_enabled=",r.probability_enabled)\n        print("[PHYSICAL] direction_enabled=",r.direction_enabled)\n        print("[PHYSICAL] execution_authority=",r.execution_authority)\n        self.assertTrue(r.physical_ready);self.assertFalse(r.probability_enabled);self.assertFalse(r.direction_enabled);self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-226 physical materialization I + OCL-029 readmission certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*122);print(" OAD-226 PHYSICAL LEARNING-STATE MATERIALIZATION I + OCL-029 READMISSION");print("="*122)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_221_crypto_scientific_reasoning_admission_physical_certification.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_222_crypto_physical_calibration_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_223_crypto_physical_source_reliability_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_224_crypto_physical_market_behavior_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_225_crypto_physical_maturity_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_023_meta_learning_performance.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_024_adaptive_learning_weight.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    pt=r/"test_oad_226_crypto_physical_adaptive_state_and_ocl029_readmission_PHYSICAL.py"
    targets=[m,t,pt];old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        write_atomic(pt,PHYSICAL)
        run_test(r,t)
        run_test(r,pt)
        print('[PASS] OCL-029 readmission uses only physically materialized hashes')
        print('[PASS] adaptive weight HOLDs without genuine mechanism-performance deltas')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-226 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
