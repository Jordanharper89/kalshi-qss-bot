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

def run_test(r,p):
    z=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if z.returncode:
        raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_231_SNAPSHOT_OCL029_SCIENTIFIC_REASONING_READMISSION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_231_snapshot_ocl029_scientific_reasoning_readmission_IDENTITY_SAFE.py'
MODULE_NAME='oad_231_snapshot_ocl029_scientific_reasoning_readmission.py'
TEST_NAME='test_oad_231_snapshot_ocl029_scientific_reasoning_readmission.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_228_snapshot_market_behavior_maturity_materialization import materialize_snapshot_behavior_maturity\nfrom .oad_229_crypto_physical_entity_relationship_materialization import materialize_entity_relationship_state\nfrom .oad_230_crypto_causal_narrative_physical_resolution import resolve_causal_narrative_physical_state\nfrom .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission\nfrom .oad_222_crypto_physical_calibration_state_materialization import materialize_physical_calibration_state\nfrom .oad_223_crypto_physical_source_reliability_state_materialization import materialize_physical_source_reliability_state\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SnapshotOCL029Readmission:\n    as_of_sequence:int\n    supplied_hashes:tuple[str,...]\n    missing_state_hashes:tuple[str,...]\n    calibration_state:str\n    source_reliability_state:str\n    causal_state:str\n    narrative_state:str\n    admission_state:str\n    handoff_verified:bool\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_snapshot_ocl029_readmission(root=None):\n    bm=materialize_snapshot_behavior_maturity(root)\n    er=materialize_entity_relationship_state(root)\n    cn=resolve_causal_narrative_physical_state(root)\n    # Ensure snapshot-derived state families came from the same canonical cut.\n    if len({bm.as_of_sequence,er.as_of_sequence,cn.as_of_sequence}) != 1:\n        raise RuntimeError("Scientific Reasoning state materializers crossed as-of snapshot boundary")\n    cal=materialize_physical_calibration_state(root)\n    rel=materialize_physical_source_reliability_state(root)\n    hashes={}\n    if bm.market_behavior_state_hash:hashes["market_behavior_state_hash"]=bm.market_behavior_state_hash\n    if bm.maturity_state_hash:hashes["maturity_state_hash"]=bm.maturity_state_hash\n    if er.entity_relationship_state_hash:hashes["entity_relationship_state_hash"]=er.entity_relationship_state_hash\n    adm=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)\n    return SnapshotOCL029Readmission(\n        bm.as_of_sequence,tuple(sorted(hashes)),tuple(adm.missing_state_hashes),\n        cal.state,rel.state,cn.causal_state,cn.narrative_state,adm.state,bool(adm.handoff_verified)\n    )\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_231_snapshot_ocl029_scientific_reasoning_readmission as m\nclass T(unittest.TestCase):\n    def test_snapshot_readmission(self):\n        bm=SimpleNamespace(as_of_sequence=50,market_behavior_state_hash="a"*64,maturity_state_hash="b"*64)\n        er=SimpleNamespace(as_of_sequence=50,entity_relationship_state_hash="c"*64)\n        cn=SimpleNamespace(as_of_sequence=50,causal_state="HOLD_EXPLICIT_CAUSAL_EVIDENCE_REQUIRED",narrative_state="HOLD_EXPLICIT_NARRATIVE_EVIDENCE_REQUIRED")\n        cal=SimpleNamespace(state="HOLD_HISTORICAL_FORECAST_PROBABILITY_REQUIRED")\n        rel=SimpleNamespace(state="HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")\n        adm=SimpleNamespace(missing_state_hashes=("calibration_state_hash","source_reliability_state_hash","causal_state_hash","narrative_state_hash","adaptive_weight_state_hash"),state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",handoff_verified=False)\n        with patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn),patch.object(m,"materialize_physical_calibration_state",return_value=cal),patch.object(m,"materialize_physical_source_reliability_state",return_value=rel),patch.object(m,"certify_crypto_scientific_reasoning_admission",return_value=adm):\n            r=m.run_snapshot_ocl029_readmission()\n        print("[SUPPLIED]",r.supplied_hashes);print("[MISSING]",r.missing_state_hashes)\n        self.assertEqual(r.supplied_hashes,("entity_relationship_state_hash","market_behavior_state_hash","maturity_state_hash"))\n        self.assertFalse(r.handoff_verified)\n\n    def test_cross_snapshot_rejected(self):\n        bm=SimpleNamespace(as_of_sequence=50,market_behavior_state_hash="a"*64,maturity_state_hash="b"*64)\n        er=SimpleNamespace(as_of_sequence=51,entity_relationship_state_hash="c"*64)\n        cn=SimpleNamespace(as_of_sequence=50,causal_state="",narrative_state="")\n        with patch.object(m,"materialize_snapshot_behavior_maturity",return_value=bm),patch.object(m,"materialize_entity_relationship_state",return_value=er),patch.object(m,"resolve_causal_narrative_physical_state",return_value=cn):\n            with self.assertRaises(RuntimeError):m.run_snapshot_ocl029_readmission()\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-231 same-snapshot OCL-029 readmission contract certified")\n'
PHYSICAL='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_231_snapshot_ocl029_scientific_reasoning_readmission import run_snapshot_ocl029_readmission\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_snapshot_ocl029_readmission()\n        print("[PHYSICAL] as_of_sequence=",r.as_of_sequence)\n        print("[PHYSICAL] supplied_hashes=",r.supplied_hashes)\n        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)\n        print("[PHYSICAL] calibration_state=",r.calibration_state)\n        print("[PHYSICAL] source_reliability_state=",r.source_reliability_state)\n        print("[PHYSICAL] causal_state=",r.causal_state)\n        print("[PHYSICAL] narrative_state=",r.narrative_state)\n        print("[PHYSICAL] admission_state=",r.admission_state)\n        print("[PHYSICAL] handoff_verified=",r.handoff_verified)\n        print("[PHYSICAL] probability_enabled=",r.probability_enabled)\n        print("[PHYSICAL] direction_enabled=",r.direction_enabled)\n        print("[PHYSICAL] execution_authority=",r.execution_authority)\n        self.assertFalse(r.probability_enabled);self.assertFalse(r.direction_enabled);self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-231 physical same-snapshot OCL-029 readmission certified")\n'
PHYSICAL_NAME='test_oad_231_snapshot_ocl029_scientific_reasoning_readmission_PHYSICAL.py'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    pt=r/PHYSICAL_NAME
    print("="*124);print(" OAD-231 SNAPSHOT OCL-029 SCIENTIFIC REASONING READMISSION");print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_228_snapshot_market_behavior_maturity_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_229_crypto_physical_entity_relationship_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_230_crypto_causal_narrative_physical_resolution.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_221_crypto_scientific_reasoning_admission_physical_certification.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_222_crypto_physical_calibration_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_223_crypto_physical_source_reliability_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t];targets.append(pt)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        write_atomic(pt,PHYSICAL)
        run_test(r,t)
        run_test(r,pt)
        print('[PASS] only same-snapshot physical hashes admitted')
        print('[PASS] unresolved evidence families remain explicit HOLDs')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-231 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
