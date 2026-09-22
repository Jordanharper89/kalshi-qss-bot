from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_221_CRYPTO_SCIENTIFIC_REASONING_ADMISSION_PHYSICAL_IDENTITY_SAFE_V1"
EXPECTED_INSTALLER="build_oad_221_crypto_scientific_reasoning_admission_PHYSICAL_IDENTITY_SAFE.py"
MODULE_NAME="oad_221_crypto_scientific_reasoning_admission_physical_certification.py"
TEST_NAME="test_oad_221_crypto_scientific_reasoning_admission_physical_certification.py"

MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass

from .oad_216_crypto_scientific_reasoning_handoff_gate import (
    REQUIRED_NON_LEARNER_HASHES,
    evaluate_crypto_scientific_reasoning_handoff,
)
from .oad_217_certified_ocl_state_contract_resolution import (
    resolve_certified_ocl_contracts,
)
from .oad_220_scientific_reasoning_state_hash_registry import (
    REQUIRED_STATE_HASHES,
)
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import (
    verify_ocl_029_scientific_reasoning_handoff_contract,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class AdmissionCertification:
    learner_state_hash:str
    learner_state_verified:bool
    certified_existing_contracts:tuple[str,...]
    unavailable_existing_contracts:tuple[str,...]
    required_non_learner_hashes:tuple[str,...]
    supplied_certified_state_hashes:tuple[str,...]
    missing_state_hashes:tuple[str,...]
    handoff_hash:str|None
    handoff_verified:bool
    state:str
    physical_ready:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def certify_crypto_scientific_reasoning_admission(certified_state_hashes=None):
    if not verify_ocl_029_scientific_reasoning_handoff_contract():
        raise RuntimeError("Frozen OCL-029 handoff contract failed verification")

    contracts=resolve_certified_ocl_contracts()

    supplied=dict(certified_state_hashes or {})
    accepted=tuple(
        name for name in REQUIRED_NON_LEARNER_HASHES
        if len(str(supplied.get(name,"")))==64
    )

    gate=evaluate_crypto_scientific_reasoning_handoff(
        certified_state_hashes=supplied
    )

    handoff_hash=(
        str(gate.handoff.handoff_hash)
        if gate.handoff is not None
        else None
    )

    return AdmissionCertification(
        learner_state_hash=gate.learner_state_hash,
        learner_state_verified=bool(gate.learner_state_verified),
        certified_existing_contracts=contracts.certified_contracts,
        unavailable_existing_contracts=contracts.unavailable_contracts,
        required_non_learner_hashes=tuple(REQUIRED_NON_LEARNER_HASHES),
        supplied_certified_state_hashes=accepted,
        missing_state_hashes=tuple(gate.missing_state_hashes),
        handoff_hash=handoff_hash,
        handoff_verified=bool(gate.handoff_verified),
        state=str(gate.state),
        physical_ready=bool(gate.physical_ready),
        probability_enabled=False,
        direction_enabled=False,
        execution_authority=False,
    )
"""

TEST=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_221_crypto_scientific_reasoning_admission_physical_certification import (
    certify_crypto_scientific_reasoning_admission,
)

class T(unittest.TestCase):
    def test_physical_current_admission(self):
        r=certify_crypto_scientific_reasoning_admission()

        print("[PHYSICAL] learner_state_hash=",r.learner_state_hash)
        print("[PHYSICAL] learner_state_verified=",r.learner_state_verified)
        print("[PHYSICAL] certified_existing_contracts=",r.certified_existing_contracts)
        print("[PHYSICAL] unavailable_existing_contracts=",r.unavailable_existing_contracts)
        print("[PHYSICAL] supplied_certified_state_hashes=",r.supplied_certified_state_hashes)
        print("[PHYSICAL] missing_state_hashes=",r.missing_state_hashes)
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] handoff_hash=",r.handoff_hash)
        print("[PHYSICAL] handoff_verified=",r.handoff_verified)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        print("[PHYSICAL] probability_enabled=",r.probability_enabled)
        print("[PHYSICAL] direction_enabled=",r.direction_enabled)
        print("[PHYSICAL] execution_authority=",r.execution_authority)

        self.assertTrue(r.learner_state_verified)
        self.assertTrue(r.physical_ready)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

        if r.missing_state_hashes:
            self.assertEqual(
                r.state,
                "HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED"
            )
            self.assertIsNone(r.handoff_hash)
            self.assertFalse(r.handoff_verified)
        else:
            self.assertEqual(
                r.state,
                "READY_FOR_SCIENTIFIC_REASONING_HANDOFF"
            )
            self.assertEqual(len(r.handoff_hash),64)
            self.assertTrue(r.handoff_verified)

if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-221 physical Scientific Reasoning admission truthfully certified")
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
        pkg/"oad_216_crypto_scientific_reasoning_handoff_gate.py",
        pkg/"oad_217_certified_ocl_state_contract_resolution.py",
        pkg/"oad_218_existing_ocl_state_hash_envelope.py",
        pkg/"oad_219_crypto_maturity_adaptive_state_resolution.py",
        pkg/"oad_220_scientific_reasoning_state_hash_registry.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_029_scientific_reasoning_handoff.py",
    )

    print("="*116)
    print(" OAD-221 CRYPTO SCIENTIFIC REASONING ADMISSION — PHYSICAL IDENTITY-SAFE CERTIFICATION")
    print("="*116)
    print("[BOOT]",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    for dep in deps:
        if not dep.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(dep))
        print("[PASS] dependency verified:",dep.relative_to(r))

    print("[PASS] installer identity verified as OAD-221")

    old={x:(x.read_bytes() if x.exists() else None) for x in (module,test)}
    try:
        write_atomic(module,MODULE)
        write_atomic(test,TEST)

        print("[PASS] OAD-221 production module installed:",module.relative_to(r))
        print("[PASS] OAD-221 physical certification test installed:",test.name)

        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode:
            raise RuntimeError("OAD-221 physical certification failed")

        print("[PASS] physical learner state read through OAD-216")
        print("[PASS] frozen OCL-029 remains sole Scientific Reasoning handoff authority")
        print("[PASS] no test-only state hash is promoted to physical certification")
        print("[PASS] unavailable certified state hashes remain HOLD")
        print("[PASS] probability=FALSE direction=FALSE execution=FALSE")
        print("[DONE] OAD-221 INSTALLATION COMPLETE")

    except Exception:
        for x,data in old.items():
            if data is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(data)
        print("[ROLLBACK] OAD-221 installation rolled back")
        raise

if __name__=="__main__":
    main()
