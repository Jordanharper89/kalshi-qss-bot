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
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import (
    ACTIVATION_POLICY_ID,
    ACTIVATION_READY,
    ENTRY_ACTIVATED,
    stable_hash as activation_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_manifest_builder import (
    SESSION_POLICY_ID,
    SESSION_READY,
    SESSION_ENTRY_READY,
    OracleQualifiedResearchWorkerSessionManifestBuilder,
    QualifiedResearchWorkerSessionInvariantError,
    format_session,
    stable_hash,
)

NOW = datetime(2026, 7, 21, 11, 0, 0, tzinfo=timezone.utc)


def make_entry(index: int) -> dict:
    body = {
        "activation_sequence": index,
        "claim_sequence": index,
        "dispatch_sequence": index + 4,
        "batch_number": 3,
        "batch_position": index,
        "work_item_id": f"oia019-{index:032x}",
        "queue_position": index + 4,
        "source_rank": index + 4,
        "dimension": "candidate_family_horizon",
        "key": f"candidate-{index}|1800",
        "tier": "tier_2",
        "priority_score": f"{60-index}.00000000",
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
        "activation_status": ENTRY_ACTIVATED,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "source_eligibility_decision_hash": f"{index:064x}",
        "source_ranking_record_hash": f"{index+100:064x}",
        "source_tier_record_hash": f"{index+200:064x}",
        "source_queue_record_hash": f"{index+300:064x}",
        "source_work_item_hash": f"{index+400:064x}",
        "source_dispatch_entry_hash": f"{index+500:064x}",
        "source_claim_entry_hash": f"{index+600:064x}",
    }
    return {**body, "activation_entry_hash": activation_hash(body)}


def write_activation(directory: Path) -> dict:
    entries = [make_entry(1), make_entry(2)]
    body = {
        "schema_version": "OIA-022",
        "engine_id": "OIA-022",
        "generated_at": NOW,
        "activation_id": "oia022-activation-" + "a" * 32,
        "activation_status": ACTIVATION_READY,
        "worker_id": "oracle-research-worker-01",
        "claim_directory": "claims",
        "activation_directory": str(directory),
        "source_claim_id": "oia021-claim-" + "b" * 32,
        "manifest_id": "oia020-manifest-" + "c" * 32,
        "selected_batch_id": "oia020-batch-" + "d" * 32,
        "selected_batch_number": 3,
        "activated_entry_count": 2,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "entries": entries,
        "source_claim_hash": "e" * 64,
        "source_manifest_hash": "f" * 64,
        "source_batch_hash": "1" * 64,
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
        "activation_artifact_persistence_allowed": True,
    }
    payload = {**body, "activation_hash": activation_hash(body)}
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
        activation_directory = root / "activations"
        session_directory = root / "sessions"
        source = write_activation(activation_directory)

        builder = OracleQualifiedResearchWorkerSessionManifestBuilder(
            activation_directory=activation_directory,
            session_directory=session_directory,
        )
        session = builder.build(generated_at=NOW, persist=True)

        assert session.schema_version == "OIA-023"
        assert session.engine_id == "OIA-023"
        assert session.session_status == SESSION_READY
        assert session.session_policy_id == SESSION_POLICY_ID
        assert session.session_entry_count == 2
        assert session.source_activation_hash == source["activation_hash"]
        assert [e.session_sequence for e in session.entries] == [1, 2]
        assert [e.dispatch_sequence for e in session.entries] == [5, 6]
        assert all(
            e.session_entry_status == SESSION_ENTRY_READY
            for e in session.entries
        )

        for entry in session.entries:
            payload = dict(entry.to_dict())
            digest = payload.pop("session_entry_hash")
            assert digest == stable_hash(payload)

        payload = dict(session.to_dict())
        digest = payload.pop("session_hash")
        assert digest == stable_hash(payload)
        assert session.read_only_corpus
        assert not session.research_execution_allowed
        assert not session.execution_allowed
        assert not session.qseries_handoff_allowed
        assert not session.market_order_creation_allowed
        assert not session.funds_movement_allowed
        assert not session.portfolio_mutation_allowed

        current = session_directory / "current.json"
        immutable = (
            session_directory
            / "sessions"
            / f"{session.session_id}-{session.session_hash}.json"
        )
        assert current.exists()
        assert immutable.exists()
        before = current.read_bytes()

        replay = builder.build(generated_at=NOW, persist=True)
        assert replay.session_id == session.session_id
        assert replay.session_hash == session.session_hash
        assert current.read_bytes() == before

        rendered = format_session(session)
        assert "ORACLE QUALIFIED RESEARCH WORKER SESSION MANIFEST" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        tampered = json.loads(
            (activation_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["entries"][0]["priority_score"] = "0.00000000"
        (activation_directory / "current.json").write_text(
            json.dumps(tampered, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            builder.build(generated_at=NOW, persist=False)
        except QualifiedResearchWorkerSessionInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-022 activation was not rejected.")

    print(
        "[PASS] OIA-023 Oracle Qualified Research "
        "Worker Session Manifest Builder"
    )


if __name__ == "__main__":
    run_test()
