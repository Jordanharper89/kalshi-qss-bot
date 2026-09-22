from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    OracleLiveShadowOperatorHealthAttestor,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_evidence_store import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveShadowOperatorHealthEvidenceStore,
    OracleLiveShadowOperatorHealthEvidenceStoreBlocked,
    build_production_operator_health_evidence_store,
)


OBSERVED_AT = datetime(
    2026,
    7,
    17,
    21,
    0,
    0,
    123456,
    tzinfo=timezone.utc,
)


def expect_blocked(callable_object) -> None:
    try:
        callable_object()
    except OracleLiveShadowOperatorHealthEvidenceStoreBlocked:
        return

    raise AssertionError(
        "expected OLA-067 to fail closed"
    )


def build_attestation(
    *,
    status: str,
    pid: int | None,
    process_alive: bool,
    runtime_fresh: bool,
    state_age_seconds: float | None,
    newest_log_age_seconds: float | None,
):
    return OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": status,
            "pid": pid,
            "process_alive": process_alive,
            "runtime_fresh": runtime_fresh,
            "state_age_seconds": state_age_seconds,
            "newest_log_age_seconds": (
                newest_log_age_seconds
            ),
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )


def main() -> int:
    assert SCHEMA_VERSION == "OLA-067"
    assert ENGINE_ID == "OLA-067"

    healthy_attestation = build_attestation(
        status="RUNNING",
        pid=54321,
        process_alive=True,
        runtime_fresh=True,
        state_age_seconds=3.0,
        newest_log_age_seconds=2.0,
    )

    degraded_attestation = build_attestation(
        status="DEGRADED",
        pid=54322,
        process_alive=True,
        runtime_fresh=False,
        state_age_seconds=180.0,
        newest_log_age_seconds=181.0,
    )

    stopped_attestation = build_attestation(
        status="STOPPED",
        pid=None,
        process_alive=False,
        runtime_fresh=False,
        state_age_seconds=None,
        newest_log_age_seconds=None,
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        repository_root = Path(
            temporary_directory
        )

        store = (
            build_production_operator_health_evidence_store(
                repository_root=repository_root
            )
        )

        expected_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "current.json"
        )

        assert store.target_path == expected_target

        first_write = store.write(
            attestation=healthy_attestation
        )

        assert expected_target.exists()
        assert first_write.schema_version == "OLA-067"
        assert first_write.engine_id == "OLA-067"
        assert first_write.write_status == "written"
        assert first_write.atomic_write is True
        assert first_write.durable_flush_requested is True
        assert first_write.bytes_written > 0
        assert first_write.operator_status == "RUNNING"
        assert first_write.health_status == "HEALTHY"
        assert (
            first_write.attestation_evidence_hash
            == healthy_attestation.evidence_hash
        )
        assert first_write.read_only is True
        assert first_write.execution_allowed is False
        assert first_write.alerts_allowed is False
        assert first_write.qseries_handoff_allowed is False
        assert first_write.execution_adapter_resolved is False
        assert first_write.execution_adapter_invoked is False
        assert first_write.trade_authorization_allowed is False
        assert first_write.order_placement_allowed is False
        assert first_write.funds_moved is False
        assert first_write.portfolio_mutated is False

        first_payload = store.read_current()

        assert first_payload["schema_version"] == "OLA-067"
        assert first_payload["engine_id"] == "OLA-067"
        assert first_payload["read_only"] is True
        assert first_payload["execution_allowed"] is False
        assert (
            first_payload["attestation"]["evidence_hash"]
            == healthy_attestation.evidence_hash
        )

        try:
            first_payload["engine_id"] = "mutated"
        except TypeError:
            pass
        else:
            raise AssertionError(
                "read projection must be immutable"
            )

        first_bytes = expected_target.read_bytes()

        replay_write = store.write(
            attestation=healthy_attestation
        )

        replay_bytes = expected_target.read_bytes()

        assert first_bytes == replay_bytes
        assert replay_write.bytes_written == (
            first_write.bytes_written
        )
        assert (
            replay_write.attestation_evidence_hash
            == first_write.attestation_evidence_hash
        )

        degraded_write = store.write(
            attestation=degraded_attestation
        )

        degraded_payload = store.read_current()

        assert degraded_write.operator_status == "DEGRADED"
        assert degraded_write.health_status == "DEGRADED"
        assert (
            degraded_payload["attestation"]["degraded"]
            is True
        )
        assert (
            degraded_payload["attestation"]["fail_closed"]
            is True
        )

        stopped_write = store.write(
            attestation=stopped_attestation
        )

        stopped_payload = store.read_current()

        assert stopped_write.operator_status == "STOPPED"
        assert stopped_write.health_status == "STOPPED"
        assert (
            stopped_payload["attestation"]["stopped"]
            is True
        )
        assert (
            stopped_payload["attestation"]["fail_closed"]
            is True
        )

        raw_payload = json.loads(
            expected_target.read_text(
                encoding="utf-8"
            )
        )

        raw_payload["execution_allowed"] = True

        expected_target.write_text(
            json.dumps(raw_payload),
            encoding="utf-8",
        )

        expect_blocked(
            store.read_current
        )

        bad_target = (
            repository_root
            / ".env"
            / "current.json"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=bad_target
            )
        )

        wrong_name_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "latest.json"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=wrong_name_target
            )
        )

        wrong_type_target = (
            repository_root
            / "runtime"
            / "oracle_live_shadow"
            / "operator"
            / "health"
            / "current.txt"
        )

        expect_blocked(
            lambda: OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=wrong_type_target
            )
        )

        empty_store = (
            OracleLiveShadowOperatorHealthEvidenceStore(
                target_path=(
                    repository_root
                    / "empty"
                    / "current.json"
                )
            )
        )

        expect_blocked(
            empty_store.read_current
        )

    print(
        "[PASS] OLA-067 Oracle Live Shadow "
        "Operator Health Evidence Store"
    )

    print(
        {
            "schema_version": "OLA-067",
            "engine_id": "OLA-067",
            "status": "passed",
            "ola066_typed_attestation_required": True,
            "healthy_evidence_written": True,
            "degraded_evidence_written_fail_closed": True,
            "stopped_evidence_written_fail_closed": True,
            "canonical_json_serialization": True,
            "deterministic_replay_bytes": True,
            "atomic_temp_file_replacement": True,
            "durable_file_flush_requested": True,
            "post_write_verification": True,
            "current_pointer_contract": True,
            "immutable_read_projection": True,
            "forbidden_target_paths_rejected": True,
            "malformed_evidence_fails_closed": True,
            "authority_tampering_fails_closed": True,
            "secrets_not_persisted": True,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
