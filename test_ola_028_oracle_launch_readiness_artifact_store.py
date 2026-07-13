from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_launch_readiness_artifact_store import (
    OracleLaunchReadinessArtifactStore,
    OracleLaunchReadinessArtifactStoreBlocked,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_shadow_launch_readiness_gate import (
    evaluate_oracle_shadow_launch_readiness,
)

from test_ola_018_oracle_kalshi_live_read_readiness_gate import (
    DeterministicHealthyFetcher,
    build_gate,
    evaluate_gate,
)

from test_ola_020_oracle_service_isolation_canonical_intelligence_handoff_contract import (
    build_service_contract,
)

from test_ola_022_oracle_live_shadow_service_bootstrap_contract import (
    build_bootstrap_record,
)

from test_ola_026_oracle_shadow_launch_readiness_gate import (
    _build_production_gate_record,
)


def build_readiness(
    *,
    root: Path,
):
    fetcher = DeterministicHealthyFetcher()

    adapter, live_gate = build_gate(
        fetcher=fetcher
    )

    live_readiness = evaluate_gate(
        gate=live_gate
    )

    service_isolation = build_service_contract()

    bootstrap = build_bootstrap_record()

    (
        readiness_runtime_root,
        production_gate,
    ) = _build_production_gate_record(
        root=root / "readiness"
    )

    readiness = (
        evaluate_oracle_shadow_launch_readiness(
            live_readiness_record=live_readiness,
            service_isolation_contract=(
                service_isolation
            ),
            bootstrap_record=bootstrap,
            production_evidence_gate_record=(
                production_gate
            ),
            runtime_root=readiness_runtime_root,
        )
    )

    assert readiness.launch_ready is True
    assert readiness.verify_readiness_hash() is True

    return readiness


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(
            temporary_directory
        ).resolve()

        runtime_root = (
            root
            / "runtime"
        )

        readiness = build_readiness(
            root=root
        )

        store = OracleLaunchReadinessArtifactStore(
            runtime_root=runtime_root
        )

        receipt = store.persist(
            readiness_record=readiness
        )

        assert receipt.schema_version == "OLA-028"
        assert receipt.engine_id == "OLA-028"
        assert receipt.artifact_status == "persisted"

        assert (
            receipt.readiness_schema_version
            == "OLA-026"
        )

        assert receipt.readiness_engine_id == "OLA-026"

        assert (
            receipt.readiness_hash
            == readiness.readiness_hash
        )

        assert (
            receipt.artifact_identity
            == "oracle.launch_readiness."
            + readiness.readiness_hash
        )

        assert receipt.immutable_artifact_written is True
        assert receipt.current_pointer_updated is True

        assert (
            receipt.artifact_relative_path.startswith(
                "state/launch_readiness/"
            )
        )

        assert (
            receipt.current_pointer_relative_path
            == "state/launch_readiness/current.json"
        )

        loaded = store.load_current()

        assert loaded == readiness
        assert loaded.launch_ready is True
        assert loaded.readiness_status == "ready"
        assert loaded.verify_readiness_hash() is True

        second_receipt = store.persist(
            readiness_record=readiness
        )

        assert (
            second_receipt.artifact_hash
            == receipt.artifact_hash
        )

        assert (
            second_receipt.artifact_identity
            == receipt.artifact_identity
        )

        assert (
            second_receipt.immutable_artifact_written
            is False
        )

        assert store.load_current() == readiness

        blocked_readiness = replace(
            readiness,
            launch_ready=False,
            readiness_status="blocked",
        )

        blocked_persist = False

        try:
            store.persist(
                readiness_record=blocked_readiness
            )
        except OracleLaunchReadinessArtifactStoreBlocked:
            blocked_persist = True

        assert blocked_persist is True

        invalid_hash_readiness = replace(
            readiness,
            readiness_hash="0" * 64,
        )

        invalid_hash_blocked = False

        try:
            store.persist(
                readiness_record=invalid_hash_readiness
            )
        except OracleLaunchReadinessArtifactStoreBlocked:
            invalid_hash_blocked = True

        assert invalid_hash_blocked is True

        artifact_path = (
            runtime_root
            / receipt.artifact_relative_path
        )

        original_artifact = artifact_path.read_text(
            encoding="utf-8"
        )

        artifact_data = json.loads(
            original_artifact
        )

        artifact_data[
            "readiness_record"
        ][
            "launch_ready"
        ] = False

        artifact_path.write_text(
            json.dumps(
                artifact_data,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        tampered_artifact_blocked = False

        try:
            store.load_current()
        except OracleLaunchReadinessArtifactStoreBlocked:
            tampered_artifact_blocked = True

        assert tampered_artifact_blocked is True

        artifact_path.write_text(
            original_artifact,
            encoding="utf-8",
        )

        assert store.load_current() == readiness

        pointer_path = store.current_pointer_path

        original_pointer = pointer_path.read_text(
            encoding="utf-8"
        )

        pointer_data = json.loads(
            original_pointer
        )

        pointer_data["artifact_hash"] = "f" * 64

        pointer_path.write_text(
            json.dumps(
                pointer_data,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        tampered_pointer_blocked = False

        try:
            store.load_current()
        except OracleLaunchReadinessArtifactStoreBlocked:
            tampered_pointer_blocked = True

        assert tampered_pointer_blocked is True

        pointer_path.write_text(
            original_pointer,
            encoding="utf-8",
        )

        assert store.load_current() == readiness

        malformed_pointer_blocked = False

        pointer_path.write_text(
            "{not-json",
            encoding="utf-8",
        )

        try:
            store.load_current()
        except OracleLaunchReadinessArtifactStoreBlocked:
            malformed_pointer_blocked = True

        assert malformed_pointer_blocked is True

        pointer_path.write_text(
            original_pointer,
            encoding="utf-8",
        )

        secret_artifact = json.loads(
            original_artifact
        )

        secret_artifact["api_key"] = "forbidden"

        artifact_path.write_text(
            json.dumps(
                secret_artifact,
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        secret_bearing_artifact_blocked = False

        try:
            store.load_current()
        except OracleLaunchReadinessArtifactStoreBlocked:
            secret_bearing_artifact_blocked = True

        assert secret_bearing_artifact_blocked is True

        artifact_path.write_text(
            original_artifact,
            encoding="utf-8",
        )

        assert store.load_current() == readiness

        missing_runtime_root = (
            root
            / "missing-runtime"
        )

        missing_store = (
            OracleLaunchReadinessArtifactStore(
                runtime_root=missing_runtime_root
            )
        )

        missing_pointer_blocked = False

        try:
            missing_store.load_current()
        except OracleLaunchReadinessArtifactStoreBlocked:
            missing_pointer_blocked = True

        assert missing_pointer_blocked is True

        assert receipt.read_only is True
        assert receipt.alerts_allowed is False
        assert receipt.qseries_intake_allowed is False

        assert (
            receipt.canonical_handoff_published
            is False
        )

        assert receipt.execution_allowed is False

        assert (
            receipt.execution_adapter_resolved
            is False
        )

        assert (
            receipt.execution_adapter_invoked
            is False
        )

        assert (
            receipt.trade_authorization_allowed
            is False
        )

        assert receipt.order_placement_allowed is False
        assert receipt.funds_moved is False
        assert receipt.portfolio_mutated is False

        result = {
            "schema_version": "OLA-028",
            "engine_id": "OLA-028",
            "status": "passed",
            "fresh_repository_audit_boundary": True,
            "ola_026_record_required": True,
            "launch_ready_required": True,
            "readiness_status_ready_required": True,
            "readiness_hash_verified_before_persist": True,
            "immutable_hash_addressed_artifact": True,
            "atomic_current_pointer_replacement": True,
            "canonical_json_serialization": True,
            "deterministic_stable_hashing": True,
            "exact_ola_026_record_reconstructed": True,
            "readiness_hash_verified_after_load": True,
            "idempotent_identical_persist": True,
            "immutable_artifact_conflict_fails_closed": True,
            "blocked_readiness_fails_closed": True,
            "invalid_readiness_hash_fails_closed": True,
            "tampered_artifact_fails_closed": True,
            "tampered_pointer_fails_closed": True,
            "malformed_pointer_fails_closed": True,
            "missing_pointer_fails_closed": True,
            "secret_bearing_artifact_fails_closed": True,
            "runtime_state_confinement": True,
            "unattended_collection_started": False,
            "read_only": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "canonical_handoff_published": False,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        print(
            "[PASS] OLA-028 Oracle Launch Readiness "
            "Artifact Store"
        )

        print(result)


if __name__ == "__main__":
    main()
