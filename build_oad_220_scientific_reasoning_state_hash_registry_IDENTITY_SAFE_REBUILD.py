from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_220_SCIENTIFIC_REASONING_STATE_HASH_REGISTRY_IDENTITY_SAFE_REBUILD"
EXPECTED_INSTALLER="build_oad_220_scientific_reasoning_state_hash_registry_IDENTITY_SAFE_REBUILD.py"
MODULE_NAME="oad_220_scientific_reasoning_state_hash_registry.py"
TEST_NAME="test_oad_220_scientific_reasoning_state_hash_registry.py"

MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass

from .oad_218_existing_ocl_state_hash_envelope import envelope

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

REQUIRED_STATE_HASHES=(
    "calibration_state_hash",
    "source_reliability_state_hash",
    "market_behavior_state_hash",
    "causal_state_hash",
    "narrative_state_hash",
    "entity_relationship_state_hash",
    "maturity_state_hash",
    "adaptive_weight_state_hash",
)

CAPABILITY_BY_HASH={
    "calibration_state_hash":"calibration",
    "source_reliability_state_hash":"source_reliability",
    "market_behavior_state_hash":"market_behavior",
    "causal_state_hash":"causal",
    "narrative_state_hash":"narrative",
    "entity_relationship_state_hash":"entity_relationship",
    "maturity_state_hash":"maturity",
    "adaptive_weight_state_hash":"adaptive_weight",
}

@dataclass(frozen=True,slots=True)
class ScientificReasoningStateHashRegistry:
    hashes:dict
    missing:tuple[str,...]
    complete:bool
    fabricated:bool=False
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def build_state_hash_registry(states):
    if states is None:
        states={}
    hashes={}
    for hash_name in REQUIRED_STATE_HASHES:
        capability=CAPABILITY_BY_HASH[hash_name]
        state=states.get(capability)
        if state is not None:
            hashes[hash_name]=envelope(capability,state).state_hash

    missing=tuple(
        name for name in REQUIRED_STATE_HASHES
        if name not in hashes
    )

    return ScientificReasoningStateHashRegistry(
        hashes=hashes,
        missing=missing,
        complete=(len(missing)==0),
        fabricated=False,
        read_only=True,
        probability_enabled=False,
        direction_enabled=False,
        execution_authority=False,
    )
"""

TEST=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_220_scientific_reasoning_state_hash_registry import (
    REQUIRED_STATE_HASHES,
    CAPABILITY_BY_HASH,
    build_state_hash_registry,
)

class T(unittest.TestCase):
    def test_missing_remains_missing(self):
        r=build_state_hash_registry({
            "maturity":{"band":"immature","score":0.09},
            "adaptive_weight":{"weight":0.06},
        })
        print("[HASHES]",r.hashes)
        print("[MISSING]",r.missing)
        self.assertFalse(r.complete)
        self.assertFalse(r.fabricated)
        self.assertIn("calibration_state_hash",r.missing)
        self.assertIn("source_reliability_state_hash",r.missing)
        self.assertNotIn("maturity_state_hash",r.missing)
        self.assertNotIn("adaptive_weight_state_hash",r.missing)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

    def test_complete_only_with_all_real_states(self):
        states={
            CAPABILITY_BY_HASH[name]:{"physical":name}
            for name in REQUIRED_STATE_HASHES
        }
        r=build_state_hash_registry(states)
        self.assertTrue(r.complete)
        self.assertEqual(len(r.hashes),8)
        for value in r.hashes.values():
            self.assertEqual(len(value),64)

    def test_none_is_truthful_hold(self):
        r=build_state_hash_registry(None)
        self.assertFalse(r.complete)
        self.assertEqual(r.missing,REQUIRED_STATE_HASHES)
        self.assertEqual(r.hashes,{})

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-220 truthful Scientific Reasoning state-hash registry certified")
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
        pkg/"oad_219_crypto_maturity_adaptive_state_resolution.py",
        pkg/"oad_216_crypto_scientific_reasoning_handoff_gate.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_029_scientific_reasoning_handoff.py",
    )

    print("="*112)
    print(" OAD-220 SCIENTIFIC REASONING STATE-HASH REGISTRY — IDENTITY-SAFE REBUILD")
    print("="*112)
    print("[BOOT]",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    for dep in deps:
        if not dep.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(dep))
        print("[PASS] dependency verified:",dep.relative_to(r))

    print("[PASS] installer identity verified as OAD-220")

    old={x:(x.read_bytes() if x.exists() else None) for x in (module,test)}
    try:
        write_atomic(module,MODULE)
        write_atomic(test,TEST)

        print("[PASS] OAD-220 production module installed:",module.relative_to(r))
        print("[PASS] OAD-220 certification test installed:",test.name)

        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode:
            raise RuntimeError("OAD-220 certification test failed")

        print("[PASS] real physical states produce deterministic hashes")
        print("[PASS] unavailable states remain explicitly missing")
        print("[PASS] no placeholder/fabricated hash admitted")
        print("[PASS] probability=FALSE direction=FALSE execution=FALSE")
        print("[DONE] OAD-220 INSTALLATION COMPLETE")

    except Exception:
        for x,data in old.items():
            if data is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(data)
        print("[ROLLBACK] OAD-220 rebuild rolled back")
        raise

if __name__=="__main__":
    main()
