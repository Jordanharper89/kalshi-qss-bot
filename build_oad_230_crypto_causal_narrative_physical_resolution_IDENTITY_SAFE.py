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

REVISION='OAD_230_CRYPTO_CAUSAL_NARRATIVE_PHYSICAL_RESOLUTION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_230_crypto_causal_narrative_physical_resolution_IDENTITY_SAFE.py'
MODULE_NAME='oad_230_crypto_causal_narrative_physical_resolution.py'
TEST_NAME='test_oad_230_crypto_causal_narrative_physical_resolution.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_014_causal_evidence import verify_ocl_014_causal_evidence_learning\nfrom qseries_v2.oracle_continuous_learner.ocl_018_narrative_learning import verify_ocl_018_narrative_learning_engine\nfrom qseries_v2.oracle_continuous_learner.ocl_019_narrative_market_relationship import verify_ocl_019_narrative_market_relationship_learning\nfrom .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CausalNarrativePhysicalResolution:\n    as_of_sequence:int\n    explicit_causal_rows:int\n    explicit_narrative_rows:int\n    causal_state_hash:str|None\n    narrative_state_hash:str|None\n    causal_state:str\n    narrative_state:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef resolve_causal_narrative_physical_state(root=None,per_asset_limit=512):\n    if not verify_ocl_014_causal_evidence_learning():raise RuntimeError("OCL-014 verifier failed")\n    if not verify_ocl_018_narrative_learning_engine():raise RuntimeError("OCL-018 verifier failed")\n    if not verify_ocl_019_narrative_market_relationship_learning():raise RuntimeError("OCL-019 verifier failed")\n    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)\n    causal=[];narrative=[]\n    for row in snap.rows:\n        p=row[4] if isinstance(row[4],dict) else dict(row[4] or ())\n        if p.get("causal_evidence") is not None:causal.append(p["causal_evidence"])\n        if p.get("narrative_observations") is not None or p.get("narrative_reactions") is not None:narrative.append(p)\n    # Current crypto learned-case schema contains condition vectors and outcomes,\n    # not explicit causal evidence or narrative observations/reactions.\n    return CausalNarrativePhysicalResolution(\n        snap.as_of_sequence,len(causal),len(narrative),None,None,\n        "HOLD_EXPLICIT_CAUSAL_EVIDENCE_REQUIRED" if not causal else "HOLD_CAUSAL_PROVENANCE_VALIDATION_REQUIRED",\n        "HOLD_EXPLICIT_NARRATIVE_EVIDENCE_REQUIRED" if not narrative else "HOLD_NARRATIVE_PROVENANCE_VALIDATION_REQUIRED",\n    )\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_230_crypto_causal_narrative_physical_resolution as m\nclass T(unittest.TestCase):\n    def test_truthful_hold(self):\n        snap=SimpleNamespace(as_of_sequence=10,rows=((10,"o","s","t",{"asset":"BTC","condition_vector":()}),))\n        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):\n            r=m.resolve_causal_narrative_physical_state()\n        print("[CAUSAL]",r.causal_state,"[NARRATIVE]",r.narrative_state)\n        self.assertIsNone(r.causal_state_hash);self.assertIsNone(r.narrative_state_hash)\n        self.assertEqual(r.explicit_causal_rows,0);self.assertEqual(r.explicit_narrative_rows,0)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-230 causal/narrative physical evidence resolver certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-230 CRYPTO CAUSAL + NARRATIVE PHYSICAL RESOLUTION");print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_227_crypto_learned_case_asof_snapshot_boundary.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_014_causal_evidence.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_018_narrative_learning.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_019_narrative_market_relationship.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] correlation/condition co-occurrence is not promoted to causal evidence')
        print('[PASS] condition vectors are not relabeled as narratives')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-230 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
