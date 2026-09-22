from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import ACTIVATION_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_manifest_builder import (
    SESSION_POLICY_ID,
    SESSION_READY,
    SESSION_ENTRY_READY,
    stable_hash as session_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_readiness_gate import (
    READINESS_POLICY_ID,
    READINESS_VERIFIED,
    ENTRY_READINESS_VERIFIED,
    OracleQualifiedResearchWorkerSessionReadinessGate,
    QualifiedResearchWorkerSessionReadinessInvariantError,
    format_readiness,
    stable_hash,
)

NOW = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)


def make_entry(index: int) -> dict:
    body = {
        "session_sequence": index,
        "activation_sequence": index,
        "claim_sequence": index,
        "dispatch_sequence": index + 6,
        "batch_number": 4,
        "batch_position": index,
        "work_item_id": f"oia019-{index:032x}",
        "queue_position": index + 6,
        "source_rank": index + 6,
        "dimension": "candidate_family_horizon",
        "key": f"candidate-{index}|3600",
        "tier": "tier_2",
        "priority_score": f"{50-index}.00000000",
        "research_objective": (
            "evaluate_qualified_component_with_additional_read_only_evidence"
        ),
        "required_operations": [
            "load_verified_source_lineage",
            "read_additional_canonical_market_evidence",
        ],
        "prohibited_operations": [
            "create_trading_signal",
            "create_trading_recommendation",
            "publish_operator_alert",
            "handoff_to_qseries_execution",
            "create_market_order",
            "move_funds",
            "mutate_portfolio",
            "mutate_source_corpus",
        ],
        "completion_requirements": [
            "source_lineage_hashes_verified",
            "research_output_deterministically_hashed",
        ],
        "session_entry_status": SESSION_ENTRY_READY,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "source_eligibility_decision_hash": f"{index:064x}",
        "source_ranking_record_hash": f"{index+100:064x}",
        "source_tier_record_hash": f"{index+200:064x}",
        "source_queue_record_hash": f"{index+300:064x}",
        "source_work_item_hash": f"{index+400:064x}",
        "source_dispatch_entry_hash": f"{index+500:064x}",
        "source_claim_entry_hash": f"{index+600:064x}",
        "source_activation_entry_hash": f"{index+700:064x}",
    }
    return {**body, "session_entry_hash": session_hash(body)}


def write_session(directory: Path) -> dict:
    entries = [make_entry(1), make_entry(2)]
    body = {
        "schema_version": "OIA-023",
        "engine_id": "OIA-023",
        "generated_at": NOW,
        "session_id": "oia023-session-" + "a" * 32,
        "session_status": SESSION_READY,
        "worker_id": "oracle-research-worker-01",
        "activation_directory": "activations",
        "session_directory": str(directory),
        "source_activation_id": "oia022-activation-" + "b" * 32,
        "source_claim_id": "oia021-claim-" + "c" * 32,
        "manifest_id": "oia020-manifest-" + "d" * 32,
        "selected_batch_id": "oia020-batch-" + "e" * 32,
        "selected_batch_number": 4,
        "session_entry_count": 2,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "entries": entries,
        "source_activation_hash": "f" * 64,
        "source_claim_hash": "1" * 64,
        "source_manifest_hash": "2" * 64,
        "source_batch_hash": "3" * 64,
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
        "session_artifact_persistence_allowed": True,
    }
    payload = {**body, "session_hash": session_hash(body)}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: value.isoformat(),
        ) + "\n",
        encoding="utf-8",
    )
    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        session_directory = root / "sessions"
        readiness_directory = root / "readiness"
        source = write_session(session_directory)

        gate = OracleQualifiedResearchWorkerSessionReadinessGate(
            session_directory=session_directory,
            readiness_directory=readiness_directory,
        )
        readiness = gate.attest(generated_at=NOW, persist=True)

        assert readiness.schema_version == "OIA-024"
        assert readiness.engine_id == "OIA-024"
        assert readiness.readiness_status == READINESS_VERIFIED
        assert readiness.readiness_policy_id == READINESS_POLICY_ID
        assert readiness.readiness_entry_count == 2
        assert readiness.source_session_hash == source["session_hash"]
        assert [e.readiness_sequence for e in readiness.entries] == [1, 2]
        assert all(
            e.readiness_status == ENTRY_READINESS_VERIFIED
            for e in readiness.entries
        )

        for entry in readiness.entries:
            payload = dict(entry.to_dict())
            digest = payload.pop("readiness_entry_hash")
            assert digest == stable_hash(payload)

        payload = dict(readiness.to_dict())
        digest = payload.pop("readiness_hash")
        assert digest == stable_hash(payload)
        assert readiness.read_only_corpus
        assert not readiness.research_execution_allowed
        assert not readiness.execution_allowed
        assert not readiness.qseries_handoff_allowed
        assert not readiness.market_order_creation_allowed
        assert not readiness.funds_movement_allowed
        assert not readiness.portfolio_mutation_allowed

        current = readiness_directory / "current.json"
        immutable = (
            readiness_directory
            / "attestations"
            / f"{readiness.readiness_id}-{readiness.readiness_hash}.json"
        )
        assert current.exists()
        assert immutable.exists()
        before = current.read_bytes()

        replay = gate.attest(generated_at=NOW, persist=True)
        assert replay.readiness_id == readiness.readiness_id
        assert replay.readiness_hash == readiness.readiness_hash
        assert current.read_bytes() == before

        rendered = format_readiness(readiness)
        assert "ORACLE QUALIFIED RESEARCH WORKER SESSION READINESS" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        tampered = json.loads(
            (session_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["entries"][0]["priority_score"] = "0.00000000"
        (session_directory / "current.json").write_text(
            json.dumps(tampered, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            gate.attest(generated_at=NOW, persist=False)
        except QualifiedResearchWorkerSessionReadinessInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-023 session was not rejected.")

    print(
        "[PASS] OIA-024 Oracle Qualified Research "
        "Worker Session Readiness Gate"
    )


if __name__ == "__main__":
    run_test()
