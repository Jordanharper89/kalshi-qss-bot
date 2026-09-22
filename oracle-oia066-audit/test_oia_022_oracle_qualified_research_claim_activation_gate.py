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
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import (
    CLAIM_POLICY_ID,
    CLAIM_READY,
    CLAIMED,
    stable_hash as claim_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import (
    ACTIVATION_POLICY_ID,
    ACTIVATION_READY,
    ENTRY_ACTIVATED,
    OracleQualifiedResearchClaimActivationGate,
    QualifiedResearchClaimActivationInvariantError,
    format_activation,
    stable_hash,
)

NOW = datetime(2026, 7, 21, 10, 0, 0, tzinfo=timezone.utc)


def make_entry(index: int) -> dict:
    body = {
        "claim_sequence": index,
        "dispatch_sequence": index + 2,
        "batch_number": 2,
        "batch_position": index,
        "work_item_id": f"oia019-{index:032x}",
        "queue_position": index + 2,
        "source_rank": index + 2,
        "dimension": "candidate_family_horizon",
        "key": f"candidate-{index}|900",
        "tier": "tier_2",
        "priority_score": f"{70-index}.00000000",
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
        "claim_status": CLAIMED,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "source_eligibility_decision_hash": f"{index:064x}",
        "source_ranking_record_hash": f"{index+100:064x}",
        "source_tier_record_hash": f"{index+200:064x}",
        "source_queue_record_hash": f"{index+300:064x}",
        "source_work_item_hash": f"{index+400:064x}",
        "source_dispatch_entry_hash": f"{index+500:064x}",
    }
    return {**body, "claim_entry_hash": claim_hash(body)}


def write_claim(directory: Path) -> dict:
    entries = [make_entry(1), make_entry(2)]
    body = {
        "schema_version": "OIA-021",
        "engine_id": "OIA-021",
        "generated_at": NOW,
        "claim_id": "oia021-claim-" + "a" * 32,
        "claim_status": CLAIM_READY,
        "worker_id": "oracle-research-worker-01",
        "dispatch_directory": "dispatch",
        "claim_directory": str(directory),
        "manifest_id": "oia020-manifest-" + "b" * 32,
        "selected_batch_id": "oia020-batch-" + "c" * 32,
        "selected_batch_number": 2,
        "selected_batch_entry_count": 2,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "entries": entries,
        "source_manifest_hash": "d" * 64,
        "source_batch_hash": "e" * 64,
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
        "claim_artifact_persistence_allowed": True,
    }
    payload = {**body, "claim_hash": claim_hash(body)}
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
        claim_directory = root / "claims"
        activation_directory = root / "activations"
        source = write_claim(claim_directory)
        gate = OracleQualifiedResearchClaimActivationGate(
            claim_directory=claim_directory,
            activation_directory=activation_directory,
        )
        activation = gate.activate(generated_at=NOW, persist=True)

        assert activation.schema_version == "OIA-022"
        assert activation.engine_id == "OIA-022"
        assert activation.activation_status == ACTIVATION_READY
        assert activation.activation_policy_id == ACTIVATION_POLICY_ID
        assert activation.activated_entry_count == 2
        assert activation.source_claim_hash == source["claim_hash"]
        assert [e.activation_sequence for e in activation.entries] == [1, 2]
        assert [e.dispatch_sequence for e in activation.entries] == [3, 4]
        assert all(e.activation_status == ENTRY_ACTIVATED for e in activation.entries)

        for entry in activation.entries:
            payload = dict(entry.to_dict())
            digest = payload.pop("activation_entry_hash")
            assert digest == stable_hash(payload)

        payload = dict(activation.to_dict())
        digest = payload.pop("activation_hash")
        assert digest == stable_hash(payload)
        assert activation.read_only_corpus
        assert not activation.research_execution_allowed
        assert not activation.execution_allowed
        assert not activation.qseries_handoff_allowed
        assert not activation.market_order_creation_allowed
        assert not activation.funds_movement_allowed
        assert not activation.portfolio_mutation_allowed

        current = activation_directory / "current.json"
        immutable = (
            activation_directory
            / "activations"
            / f"{activation.activation_id}-{activation.activation_hash}.json"
        )
        assert current.exists()
        assert immutable.exists()
        before = current.read_bytes()

        replay = gate.activate(generated_at=NOW, persist=True)
        assert replay.activation_id == activation.activation_id
        assert replay.activation_hash == activation.activation_hash
        assert current.read_bytes() == before

        rendered = format_activation(activation)
        assert "ORACLE QUALIFIED RESEARCH CLAIM ACTIVATION" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        tampered = json.loads(
            (claim_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["entries"][0]["priority_score"] = "1.00000000"
        (claim_directory / "current.json").write_text(
            json.dumps(tampered, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            gate.activate(generated_at=NOW, persist=False)
        except QualifiedResearchClaimActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-021 claim was not rejected.")

    print("[PASS] OIA-022 Oracle Qualified Research Claim Activation Gate")


if __name__ == "__main__":
    run_test()
