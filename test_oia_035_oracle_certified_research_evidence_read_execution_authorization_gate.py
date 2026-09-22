from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ENTRY_READY,
    EVIDENCE_READ_EXECUTION_READY,
    EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
    stable_hash as readiness_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_authorization_gate import (
    EVIDENCE_READ_EXECUTION_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED,
    CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate,
    stable_hash,
)

H = [f"{i:064x}" for i in range(1, 40)]


def seed(directory: Path) -> dict:
    entry_body = {
        "readiness_sequence": 1,
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "evidence_scope_id": "scope.test",
        "authorized_read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "readiness_status": EVIDENCE_READ_EXECUTION_ENTRY_READY,
        "source_evidence_read_request_hash": H[1],
        "source_active_evidence_read_request_hash": H[2],
    }
    entry = dict(entry_body)
    entry["readiness_entry_hash"] = readiness_hash(entry_body)

    body = {
        "schema_version": "OIA-034",
        "engine_id": "OIA-034",
        "evaluated_at": "2026-07-21T16:00:00+00:00",
        "evidence_read_execution_readiness_id": "oia034-test",
        "readiness_status": EVIDENCE_READ_EXECUTION_READY,
        "worker_id": "oracle-worker-test",
        "source_evidence_read_request_activation_id": "oia033-test",
        "source_evidence_read_request_manifest_id": "oia032-test",
        "source_evidence_task_activation_id": "oia031-test",
        "source_evidence_task_manifest_id": "oia030-test",
        "source_evidence_batch_activation_id": "oia029-test",
        "source_evidence_batch_id": "oia028-test",
        "source_evidence_session_id": "oia027-test",
        "source_evidence_manifest_id": "oia026-test",
        "source_certification_id": "oia025-test",
        "source_readiness_id": "oia024-test",
        "source_session_id": "oia023-test",
        "source_activation_id": "oia022-test",
        "source_claim_id": "oia021-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "readiness_entry_count": 1,
        "evidence_read_request_activation_policy_id": "oia033-policy",
        "evidence_read_execution_readiness_policy_id":
            EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
        "entries": [entry],
        "source_evidence_read_request_activation_hash": H[3],
        "source_evidence_read_request_manifest_hash": H[4],
        "source_evidence_task_activation_hash": H[5],
        "source_evidence_task_manifest_hash": H[6],
        "source_evidence_batch_activation_hash": H[7],
        "source_evidence_batch_hash": H[8],
        "source_evidence_session_hash": H[9],
        "source_evidence_manifest_hash": H[10],
        "source_certification_hash": H[11],
        "source_readiness_hash": H[12],
        "source_session_hash": H[13],
        "source_activation_hash": H[14],
        "source_claim_hash": H[15],
        "source_dispatch_manifest_hash": H[16],
        "source_batch_hash": H[17],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
        "research_execution_allowed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "readiness_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_readiness_hash"] = readiness_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-035 TEST")
    print(" EVIDENCE READ EXECUTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 21, 17, 0, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-035"
        assert first.engine_id == "OIA-035"
        assert first.authorization_status == EVIDENCE_READ_EXECUTION_AUTHORIZED
        assert first.authorization_entry_count == 1
        assert first.entries[0].authorization_status == (
            EVIDENCE_READ_EXECUTION_ENTRY_AUTHORIZED
        )
        assert first.source_evidence_read_execution_readiness_hash == (
            source["evidence_read_execution_readiness_hash"]
        )
        assert first.entries[0].source_readiness_entry_hash == (
            source["entries"][0]["readiness_entry_hash"]
        )
        assert all(op.startswith("read_") for op in first.entries[0].authorized_read_operations)
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_authorization_allowed is True

        for value in (
            first.research_execution_allowed,
            first.analytic_conclusion_allowed,
            first.forecast_creation_allowed,
            first.signals_allowed,
            first.alerts_allowed,
            first.qseries_handoff_allowed,
            first.execution_allowed,
            first.trading_recommendations_allowed,
            first.source_mutation_allowed,
            first.market_order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        ):
            assert value is False

        body = dict(first.to_dict())
        result_hash = body.pop("evidence_read_execution_authorization_hash")
        assert result_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("authorization_entry_hash")
        assert entry_hash == stable_hash(entry_body)

        assert (authorization / "current.json").exists()
        assert list((authorization / "authorizations").glob("*.json"))
        assert list((authorization / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        tampered["entries"][0]["authorized_read_operations"].append("create_order")
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.authorize(authorized_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-034 readiness accepted.")

    print("[PASS] Actual OIA-034 read-execution readiness contract consumed")
    print("[PASS] Authorization and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-034 lineage preserved")
    print("[PASS] Only bounded read-prefixed operations authorized")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered read-execution readiness rejected")
    print("[PASS] Atomic authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
