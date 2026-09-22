from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import ACTIVATION_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_manifest_builder import SESSION_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_readiness_gate import READINESS_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_certification_gate import (
    CERTIFICATION_POLICY_ID,
    SESSION_CERTIFIED,
    ENTRY_CERTIFIED,
    stable_hash as certification_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_manifest_builder import (
    EVIDENCE_MANIFEST_POLICY_ID,
    EVIDENCE_MANIFEST_ISSUED,
    EVIDENCE_ENTRY_AUTHORIZED,
    OracleCertifiedResearchEvidenceCollectionManifestBuilder,
    CertifiedResearchEvidenceCollectionManifestInvariantError,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 20)]


def write_certification(directory: Path) -> dict:
    entry_body = {
        "certification_sequence": 1,
        "readiness_sequence": 1,
        "session_sequence": 1,
        "activation_sequence": 1,
        "claim_sequence": 1,
        "dispatch_sequence": 1,
        "batch_number": 1,
        "batch_position": 1,
        "work_item_id": "work-item-test",
        "queue_position": 1,
        "source_rank": 1,
        "dimension": "market_microstructure",
        "key": "spread-compression",
        "tier": "A",
        "priority_score": "0.950000",
        "research_objective": "Collect canonical evidence for the certified research question.",
        "required_operations": ["read_canonical_observations"],
        "prohibited_operations": ["create_signal", "create_market_order"],
        "completion_requirements": ["preserve_lineage", "record_evidence_hashes"],
        "certification_status": ENTRY_CERTIFIED,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "readiness_policy_id": READINESS_POLICY_ID,
        "certification_policy_id": CERTIFICATION_POLICY_ID,
        "source_eligibility_decision_hash": HASHES[0],
        "source_ranking_record_hash": HASHES[1],
        "source_tier_record_hash": HASHES[2],
        "source_queue_record_hash": HASHES[3],
        "source_work_item_hash": HASHES[4],
        "source_dispatch_entry_hash": HASHES[5],
        "source_claim_entry_hash": HASHES[6],
        "source_activation_entry_hash": HASHES[7],
        "source_session_entry_hash": HASHES[8],
        "source_readiness_entry_hash": HASHES[9],
    }
    entry = dict(entry_body)
    entry["certification_entry_hash"] = certification_stable_hash(entry_body)
    body = {
        "schema_version": "OIA-025",
        "engine_id": "OIA-025",
        "certified_at": "2026-07-21T06:00:00+00:00",
        "certification_id": "oia025-certification-test",
        "certification_status": SESSION_CERTIFIED,
        "worker_id": "oracle-worker-test",
        "readiness_directory": "runtime/test/readiness",
        "certification_directory": str(directory),
        "source_readiness_id": "oia024-readiness-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "certification_entry_count": 1,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "readiness_policy_id": READINESS_POLICY_ID,
        "certification_policy_id": CERTIFICATION_POLICY_ID,
        "entries": [entry],
        "source_readiness_hash": HASHES[10],
        "source_session_hash": HASHES[11],
        "source_activation_hash": HASHES[12],
        "source_claim_hash": HASHES[13],
        "source_manifest_hash": HASHES[14],
        "source_batch_hash": HASHES[15],
        "read_only_corpus": True,
        "research_execution_allowed": False,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "certification_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["certification_hash"] = certification_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-026 TEST")
    print(" CERTIFIED EVIDENCE COLLECTION MANIFEST")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        certification_directory = root / "certification"
        manifest_directory = root / "evidence-manifest"
        source = write_certification(certification_directory)
        builder = OracleCertifiedResearchEvidenceCollectionManifestBuilder(
            certification_directory=certification_directory,
            evidence_manifest_directory=manifest_directory,
        )
        fixed_time = datetime(2026, 7, 21, 7, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed_time, persist=True)
        second = builder.build(generated_at=fixed_time, persist=False)

        assert first == second
        assert first.schema_version == "OIA-026"
        assert first.engine_id == "OIA-026"
        assert first.manifest_status == EVIDENCE_MANIFEST_ISSUED
        assert first.evidence_manifest_policy_id == EVIDENCE_MANIFEST_POLICY_ID
        assert first.source_certification_hash == source["certification_hash"]
        assert first.evidence_entry_count == 1
        assert first.entries[0].evidence_status == EVIDENCE_ENTRY_AUTHORIZED
        assert first.entries[0].source_certification_entry_hash == source["entries"][0]["certification_entry_hash"]
        assert "read_canonical_observations" in first.entries[0].authorized_evidence_operations
        assert "create_market_order" in first.entries[0].prohibited_operations
        assert first.read_only_corpus is True
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
        manifest_hash = body.pop("evidence_manifest_hash")
        assert manifest_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("evidence_entry_hash")
        assert entry_hash == stable_hash(entry_body)
        assert (manifest_directory / "current.json").exists()
        assert list((manifest_directory / "manifests").glob("*.json"))
        assert list((manifest_directory / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((certification_directory / "current.json").read_text(encoding="utf-8"))
        tampered["entries"][0]["priority_score"] = "0.000000"
        (certification_directory / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            builder.build(generated_at=fixed_time, persist=False)
        except CertifiedResearchEvidenceCollectionManifestInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-025 certification was accepted.")

    print("[PASS] Actual OIA-025 certification contract consumed")
    print("[PASS] Evidence manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-025 lineage preserved")
    print("[PASS] Bounded read-only evidence operations authorized")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered certification rejected")
    print("[PASS] Atomic evidence manifest artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
