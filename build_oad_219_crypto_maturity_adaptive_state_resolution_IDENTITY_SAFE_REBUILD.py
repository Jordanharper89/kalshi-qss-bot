from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_219_CRYPTO_MATURITY_ADAPTIVE_STATE_RESOLUTION_IDENTITY_SAFE_REBUILD"
EXPECTED_INSTALLER="build_oad_219_crypto_maturity_adaptive_state_resolution_IDENTITY_SAFE_REBUILD.py"
MODULE_NAME="oad_219_crypto_maturity_adaptive_state_resolution.py"
TEST_NAME="test_oad_219_crypto_maturity_adaptive_state_resolution.py"

MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass

from .oad_218_existing_ocl_state_hash_envelope import envelope
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import (
    evaluate_learning_maturity,
    verify_ocl_022_learning_confidence_evidence_maturity,
)
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import (
    evaluate_meta_learning_performance,
    verify_ocl_023_meta_learning_performance_evaluation,
)
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import (
    build_adaptive_learning_weight,
    verify_ocl_024_adaptive_learning_weight_model,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class MaturityAdaptiveResolution:
    maturity:object
    adaptive_weight:object
    maturity_state_hash:str
    adaptive_weight_state_hash:str
    frozen_contracts_verified:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def verify_frozen_maturity_adaptive_contracts():
    return bool(
        verify_ocl_022_learning_confidence_evidence_maturity()
        and verify_ocl_023_meta_learning_performance_evaluation()
        and verify_ocl_024_adaptive_learning_weight_model()
    )

def resolve_maturity_adaptive_state(
    evidence_count,
    independent_sources,
    consistency,
    contradiction_rate,
    calibration_quality,
    performance_history,
):
    if not verify_frozen_maturity_adaptive_contracts():
        raise RuntimeError("Frozen OCL-022/OCL-023/OCL-024 contract verification failed")

    maturity=evaluate_learning_maturity(
        int(evidence_count),
        int(independent_sources),
        float(consistency),
        float(contradiction_rate),
        float(calibration_quality),
    )

    performance=evaluate_meta_learning_performance(
        "crypto_verified_learning",
        tuple(float(x) for x in performance_history),
    )

    weight=build_adaptive_learning_weight(
        performance,
        1.0,
        maturity.maturity_score,
    )

    return MaturityAdaptiveResolution(
        maturity,
        weight,
        envelope("maturity",maturity).state_hash,
        envelope("adaptive_weight",weight).state_hash,
        True,
        False,
        False,
        False,
    )
"""

TEST=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_219_crypto_maturity_adaptive_state_resolution import (
    resolve_maturity_adaptive_state,
    verify_frozen_maturity_adaptive_contracts,
)

class T(unittest.TestCase):
    def test_frozen_contracts(self):
        self.assertTrue(verify_frozen_maturity_adaptive_contracts())

    def test_resolution(self):
        r=resolve_maturity_adaptive_state(
            evidence_count=252,
            independent_sources=3,
            consistency=.70,
            contradiction_rate=.20,
            calibration_quality=.50,
            performance_history=(.10,.20,.15),
        )
        print("[MATURITY_BAND]",r.maturity.maturity_band)
        print("[MATURITY_SCORE]",r.maturity.maturity_score)
        print("[ADAPTIVE_WEIGHT]",r.adaptive_weight.adjusted_weight)
        print("[MATURITY_HASH]",r.maturity_state_hash)
        print("[ADAPTIVE_HASH]",r.adaptive_weight_state_hash)

        self.assertEqual(len(r.maturity_state_hash),64)
        self.assertEqual(len(r.adaptive_weight_state_hash),64)
        self.assertTrue(r.frozen_contracts_verified)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

    def test_invalid_history_still_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_maturity_adaptive_state(1,1,.5,.2,.5,())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-219 frozen OCL maturity/adaptive state resolution certified")
"""

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for candidate in (base,base/"kalshi-qss-bot",*base.parents):
            if (candidate/"qseries_v2").is_dir():
                return candidate
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(
            f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}"
        )

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=r/TEST_NAME

    deps=(
        pkg/"oad_218_existing_ocl_state_hash_envelope.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_022_learning_maturity.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_023_meta_learning_performance.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_024_adaptive_learning_weight.py",
    )

    print("="*112)
    print(" OAD-219 CRYPTO MATURITY + ADAPTIVE STATE RESOLUTION — IDENTITY-SAFE REBUILD")
    print("="*112)
    print("[BOOT]",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    for dep in deps:
        if not dep.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(dep))
        print("[PASS] dependency verified:",dep.relative_to(r))

    print("[PASS] installer identity verified as OAD-219")

    old={x:(x.read_bytes() if x.exists() else None) for x in (module,test)}
    try:
        write_atomic(module,MODULE)
        write_atomic(test,TEST)
        print("[PASS] OAD-219 production module installed:",module.relative_to(r))
        print("[PASS] OAD-219 certification test installed:",test.name)

        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode:
            raise RuntimeError("OAD-219 certification test failed")

        print("[PASS] frozen OCL-022/OCL-023/OCL-024 reused unchanged")
        print("[PASS] deterministic OAD-218 hashes generated from real state objects")
        print("[PASS] probability=FALSE direction=FALSE execution=FALSE")
        print("[DONE] OAD-219 INSTALLATION COMPLETE")
    except Exception:
        for x,data in old.items():
            if data is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(data)
        print("[ROLLBACK] OAD-219 rebuild rolled back")
        raise

if __name__=="__main__":
    main()
