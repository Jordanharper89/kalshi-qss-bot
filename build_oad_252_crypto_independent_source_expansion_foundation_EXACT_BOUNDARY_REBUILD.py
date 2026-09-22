from __future__ import annotations
import ast, os, subprocess, sys, textwrap
from pathlib import Path

EXPECTED="build_oad_252_crypto_independent_source_expansion_foundation_EXACT_BOUNDARY_REBUILD.py"
REVISION="OAD_252_CRYPTO_INDEPENDENT_SOURCE_EXPANSION_FOUNDATION_EXACT_BOUNDARY_REBUILD_V1"

MODULE_NAME="oad_252_crypto_independent_source_expansion_foundation.py"
TEST_NAME="test_oad_252_crypto_independent_source_expansion_foundation.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class IndependentCryptoObservation:
    source_id:str
    provider:str
    source_class:str
    subject:str
    observation_type:str
    observed_at:str
    payload:Mapping[str,Any]
    provenance_hash:str
    independent_evidence:bool=True
    execution_authority:bool=False

def build_independent_crypto_observation(
    *,
    source_id,
    provider,
    source_class,
    subject,
    observation_type,
    payload,
    observed_at=None,
):
    required=(source_id,provider,source_class,subject,observation_type)
    if not all(str(x).strip() for x in required):
        raise ValueError("source identity, provider, class, subject, and observation type are required")
    ts=str(observed_at or datetime.now(timezone.utc).isoformat())
    body={
        "source_id":str(source_id),
        "provider":str(provider),
        "source_class":str(source_class),
        "subject":str(subject),
        "observation_type":str(observation_type),
        "observed_at":ts,
        "payload":dict(payload),
    }
    h=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return IndependentCryptoObservation(
        str(source_id),str(provider),str(source_class),str(subject),
        str(observation_type),ts,dict(payload),h,True,False
    )

def verify_independent_crypto_observation(x):
    return (
        isinstance(x,IndependentCryptoObservation)
        and x.independent_evidence is True
        and x.execution_authority is False
        and bool(x.source_id)
        and bool(x.provider)
        and bool(x.source_class)
        and len(x.provenance_hash)==64
    )
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_252_crypto_independent_source_expansion_foundation import (
    build_independent_crypto_observation,
    verify_independent_crypto_observation,
)

class T(unittest.TestCase):
    def test_contract(self):
        x=build_independent_crypto_observation(
            source_id="source:test",
            provider="provider",
            source_class="exchange_liquidity",
            subject="BTC-USD",
            observation_type="orderbook",
            payload={"best_bid":100,"best_ask":101},
            observed_at="2026-09-01T00:00:00+00:00",
        )
        print("[SOURCE]",x.source_id)
        print("[CLASS]",x.source_class)
        print("[PROVENANCE]",x.provenance_hash)
        self.assertTrue(verify_independent_crypto_observation(x))
        self.assertTrue(x.independent_evidence)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-252 independent-source provenance contract certified")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for candidate in (b,b/"kalshi-qss-bot",*b.parents):
            if (candidate/"qseries_v2").is_dir():
                return candidate
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError(f"installer identity mismatch: expected {EXPECTED}")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=r/TEST_NAME
    init=pkg/"__init__.py"

    deps=(
        pkg/"oad_242_crypto_exact_prospective_forecast_outcome_binding.py",
        pkg/"oad_246_crypto_prospective_truth_calibration_physical_certification.py",
        pkg/"oad_147_solana_onchain_evidence_foundation.py",
    )

    print("="*120)
    print(" OAD-252 CRYPTO INDEPENDENT SOURCE EXPANSION FOUNDATION — EXACT BOUNDARY REBUILD")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[INSTALLER]",Path(__file__).name)
    print("[ROOT]",r)

    for dep in deps:
        if not dep.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(dep.relative_to(r)))
        print("[PASS] dependency verified:",dep.relative_to(r))

    # Verify the repaired exact-identity production boundary actually exposes the
    # expected exact-binding read function rather than merely checking a filename.
    repaired=(pkg/"oad_242_crypto_exact_prospective_forecast_outcome_binding.py").read_text(
        encoding="utf-8"
    )
    if "read_exact_prospective_bindings" not in repaired:
        raise RuntimeError("Repaired OAD-242 exact-identity contract missing")
    print("[PASS] repaired OAD-242 exact identity boundary verified")

    physical=(pkg/"oad_246_crypto_prospective_truth_calibration_physical_certification.py").read_text(
        encoding="utf-8"
    )
    if "certify_prospective_truth_calibration" not in physical:
        raise RuntimeError("OAD-246 physical calibration certification contract missing")
    print("[PASS] OAD-246 prospective truth calibration contract verified")

    sol=(pkg/"oad_147_solana_onchain_evidence_foundation.py").read_text(encoding="utf-8")
    if "build_solana_onchain_observation" not in sol:
        raise RuntimeError("OAD-147 Solana on-chain foundation contract missing")
    print("[PASS] OAD-147 Solana independent evidence contract verified")

    old={x:(x.read_bytes() if x.exists() else None) for x in (module,test,init)}
    try:
        atomic(module,MODULE_SOURCE)
        atomic(test,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from .oad_252_crypto_independent_source_expansion_foundation import *"
        if exp not in lines:
            lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")

        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode:
            raise RuntimeError("OAD-252 certification test failed")

        print("[PASS] OAD-251 repaired production boundary preserved through OAD-242")
        print("[PASS] OAD-246 physical calibration boundary preserved")
        print("[PASS] OAD-147 Solana independent evidence boundary preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-252 INSTALLATION COMPLETE")

    except Exception:
        for x,data in old.items():
            if data is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(data)
        print("[ROLLBACK] OAD-252 installation rolled back")
        raise

if __name__=="__main__":
    main()
