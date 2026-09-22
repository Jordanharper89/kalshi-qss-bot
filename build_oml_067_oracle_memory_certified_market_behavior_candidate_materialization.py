from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

AUTH_MODULE = PACKAGE / "oracle_memory_certified_market_behavior_candidate_materialization_067_authorization_gate_066.py"
AUTH_TEST = ROOT / "test_oml_066_oracle_memory_certified_market_behavior_candidate_materialization_067_authorization_gate_066.py"
BRIDGE_MODULE = PACKAGE / "oracle_memory_certified_market_behavior_observation_intake_bridge.py"
BRIDGE_TEST = ROOT / "test_oml_065_oracle_memory_certified_market_behavior_observation_intake_bridge.py"
MATERIALIZATION_MODULE = PACKAGE / "oracle_memory_certified_observation_candidate_materialization.py"
MATERIALIZATION_TEST = ROOT / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_candidate_materialization_067.py"
TEST = ROOT / "test_oml_067_oracle_memory_certified_market_behavior_candidate_materialization_067.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_067_authorization_gate_066 import (
    OracleMemoryMarketBehaviorMaterializationAuthorizationDecision,
    verify_oracle_memory_market_behavior_materialization_authorization_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge import (
    OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge,
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    build_oracle_memory_observation_candidate_materialization_batch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID

SCHEMA_VERSION = "OML-067"
ENGINE_ID = "OML-067"
POLICY_ID = "oracle-memory.certified-market-behavior-candidate-materialization-067.v1"
AUTH_SCHEMA_VERSION = "OML-066"
AUTH_ENGINE_ID = "OML-066"
BRIDGE_SCHEMA_VERSION = "OML-065"
BRIDGE_ENGINE_ID = "OML-065"
MATERIALIZATION_SCHEMA_VERSION = "OML-028"
MATERIALIZATION_ENGINE_ID = "OML-028"
STATE_READ_ONLY = "read_only_market_behavior_candidate_materialization_067"


class OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCandidateMaterialization067:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    authorization_schema_version: str
    authorization_engine_id: str
    authorization_decision_hash: str
    bridge_schema_version: str
    bridge_engine_id: str
    bridge_certification_hash: str
    intake_batch_hash: str
    registry_gate_decision_hash: str
    materialization_schema_version: str
    materialization_engine_id: str
    materialization_batch: OracleMemoryObservationCandidateMaterializationBatch
    observation_count: int
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    state: str
    authorization_lineage_verified: bool
    bridge_lineage_verified: bool
    registry_gate_lineage_verified: bool
    observation_candidate_lineage_verified: bool
    source_certification_lineage_verified: bool
    deterministic_materialization_verified: bool
    duplicate_detection_verified: bool
    candidate_admission_authorized: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    materialization_ready: bool
    downstream_validation_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError("unsupported OML-067 value type")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-067 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError(f"OML-067 invalid {label} hexadecimal value") from exc


def build_oracle_memory_certified_market_behavior_candidate_materialization_067_067(
    *,
    authorization: OracleMemoryMarketBehaviorMaterializationAuthorizationDecision,
    bridge: OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge,
    registry_gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
) -> OracleMemoryCertifiedMarketBehaviorCandidateMaterialization067:
    verify_oracle_memory_market_behavior_materialization_authorization_decision(authorization)
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge(bridge)
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(registry_gate_decision)

    if authorization.schema_version != AUTH_SCHEMA_VERSION or authorization.engine_id != AUTH_ENGINE_ID:
        _reject("OML-067 authorization identity mismatch")
    if bridge.schema_version != BRIDGE_SCHEMA_VERSION or bridge.engine_id != BRIDGE_ENGINE_ID:
        _reject("OML-067 bridge identity mismatch")
    if authorization.upstream_certification_hash != bridge.certification_hash:
        _reject("OML-067 authorization-to-bridge certification mismatch")
    if authorization.upstream_intake_batch_hash != bridge.intake_batch.batch_hash:
        _reject("OML-067 authorization-to-intake lineage mismatch")
    if not authorization.candidate_materialization_authorized:
        _reject("OML-067 candidate materialization not authorized")
    if authorization.candidate_admission_authorized:
        _reject("OML-067 candidate admission unexpectedly authorized")
    if not authorization.read_only or not bridge.read_only:
        _reject("OML-067 upstream read-only guarantee missing")

    batch = build_oracle_memory_observation_candidate_materialization_batch(
        gate_decision=registry_gate_decision,
        intake_batch=bridge.intake_batch,
    )
    verify_oracle_memory_observation_candidate_materialization_batch(batch)

    if batch.schema_version != MATERIALIZATION_SCHEMA_VERSION or batch.engine_id != MATERIALIZATION_ENGINE_ID:
        _reject("OML-067 OML-028 materialization identity mismatch")
    if batch.upstream_batch_hash != bridge.intake_batch.batch_hash:
        _reject("OML-067 bridge-to-materialization batch mismatch")
    if batch.upstream_gate_decision_hash != registry_gate_decision.decision_hash:
        _reject("OML-067 registry gate lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "authorization_schema_version": authorization.schema_version,
        "authorization_engine_id": authorization.engine_id,
        "authorization_decision_hash": authorization.decision_hash,
        "bridge_schema_version": bridge.schema_version,
        "bridge_engine_id": bridge.engine_id,
        "bridge_certification_hash": bridge.certification_hash,
        "intake_batch_hash": bridge.intake_batch.batch_hash,
        "registry_gate_decision_hash": registry_gate_decision.decision_hash,
        "materialization_schema_version": batch.schema_version,
        "materialization_engine_id": batch.engine_id,
        "materialization_batch": batch,
        "observation_count": batch.observation_count,
        "candidate_count": batch.candidate_count,
        "unique_candidate_count": batch.unique_candidate_count,
        "duplicate_candidate_count": batch.duplicate_candidate_count,
        "state": STATE_READ_ONLY,
        "authorization_lineage_verified": True,
        "bridge_lineage_verified": True,
        "registry_gate_lineage_verified": True,
        "observation_candidate_lineage_verified": batch.observation_candidate_lineage_verified,
        "source_certification_lineage_verified": batch.source_certification_lineage_verified,
        "deterministic_materialization_verified": batch.deterministic_materialization_verified,
        "duplicate_detection_verified": batch.duplicate_detection_verified,
        "candidate_admission_authorized": False,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "materialization_ready": True,
        "downstream_validation_authorized": True,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorCandidateMaterialization067(**body, certification_hash=_stable_hash(body))
    verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(result)
    return result


def verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(
    result: OracleMemoryCertifiedMarketBehaviorCandidateMaterialization067,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-067 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID or result.policy_id != POLICY_ID:
        _reject("OML-067 identity mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-067 subsystem mismatch")
    if result.authorization_schema_version != AUTH_SCHEMA_VERSION or result.authorization_engine_id != AUTH_ENGINE_ID:
        _reject("OML-067 authorization lineage mismatch")
    if result.bridge_schema_version != BRIDGE_SCHEMA_VERSION or result.bridge_engine_id != BRIDGE_ENGINE_ID:
        _reject("OML-067 bridge lineage mismatch")
    if result.materialization_schema_version != MATERIALIZATION_SCHEMA_VERSION or result.materialization_engine_id != MATERIALIZATION_ENGINE_ID:
        _reject("OML-067 materialization lineage mismatch")
    for value, label in (
        (result.authorization_decision_hash, "authorization decision hash"),
        (result.bridge_certification_hash, "bridge certification hash"),
        (result.intake_batch_hash, "intake batch hash"),
        (result.registry_gate_decision_hash, "registry gate decision hash"),
        (result.certification_hash, "certification hash"),
    ):
        _require_hash(value, label)
    verify_oracle_memory_observation_candidate_materialization_batch(result.materialization_batch)
    batch = result.materialization_batch
    if batch.upstream_batch_hash != result.intake_batch_hash:
        _reject("OML-067 intake batch lineage mismatch")
    if batch.upstream_gate_decision_hash != result.registry_gate_decision_hash:
        _reject("OML-067 gate decision lineage mismatch")
    if result.observation_count != batch.observation_count or result.candidate_count != batch.candidate_count:
        _reject("OML-067 count mismatch")
    if result.unique_candidate_count != batch.unique_candidate_count or result.duplicate_candidate_count != batch.duplicate_candidate_count:
        _reject("OML-067 duplicate count mismatch")
    if result.state != STATE_READ_ONLY:
        _reject("OML-067 state invalid")
    if not all((result.authorization_lineage_verified, result.bridge_lineage_verified, result.registry_gate_lineage_verified, result.observation_candidate_lineage_verified, result.source_certification_lineage_verified, result.deterministic_materialization_verified, result.duplicate_detection_verified, result.materialization_ready, result.downstream_validation_authorized, result.read_only)):
        _reject("OML-067 guarantee missing")
    if any((result.candidate_admission_authorized, result.persistence_enabled, result.learning_updates_enabled, result.runtime_activation_enabled, result.publication_enabled, result.action_authorization_enabled, result.qseries_execution_enabled)):
        _reject("OML-067 forbidden capability enabled")
    return True
'''

TEST_SOURCE = r'''
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_067 import (
    OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError,
    build_oracle_memory_certified_market_behavior_candidate_materialization_067_067,
    verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError:
        return
    raise AssertionError(f"tampered OML-067 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-067 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture_066 = load_module(
        root
        / "test_oml_066_oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate.py",
        "oml_066_fixture_for_oml_067",
    )
    bridge = fixture_066.build_bridge(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate_066 import (
        build_oracle_memory_market_behavior_materialization_authorization_decision,
    )

    authorization = (
        build_oracle_memory_market_behavior_materialization_authorization_decision(
            bridge=bridge,
        )
    )


    fixture_028 = load_module(
        root / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_067",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    result = build_oracle_memory_certified_market_behavior_candidate_materialization_067_067(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )

    assert result.schema_version == "OML-067"
    assert result.engine_id == "OML-067"
    assert result.authorization_schema_version == "OML-066"
    assert result.bridge_schema_version == "OML-065"
    assert result.materialization_schema_version == "OML-028"
    assert result.authorization_decision_hash == authorization.decision_hash
    assert result.bridge_certification_hash == bridge.certification_hash
    assert result.intake_batch_hash == bridge.intake_batch.batch_hash
    assert result.registry_gate_decision_hash == registry_gate_decision.decision_hash
    assert result.observation_count == bridge.observation_count
    assert result.candidate_count == bridge.observation_count
    assert result.materialization_batch.materialization_ready
    assert not result.candidate_admission_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.downstream_validation_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_candidate_materialization_067_067(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(result)

    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(replace(result, candidate_admission_authorized=True)), "candidate admission")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(replace(result, persistence_enabled=True)), "persistence")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(replace(result, qseries_execution_enabled=True)), "Q Series execution")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067_067(replace(result, certification_hash="f" * 64)), "certification hash")

    print("[PASS] Certified OML-066 authorization consumed read-only")
    print("[PASS] Exact OML-065 intake batch passed directly")
    print("[PASS] Certified OML-008 registry gate decision passed directly")
    print("[PASS] Actual OML-028 materialization builder consumed")
    print("[PASS] Observation-to-candidate lineage retained")
    print("[PASS] Source-certification lineage retained")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-067 materializations rejected")
    print("[DONE] OML-067 CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate() -> None:
    required = (AUTH_MODULE, AUTH_TEST, BRIDGE_MODULE, BRIDGE_TEST, MATERIALIZATION_MODULE, MATERIALIZATION_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required certified files missing: " + ", ".join(missing))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    auth = importlib.import_module("qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_067_authorization_gate_066")
    bridge = importlib.import_module("qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge")
    materialization = importlib.import_module("qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization")

    expected = (
        (auth, {"SCHEMA_VERSION": "OML-066", "ENGINE_ID": "OML-066", "POLICY_ID": "oracle-memory.certified-market-behavior-candidate-materialization-authorization-gate.v1"}, "OML-066"),
        (bridge, {"SCHEMA_VERSION": "OML-065", "ENGINE_ID": "OML-065", "POLICY_ID": "oracle-memory.certified-market-behavior-observation-intake-bridge.v1"}, "OML-065"),
        (materialization, {"SCHEMA_VERSION": "OML-028", "ENGINE_ID": "OML-028", "UPSTREAM_SCHEMA_VERSION": "OML-027", "UPSTREAM_ENGINE_ID": "OML-027"}, "OML-028"),
    )
    for module, values, label in expected:
        for name, value in values.items():
            if getattr(module, name, None) != value:
                raise RuntimeError(f"Certified {label} {name} mismatch")

    required_symbols = {
        auth: ("OracleMemoryMarketBehaviorMaterializationAuthorizationDecision", "verify_oracle_memory_market_behavior_materialization_authorization_decision"),
        bridge: ("OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge", "verify_oracle_memory_certified_market_behavior_observation_intake_bridge"),
        materialization: ("OracleMemoryObservationCandidateMaterializationBatch", "build_oracle_memory_observation_candidate_materialization_batch", "verify_oracle_memory_observation_candidate_materialization_batch"),
    }
    for module, names in required_symbols.items():
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError("Certified symbol(s) missing: " + ", ".join(missing_names))

    params = set(inspect.signature(materialization.build_oracle_memory_observation_candidate_materialization_batch).parameters)
    if params != {"gate_decision", "intake_batch"}:
        raise RuntimeError("Certified OML-028 builder signature mismatch: " + ", ".join(sorted(params)))


def main() -> int:
    print("=" * 48)
    print(" OML-067 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_053_052_028_INTERFACE_ALIGNMENT")
    try:
        validate()
        print("[OK] Actual OML-066 authorization contract inspected")
        print("[OK] Actual OML-065 bridge contract inspected")
        print("[OK] Actual OML-028 dataclasses, verifier, and builder signature inspected")

        for path, label in ((AUTH_TEST, "OML-066"), (BRIDGE_TEST, "OML-065"), (MATERIALIZATION_TEST, "OML-028")):
            run = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
            if run.returncode:
                raise RuntimeError(f"{label} certification failed with exit code {run.returncode}")

        tracked = {path: path.read_bytes() for path in (AUTH_MODULE, AUTH_TEST, BRIDGE_MODULE, BRIDGE_TEST, MATERIALIZATION_MODULE, MATERIALIZATION_TEST)}
        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_market_behavior_candidate_materialization_067 import *"
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"OML-067 test failed with exit code {completed.returncode}")

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-066 unchanged")
        print("[PASS] Certified OML-065 unchanged")
        print("[PASS] Certified OML-028 unchanged")
        print("[PASS] Exact upstream dataclasses consumed directly")
        print("[PASS] OML-067 production fully replaced")
        print("[PASS] OML-067 standalone deterministic test installed")
        print("[PASS] Candidate admission remained disabled")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-067  CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION INSTALLED")
        return 0
    except (RuntimeError, SyntaxError, ImportError, AttributeError, KeyError, TypeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
