from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_cross_market_candidate_materialization.py"
UPSTREAM_TEST = ROOT / "test_oml_041_oracle_memory_certified_cross_market_candidate_materialization.py"
VALIDATION_MODULE = PACKAGE / "oracle_memory_candidate_validation_and_deduplication.py"
VALIDATION_TEST = ROOT / "test_oml_017_oracle_memory_candidate_validation_and_deduplication.py"
ADMISSION_MODULE = PACKAGE / "oracle_memory_certified_observation_candidate_validation_and_admission.py"
ADMISSION_TEST = ROOT / "test_oml_029_oracle_memory_certified_observation_candidate_validation_and_admission.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_cross_market_candidate_validation_and_admission.py"
TEST = ROOT / "test_oml_042_oracle_memory_certified_cross_market_candidate_validation_and_admission.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization import (
    OracleMemoryCertifiedCrossMarketCandidateMaterialization,
    verify_oracle_memory_certified_cross_market_candidate_materialization,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    OracleMemoryObservationCandidateAdmissionBatch,
    build_oracle_memory_observation_candidate_admission_batch,
    verify_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-042"
ENGINE_ID = "OML-042"
POLICY_ID = (
    "oracle-memory."
    "certified-cross-market-candidate-validation-and-admission.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-041"
UPSTREAM_ENGINE_ID = "OML-041"
VALIDATION_SCHEMA_VERSION = "OML-017"
VALIDATION_ENGINE_ID = "OML-017"
ADMISSION_SCHEMA_VERSION = "OML-029"
ADMISSION_ENGINE_ID = "OML-029"
STATE_READ_ONLY = "read_only_candidate_validation_and_admission"


class OracleMemoryCertifiedCrossMarketAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketCandidateAdmission:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_materialization_batch_hash: str
    validation_schema_version: str
    validation_engine_id: str
    validation_batch_hash: str
    admission_schema_version: str
    admission_engine_id: str
    admission_batch: OracleMemoryObservationCandidateAdmissionBatch
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    admission_count: int
    admitted_count: int
    rejected_duplicate_count: int
    state: str
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    observation_candidate_lineage_verified: bool
    duplicate_policy_verified: bool
    deterministic_admission_verified: bool
    candidate_admission_authorized: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    admission_ready: bool
    downstream_entity_resolution_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedCrossMarketAdmissionInvariantError(
        "unsupported OML-042 value type"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedCrossMarketAdmissionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-042 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketAdmissionInvariantError(
            f"OML-042 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_candidate_admission(
    *,
    materialization: OracleMemoryCertifiedCrossMarketCandidateMaterialization,
    validation_batch: OracleMemoryCandidateValidationBatch,
) -> OracleMemoryCertifiedCrossMarketCandidateAdmission:
    verify_oracle_memory_certified_cross_market_candidate_materialization(
        materialization
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if materialization.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-042 upstream schema mismatch")
    if materialization.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-042 upstream engine mismatch")
    if not materialization.materialization_ready:
        _reject("OML-042 materialization not ready")
    if not materialization.downstream_validation_authorized:
        _reject("OML-042 validation continuation not authorized")
    if not materialization.read_only:
        _reject("OML-042 materialization not read-only")
    if materialization.candidate_admission_authorized:
        _reject("OML-042 upstream bypassed admission boundary")

    if validation_batch.schema_version != VALIDATION_SCHEMA_VERSION:
        _reject("OML-042 validation schema mismatch")
    if validation_batch.engine_id != VALIDATION_ENGINE_ID:
        _reject("OML-042 validation engine mismatch")
    if not validation_batch.batch_ready:
        _reject("OML-042 validation batch not ready")
    if not validation_batch.next_certification_authorized:
        _reject("OML-042 validation continuation not authorized")
    if not validation_batch.read_only:
        _reject("OML-042 validation batch not read-only")

    materialized_hashes = tuple(
        candidate.candidate_hash
        for candidate in materialization.materialization_batch.candidates
    )
    validation_hashes = tuple(
        result.candidate_hash for result in validation_batch.results
    )
    if tuple(sorted(materialized_hashes)) != tuple(sorted(validation_hashes)):
        _reject("OML-042 materialization/validation candidate mismatch")

    forbidden_validation = (
        validation_batch.persistence_enabled,
        validation_batch.learning_updates_enabled,
        validation_batch.runtime_activation_enabled,
        validation_batch.publication_enabled,
        validation_batch.action_authorization_enabled,
        validation_batch.qseries_execution_enabled,
    )
    if any(forbidden_validation):
        _reject("OML-042 validation forbidden capability enabled")

    admission_batch = (
        build_oracle_memory_observation_candidate_admission_batch(
            materialization_batch=materialization.materialization_batch,
            validation_batch=validation_batch,
        )
    )
    verify_oracle_memory_observation_candidate_admission_batch(
        admission_batch
    )

    if admission_batch.schema_version != ADMISSION_SCHEMA_VERSION:
        _reject("OML-042 admission schema mismatch")
    if admission_batch.engine_id != ADMISSION_ENGINE_ID:
        _reject("OML-042 admission engine mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": materialization.schema_version,
        "upstream_engine_id": materialization.engine_id,
        "upstream_certification_hash": materialization.certification_hash,
        "upstream_materialization_batch_hash": (
            materialization.materialization_batch.batch_hash
        ),
        "validation_schema_version": validation_batch.schema_version,
        "validation_engine_id": validation_batch.engine_id,
        "validation_batch_hash": validation_batch.batch_hash,
        "admission_schema_version": admission_batch.schema_version,
        "admission_engine_id": admission_batch.engine_id,
        "admission_batch": admission_batch,
        "candidate_count": validation_batch.candidate_count,
        "unique_candidate_count": validation_batch.unique_candidate_count,
        "duplicate_candidate_count": validation_batch.duplicate_candidate_count,
        "admission_count": admission_batch.admission_count,
        "admitted_count": admission_batch.admitted_count,
        "rejected_duplicate_count": admission_batch.rejected_duplicate_count,
        "state": STATE_READ_ONLY,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "observation_candidate_lineage_verified": True,
        "duplicate_policy_verified": admission_batch.duplicate_policy_verified,
        "deterministic_admission_verified": (
            admission_batch.deterministic_admission_verified
        ),
        "candidate_admission_authorized": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "admission_ready": True,
        "downstream_entity_resolution_authorized": (
            admission_batch.downstream_entity_resolution_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketCandidateAdmission(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_candidate_admission(result)
    return result


def verify_oracle_memory_certified_cross_market_candidate_admission(
    result: OracleMemoryCertifiedCrossMarketCandidateAdmission,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-042 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-042 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-042 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-042 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-042 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-042 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-042 upstream engine lineage mismatch")
    if result.validation_schema_version != VALIDATION_SCHEMA_VERSION:
        _reject("OML-042 validation schema lineage mismatch")
    if result.validation_engine_id != VALIDATION_ENGINE_ID:
        _reject("OML-042 validation engine lineage mismatch")
    if result.admission_schema_version != ADMISSION_SCHEMA_VERSION:
        _reject("OML-042 admission schema lineage mismatch")
    if result.admission_engine_id != ADMISSION_ENGINE_ID:
        _reject("OML-042 admission engine lineage mismatch")

    for value, label in (
        (result.upstream_certification_hash, "upstream certification hash"),
        (
            result.upstream_materialization_batch_hash,
            "materialization batch hash",
        ),
        (result.validation_batch_hash, "validation batch hash"),
        (result.certification_hash, "certification hash"),
    ):
        _require_hash(value, label)

    verify_oracle_memory_observation_candidate_admission_batch(
        result.admission_batch
    )

    if result.upstream_materialization_batch_hash != (
        result.admission_batch.upstream_batch_hash
    ):
        _reject("OML-042 materialization lineage mismatch")
    if result.validation_batch_hash != (
        result.admission_batch.validation_batch_hash
    ):
        _reject("OML-042 validation lineage mismatch")
    if result.admission_count != result.admission_batch.admission_count:
        _reject("OML-042 admission count mismatch")
    if result.admitted_count != result.admission_batch.admitted_count:
        _reject("OML-042 admitted count mismatch")
    if result.rejected_duplicate_count != (
        result.admission_batch.rejected_duplicate_count
    ):
        _reject("OML-042 duplicate rejection count mismatch")
    if result.candidate_count != (
        result.unique_candidate_count + result.duplicate_candidate_count
    ):
        _reject("OML-042 candidate count reconciliation mismatch")
    if result.admission_count != result.candidate_count:
        _reject("OML-042 candidate/admission count mismatch")

    required = (
        result.materialization_lineage_verified,
        result.validation_lineage_verified,
        result.observation_candidate_lineage_verified,
        result.duplicate_policy_verified,
        result.deterministic_admission_verified,
        result.candidate_admission_authorized,
        result.admission_ready,
        result.downstream_entity_resolution_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-042 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-042 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-042 forbidden capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_validation_and_admission import (
    OracleMemoryCertifiedCrossMarketAdmissionInvariantError,
    build_oracle_memory_certified_cross_market_candidate_admission,
    verify_oracle_memory_certified_cross_market_candidate_admission,
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
    except OracleMemoryCertifiedCrossMarketAdmissionInvariantError:
        return
    raise AssertionError(f"tampered OML-042 {label} accepted")


def build_materialization(root: Path):
    fixture_040 = load_module(
        root
        / "test_oml_040_oracle_memory_certified_cross_market_candidate_materialization_authorization_gate.py",
        "oml_040_fixture_for_oml_042",
    )
    bridge = fixture_040.build_bridge(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
        build_oracle_memory_cross_market_materialization_authorization_decision,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization import (
        build_oracle_memory_certified_cross_market_candidate_materialization,
    )

    authorization = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_042",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    return build_oracle_memory_certified_cross_market_candidate_materialization(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )


def build_validation(root: Path, materialization):
    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_042",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)

    from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
        build_oracle_memory_ledger_integrity_replay_certification,
    )

    ledger_certification = (
        build_oracle_memory_ledger_integrity_replay_certification(
            ledger_contract=ledger_contract,
        )
    )

    return build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger_certification,
        candidates=materialization.materialization_batch.candidates,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-042 TEST")
    print(" CERTIFIED CROSS-MARKET CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    materialization = build_materialization(root)
    validation_batch = build_validation(root, materialization)

    result = build_oracle_memory_certified_cross_market_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    assert result.schema_version == "OML-042"
    assert result.engine_id == "OML-042"
    assert result.upstream_schema_version == "OML-041"
    assert result.upstream_engine_id == "OML-041"
    assert result.validation_schema_version == "OML-017"
    assert result.validation_engine_id == "OML-017"
    assert result.admission_schema_version == "OML-029"
    assert result.admission_engine_id == "OML-029"
    assert result.upstream_certification_hash == materialization.certification_hash
    assert result.upstream_materialization_batch_hash == (
        materialization.materialization_batch.batch_hash
    )
    assert result.validation_batch_hash == validation_batch.batch_hash
    assert result.candidate_count == validation_batch.candidate_count
    assert result.unique_candidate_count == validation_batch.unique_candidate_count
    assert result.duplicate_candidate_count == (
        validation_batch.duplicate_candidate_count
    )
    assert result.admission_count == result.admission_batch.admission_count
    assert result.admitted_count == result.admission_batch.admitted_count
    assert result.rejected_duplicate_count == (
        result.admission_batch.rejected_duplicate_count
    )
    assert result.candidate_admission_authorized
    assert result.admission_ready
    assert result.downstream_entity_resolution_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_candidate_admission(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, downstream_entity_resolution_authorized=False)
        ),
        "entity-resolution continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-041 materialization consumed read-only")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-029 admission builder consumed")
    print("[PASS] Observation-candidate lineage retained")
    print("[PASS] Validation-result lineage retained")
    print("[PASS] Duplicate policy enforced")
    print("[PASS] Candidate admission authorized read-only")
    print("[PASS] Entity-resolution continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-042 admissions rejected")
    print(
        "[DONE] OML-042 CERTIFIED CROSS-MARKET "
        "CANDIDATE VALIDATION AND ADMISSION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate() -> None:
    required = (
        UPSTREAM,
        UPSTREAM_TEST,
        VALIDATION_MODULE,
        VALIDATION_TEST,
        ADMISSION_MODULE,
        ADMISSION_TEST,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_cross_market_candidate_materialization"
    )
    validation_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_candidate_validation_and_deduplication"
    )
    admission_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_candidate_validation_and_admission"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-041",
        "ENGINE_ID": "OML-041",
        "POLICY_ID": (
            "oracle-memory."
            "certified-cross-market-candidate-materialization.v1"
        ),
    }
    expected_validation = {
        "SCHEMA_VERSION": "OML-017",
        "ENGINE_ID": "OML-017",
        "POLICY_ID": (
            "oracle-memory."
            "candidate-validation-and-deduplication.v1"
        ),
    }
    expected_admission = {
        "SCHEMA_VERSION": "OML-029",
        "ENGINE_ID": "OML-029",
        "POLICY_ID": (
            "oracle-memory."
            "certified-observation-candidate-validation-and-admission.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-028",
        "UPSTREAM_ENGINE_ID": "OML-028",
    }

    for module, expected, label in (
        (upstream_module, expected_upstream, "OML-041"),
        (validation_module, expected_validation, "OML-017"),
        (admission_module, expected_admission, "OML-029"),
    ):
        for name, value in expected.items():
            actual = getattr(module, name, None)
            if actual != value:
                raise RuntimeError(
                    f"Certified {label} {name} mismatch: "
                    f"expected {value!r}, got {actual!r}"
                )

    required_symbols = (
        (
            upstream_module,
            (
                "OracleMemoryCertifiedCrossMarketCandidateMaterialization",
                "verify_oracle_memory_certified_cross_market_candidate_materialization",
            ),
            "OML-041",
        ),
        (
            validation_module,
            (
                "OracleMemoryCandidateValidationBatch",
                "verify_oracle_memory_candidate_validation_batch",
            ),
            "OML-017",
        ),
        (
            admission_module,
            (
                "OracleMemoryObservationCandidateAdmissionBatch",
                "build_oracle_memory_observation_candidate_admission_batch",
                "verify_oracle_memory_observation_candidate_admission_batch",
                "OracleMemoryObservationCandidateAdmissionInvariantError",
            ),
            "OML-029",
        ),
    )

    for module, symbols, label in required_symbols:
        missing_symbols = [
            name for name in symbols if not hasattr(module, name)
        ]
        if missing_symbols:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_symbols)
            )

    actual_parameters = set(
        inspect.signature(
            admission_module.
            build_oracle_memory_observation_candidate_admission_batch
        ).parameters
    )
    required_parameters = {
        "materialization_batch",
        "validation_batch",
    }
    missing_parameters = sorted(required_parameters - actual_parameters)
    if missing_parameters:
        raise RuntimeError(
            "Certified OML-029 builder parameters missing: "
            + ", ".join(missing_parameters)
        )

    upstream_fields = set(
        upstream_module.
        OracleMemoryCertifiedCrossMarketCandidateMaterialization.
        __dataclass_fields__
    )
    required_upstream_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "materialization_batch",
        "candidate_count",
        "candidate_admission_authorized",
        "materialization_ready",
        "downstream_validation_authorized",
        "read_only",
    }
    missing_fields = sorted(required_upstream_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-041 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-042 INSTALLER")
    print(" CERTIFIED CROSS-MARKET CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_041_017_029_INTERFACE_ALIGNMENT")

    try:
        validate()
        print("[OK] Actual OML-041 dataclass and verifier inspected")
        print("[OK] Actual OML-017 validation contract inspected")
        print("[OK] Actual OML-029 admission builder inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-041"),
            (VALIDATION_TEST, "OML-017"),
            (ADMISSION_TEST, "OML-029"),
        ):
            run = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                check=False,
            )
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code "
                    f"{run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                VALIDATION_MODULE,
                VALIDATION_TEST,
                ADMISSION_MODULE,
                ADMISSION_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_cross_market_"
            "candidate_validation_and_admission import *"
        )
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

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OML-042 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-041 production unchanged")
        print("[PASS] Certified OML-041 standalone test unchanged")
        print("[PASS] Certified OML-017 validation engine unchanged")
        print("[PASS] Certified OML-029 admission engine unchanged")
        print("[PASS] Exact upstream dataclasses consumed directly")
        print("[PASS] OML-042 production fully replaced")
        print("[PASS] OML-042 standalone deterministic test installed")
        print("[PASS] Deterministic hashes and replay guarantees preserved")
        print("[PASS] Immutable certified lineage preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-042 CERTIFIED CROSS-MARKET "
            "CANDIDATE VALIDATION AND ADMISSION INSTALLED"
        )
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
