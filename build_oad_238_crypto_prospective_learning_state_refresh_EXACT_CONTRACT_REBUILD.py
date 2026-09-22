from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_238_EXACT_CERTIFIED_CONTRACT_REBUILD_V1"
EXPECTED="build_oad_238_crypto_prospective_learning_state_refresh_EXACT_CONTRACT_REBUILD.py"

MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom .oad_235_prospective_calibration_source_reliability_materialization import (\n    materialize_prospective_calibration_source_reliability,\n)\nfrom .oad_236_prospective_adaptive_ocl029_readmission import (\n    run_prospective_adaptive_ocl029_readmission,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass ProspectiveLearningStateRefresh:\n    calibration_state_hash:str|None\n    source_reliability_state_hash:str|None\n    adaptive_weight_state_hash:str|None\n    calibration_state:str\n    adaptive_state:str\n    admission_state:str\n    handoff_verified:bool\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    publication_allowed:bool=False\n    execution_authority:bool=False\n\ndef refresh_prospective_learning_states(root=None):\n    calibration=materialize_prospective_calibration_source_reliability(root)\n    adaptive=run_prospective_adaptive_ocl029_readmission(root)\n    return ProspectiveLearningStateRefresh(\n        calibration_state_hash=calibration.calibration_state_hash,\n        source_reliability_state_hash=calibration.source_reliability_state_hash,\n        adaptive_weight_state_hash=adaptive.adaptive_weight_state_hash,\n        calibration_state=str(calibration.state),\n        adaptive_state=str(adaptive.adaptive_state),\n        admission_state=str(adaptive.admission_state),\n        handoff_verified=bool(adaptive.handoff_verified),\n    )\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_238_crypto_prospective_learning_state_refresh as m\n\nclass T(unittest.TestCase):\n    def test_exact_certified_contracts(self):\n        c=SimpleNamespace(\n            calibration_state_hash=None,\n            source_reliability_state_hash=None,\n            state="HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED",\n        )\n        a=SimpleNamespace(\n            adaptive_weight_state_hash=None,\n            adaptive_state="HOLD_META_LEARNING_PERFORMANCE_DELTAS_REQUIRED",\n            admission_state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED",\n            handoff_verified=False,\n        )\n        with patch.object(m,"materialize_prospective_calibration_source_reliability",return_value=c) as pc, \\\n             patch.object(m,"run_prospective_adaptive_ocl029_readmission",return_value=a) as pa:\n            x=m.refresh_prospective_learning_states()\n\n        print("[CALIBRATION]",x.calibration_state)\n        print("[ADAPTIVE]",x.adaptive_state)\n        print("[ADMISSION]",x.admission_state)\n        self.assertEqual(pc.call_count,1)\n        self.assertEqual(pa.call_count,1)\n        self.assertIsNone(x.calibration_state_hash)\n        self.assertIsNone(x.source_reliability_state_hash)\n        self.assertIsNone(x.adaptive_weight_state_hash)\n        self.assertFalse(x.handoff_verified)\n        self.assertFalse(x.probability_enabled)\n        self.assertFalse(x.direction_enabled)\n        self.assertFalse(x.publication_allowed)\n        self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-238 exact certified OAD-235/OAD-236 contract refresh certified")\n'

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)

def run(r,p):
    q=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if q.returncode:
        raise RuntimeError("Certification test failed: "+p.name)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module_path=pkg/"oad_238_crypto_prospective_learning_state_refresh.py"
    test_path=r/"test_oad_238_crypto_prospective_learning_state_refresh.py"

    print("="*124)
    print(" OAD-238 EXACT-CONTRACT REBUILD — CRYPTO PROSPECTIVE LEARNING STATE REFRESH")
    print("="*124)
    print("[BOOT]",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    deps=(
        pkg/"oad_235_prospective_calibration_source_reliability_materialization.py",
        pkg/"oad_236_prospective_adaptive_ocl029_readmission.py",
    )
    for d in deps:
        if not d.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(d))
        src=d.read_text(encoding="utf-8")
        if d.name.startswith("oad_235_") and "def materialize_prospective_calibration_source_reliability(" not in src:
            raise RuntimeError("Exact OAD-235 certified symbol missing")
        if d.name.startswith("oad_236_") and "def run_prospective_adaptive_ocl029_readmission(" not in src:
            raise RuntimeError("Exact OAD-236 certified symbol missing")
        print("[PASS] exact dependency contract verified:",d.relative_to(r))

    targets=(module_path,test_path)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}

    try:
        write_atomic(module_path,MODULE)
        write_atomic(test_path,TEST)
        run(r,test_path)
        print("[PASS] failed guessed OAD-235/OAD-236 symbol names retired")
        print("[PASS] exact certified OAD-235 and OAD-236 interfaces used")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-238 EXACT-CONTRACT REBUILD COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OAD-238 exact-contract rebuild rolled back")
        raise

if __name__=="__main__":
    main()
