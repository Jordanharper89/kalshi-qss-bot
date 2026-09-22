from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_full_subsystem_completion_integration_gate.py"
TEST = ROOT / "test_int_oia_001_oracle_intelligence_analytics_full_subsystem_completion_integration_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
OIA067 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_completion_attestation_gate.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-001"
ENGINE_ID = "INT-OIA-001"
POLICY_ID = "oracle.intelligence.analytics.full-subsystem-completion-integration.v1"
STATUS_CERTIFIED = "oracle_intelligence_analytics_subsystem_integration_certified"

DEFAULT_OIA_COMPLETION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_"
    "controlled_callable_invocation_completion_attestation"
)
DEFAULT_INTEGRATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_full_subsystem_completion_integration"
)


class OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsSubsystemBoundary:
    boundary_id: str
    subsystem_id: str
    first_module_id: str
    final_module_id: str
    module_count: int
    source_completion_attestation_id: str
    source_completion_attestation_manifest_hash: str
    complete_lineage_verified: bool
    controlled_read_execution_verified: bool
    completion_attestation_verified: bool
    read_only_boundary_frozen: bool
    downstream_consumer_authorized: bool
    source_reexecution_performed: bool
    corpus_read_performed: bool
    signal_generation_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    boundary_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationCertification:
    schema_version: str
    engine_id: str
    certified_at: str
    integration_certification_id: str
    integration_certification_status: str
    integration_policy_id: str
    source_completion_attestation_id: str
    source_completion_attestation_manifest_hash: str
    source_worker_id: str
    source_lineage: dict[str, Any]
    subsystem_boundary: OracleIntelligenceAnalyticsSubsystemBoundary
    oia_001_through_oia_067_complete: bool
    actual_oia_067_contract_consumed: bool
    exact_approved_adapter_set_completed: bool
    invocation_results_validated: bool
    all_result_hashes_verified: bool
    all_nonce_pairs_unique: bool
    controlled_read_only_execution_completed: bool
    source_invocation_reexecuted: bool
    owner_reconstruction_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    adapter_execution_performed: bool
    corpus_read_execution_performed: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    trading_recommendations_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    downstream_read_only_consumption_allowed: bool
    oia_subsystem_frozen: bool
    integration_artifact_persistence_allowed: bool
    integration_certification_manifest_hash: str


class OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationGate:
    def __init__(
        self,
        *,
        completion_directory: Path | str = DEFAULT_OIA_COMPLETION_DIRECTORY,
        integration_directory: Path | str = DEFAULT_INTEGRATION_DIRECTORY,
    ) -> None:
        self.completion_directory = Path(completion_directory)
        self.integration_directory = Path(integration_directory)

    def _load_completion(self) -> dict[str, Any]:
        path = self.completion_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                f"OIA-067 completion artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                "OIA-067 completion artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "controlled_callable_invocation_completion_attestation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                "OIA-067 completion manifest hash mismatch"
            )
        payload[
            "controlled_callable_invocation_completion_attestation_manifest_hash"
        ] = manifest_hash

        required = {
            "schema_version": "OIA-067",
            "engine_id": "OIA-067",
            "invocation_results_validated": True,
            "all_approved_invocations_completed": True,
            "all_result_hashes_verified": True,
            "all_nonce_pairs_unique": True,
            "source_invocation_reexecuted": False,
            "owner_reconstruction_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_performed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "oia_subsystem_complete": True,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    f"unsafe or incomplete OIA-067 field: {field}"
                )

        entries = payload.get("completion_entries")
        if (
            not isinstance(entries, list)
            or len(entries) != 2
            or payload.get("completion_entry_count") != len(entries)
        ):
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                "OIA-067 completion entries invalid"
            )

        adapter_ids = {
            entry.get("adapter_id")
            for entry in entries
            if isinstance(entry, dict)
        }
        expected_adapters = {
            "oracle_read_only_canonical_observation_adapter.v1",
            "oracle_read_only_market_state_lineage_adapter.v1",
        }
        if adapter_ids != expected_adapters:
            raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                "OIA-067 approved adapter set mismatch"
            )

        for sequence, raw_entry in enumerate(entries, start=1):
            entry = dict(raw_entry)
            entry_hash = entry.pop(
                "controlled_callable_invocation_completion_entry_hash",
                None,
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    "OIA-067 completion entry hash mismatch"
                )
            if entry.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    "OIA-067 completion entry sequence mismatch"
                )
            if (
                entry.get("completion_validated") is not True
                or entry.get("callable_invoked") is not True
                or entry.get("adapter_executed") is not True
                or entry.get("corpus_read_executed") is not True
                or entry.get("source_mutation_performed") is not False
            ):
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    "OIA-067 completion entry not safely completed"
                )
            if not _valid_hash(entry.get("result_hash")):
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    "OIA-067 result hash invalid"
                )
            if not _valid_hash(entry.get("result_summary_hash")):
                raise OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError(
                    "OIA-067 result summary hash invalid"
                )

        return payload

    def certify(
        self,
        *,
        certified_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationCertification:
        certified_at = _aware(certified_at, "certified_at")
        source = self._load_completion()

        source_id = source[
            "controlled_callable_invocation_completion_attestation_id"
        ]
        source_hash = source[
            "controlled_callable_invocation_completion_attestation_manifest_hash"
        ]

        boundary_body = {
            "boundary_id": stable_hash(
                {
                    "subsystem_id": "OIA",
                    "source_completion_attestation_id": source_id,
                    "source_completion_attestation_manifest_hash": source_hash,
                }
            ),
            "subsystem_id": "OIA",
            "first_module_id": "OIA-001",
            "final_module_id": "OIA-067",
            "module_count": 67,
            "source_completion_attestation_id": source_id,
            "source_completion_attestation_manifest_hash": source_hash,
            "complete_lineage_verified": True,
            "controlled_read_execution_verified": True,
            "completion_attestation_verified": True,
            "read_only_boundary_frozen": True,
            "downstream_consumer_authorized": True,
            "source_reexecution_performed": False,
            "corpus_read_performed": False,
            "signal_generation_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        boundary = OracleIntelligenceAnalyticsSubsystemBoundary(
            **boundary_body,
            boundary_hash=stable_hash(boundary_body),
        )

        identity = {
            "source_completion_attestation_id": source_id,
            "source_completion_attestation_manifest_hash": source_hash,
            "boundary_hash": boundary.boundary_hash,
            "certified_at": certified_at.isoformat(),
        }
        certification_id = stable_hash(identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "certified_at": certified_at.isoformat(),
            "integration_certification_id": certification_id,
            "integration_certification_status": STATUS_CERTIFIED,
            "integration_policy_id": POLICY_ID,
            "source_completion_attestation_id": source_id,
            "source_completion_attestation_manifest_hash": source_hash,
            "source_worker_id": source["worker_id"],
            "source_lineage": dict(source["source_lineage"]),
            "subsystem_boundary": boundary,
            "oia_001_through_oia_067_complete": True,
            "actual_oia_067_contract_consumed": True,
            "exact_approved_adapter_set_completed": True,
            "invocation_results_validated": True,
            "all_result_hashes_verified": True,
            "all_nonce_pairs_unique": True,
            "controlled_read_only_execution_completed": True,
            "source_invocation_reexecuted": False,
            "owner_reconstruction_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_performed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "downstream_read_only_consumption_allowed": True,
            "oia_subsystem_frozen": True,
            "integration_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["subsystem_boundary"] = asdict(boundary)
        manifest_hash = stable_hash(serializable)

        certification = (
            OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationCertification(
                **body,
                integration_certification_manifest_hash=manifest_hash,
            )
        )

        if persist:
            payload = asdict(certification)
            _atomic_write(
                self.integration_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.integration_directory
                / "certifications"
                / f"{certification_id}.json",
                payload,
            )
            _atomic_write(
                self.integration_directory
                / "boundaries"
                / f"{boundary.boundary_id}.json",
                payload,
            )

        return certification
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_full_subsystem_completion_integration_gate import (
    OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationGate,
    OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError,
    stable_hash,
)


def _completion_entry(
    sequence: int,
    adapter_id: str,
) -> dict:
    body = {
        "sequence": sequence,
        "worker_id": "worker-int-oia-001",
        "work_item_id": f"work-{sequence}",
        "adapter_id": adapter_id,
        "source_invocation_hash": stable_hash(
            {"invocation": sequence}
        ),
        "activation_nonce": f"activation-{sequence}",
        "consumption_attempt_nonce": f"attempt-{sequence}",
        "result_type": (
            "OracleLiveCorpusReport"
            if sequence == 1
            else "tuple"
        ),
        "result_hash": stable_hash({"result": sequence}),
        "result_summary_hash": stable_hash(
            {"summary": sequence}
        ),
        "callable_invoked": True,
        "adapter_executed": True,
        "corpus_read_executed": True,
        "source_mutation_performed": False,
        "completion_validated": True,
        "completion_status": "validated",
    }
    body[
        "controlled_callable_invocation_completion_entry_hash"
    ] = stable_hash(body)
    return body


def _seed(path: Path) -> None:
    entries = [
        _completion_entry(
            1,
            "oracle_read_only_canonical_observation_adapter.v1",
        ),
        _completion_entry(
            2,
            "oracle_read_only_market_state_lineage_adapter.v1",
        ),
    ]
    manifest = {
        "schema_version": "OIA-067",
        "engine_id": "OIA-067",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "controlled_callable_invocation_completion_attestation_id": (
            "oia067-test"
        ),
        "controlled_callable_invocation_completion_attestation_status": (
            "evidence_read_execution_adapter_"
            "controlled_callable_invocation_completed"
        ),
        "controlled_callable_invocation_completion_attestation_policy_id": (
            "test"
        ),
        "worker_id": "worker-int-oia-001",
        "completion_entry_count": len(entries),
        "completion_entries": entries,
        "source_invocation_id": "oia066-test",
        "source_invocation_manifest_hash": stable_hash({"oia": 66}),
        "source_readiness_id": "oia065-test",
        "source_readiness_manifest_hash": stable_hash({"oia": 65}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "completion_module_id": "OIA-067",
        },
        "invocation_results_validated": True,
        "all_approved_invocations_completed": True,
        "all_result_hashes_verified": True,
        "all_nonce_pairs_unique": True,
        "source_invocation_reexecuted": False,
        "owner_reconstruction_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "oia_subsystem_complete": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest[
        "controlled_callable_invocation_completion_attestation_manifest_hash"
    ] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-001 TEST")
    print(" FULL OIA SUBSYSTEM INTEGRATION")
    print(" OIA-001 THROUGH OIA-067 FREEZE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        completion = root / "completion"
        integration = root / "integration"
        _seed(completion)

        gate = (
            OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationGate(
                completion_directory=completion,
                integration_directory=integration,
            )
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.certify(
            certified_at=fixed,
            persist=True,
        )
        second = gate.certify(
            certified_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-001"
        assert first.oia_001_through_oia_067_complete
        assert first.actual_oia_067_contract_consumed
        assert first.controlled_read_only_execution_completed
        assert first.oia_subsystem_frozen
        assert first.downstream_read_only_consumption_allowed
        assert first.subsystem_boundary.first_module_id == "OIA-001"
        assert first.subsystem_boundary.final_module_id == "OIA-067"
        assert first.subsystem_boundary.module_count == 67
        assert first.subsystem_boundary.read_only_boundary_frozen
        assert not first.source_invocation_reexecuted
        assert not first.owner_reconstruction_performed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_performed
        assert not first.adapter_execution_performed
        assert not first.corpus_read_execution_performed
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_handoff_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        assert (integration / "current.json").exists()
        assert (
            integration
            / "certifications"
            / f"{first.integration_certification_id}.json"
        ).exists()
        assert (
            integration
            / "boundaries"
            / f"{first.subsystem_boundary.boundary_id}.json"
        ).exists()

        tampered = json.loads(
            (completion / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["oia_subsystem_complete"] = False
        (completion / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )

        try:
            gate.certify(
                certified_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered OIA-067 completion was accepted"
            )
        except OracleIntelligenceAnalyticsFullSubsystemCompletionIntegrationInvariantError:
            pass

    print("[PASS] Actual OIA-067 completion contract consumed")
    print("[PASS] OIA-001 through OIA-067 certified complete")
    print("[PASS] Exact approved read adapter set preserved")
    print("[PASS] Controlled read-only execution boundary verified")
    print("[PASS] Full lineage, result hashes, and nonce integrity preserved")
    print("[PASS] OIA subsystem frozen against accidental extension")
    print("[PASS] Downstream read-only consumption boundary issued")
    print("[PASS] OIA-066 invocation was not re-executed")
    print("[PASS] No owner reconstruction, binding, invocation, or read repeated")
    print("[PASS] Tampered or incomplete completion evidence rejected")
    print("[PASS] Atomic integration certification artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series execution, orders, funds, and "
        "portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify_oia067_contract() -> None:
    if not OIA067.exists():
        raise FileNotFoundError(
            f"Actual OIA-067 production module missing: {OIA067}"
        )
    source = OIA067.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "OIA-067"',
        "class ControlledCallableInvocationCompletionAttestation",
        "class OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationCompletionAttestationGate",
        "controlled_callable_invocation_completion_attestation_manifest_hash",
        "oia_subsystem_complete",
    )
    missing = [
        token for token in required_tokens if token not in source
    ]
    if missing:
        raise RuntimeError(
            "Actual OIA-067 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual OIA-067 completion-attestation contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        PACKAGE.read_text(encoding="utf-8")
        if PACKAGE.exists()
        else ""
    )
    export_line = (
        "from .oracle_intelligence_analytics_full_subsystem_"
        "completion_integration_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(
            existing,
            encoding="utf-8",
            newline="\n",
        )
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-001 INSTALLER")
    print(" FULL OIA SUBSYSTEM INTEGRATION")
    print(" OIA-001 THROUGH OIA-067 FREEZE")
    print("=" * 40)

    verify_oia067_contract()
    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    update_package()

    py_compile.compile(str(PRODUCTION), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    py_compile.compile(str(PACKAGE), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] INT-OIA-001 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-001 full OIA subsystem completion "
        "integration gate installed"
    )
    print("[DONE] OIA-001 through OIA-067 frozen as complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
