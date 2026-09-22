from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    RANKING_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    QUEUE_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import (
    READY,
    RESEARCH_OBJECTIVE,
    WORK_ITEM_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import (
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    MANIFEST_READY,
    stable_hash as dispatch_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import (
    CLAIMED,
    CLAIM_POLICY_ID,
    CLAIM_READY,
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchDispatchClaimGate,
    QualifiedResearchDispatchClaimInvariantError,
    format_claim,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    9,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_entry(
    *,
    index: int,
    batch_number: int,
    batch_position: int,
    tier: str,
    score: str,
) -> dict:
    body = {
        "dispatch_sequence": index,
        "batch_number": batch_number,
        "batch_position": batch_position,
        "work_item_id": (
            f"oia019-{index:032x}"
        ),
        "work_item_status": READY,
        "queue_position": index,
        "source_rank": index,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": f"candidate-{index}|300",
        "tier": tier,
        "priority_score": score,
        "research_objective": (
            RESEARCH_OBJECTIVE
        ),
        "required_operations": [
            "load_verified_source_lineage",
            "read_additional_canonical_market_evidence",
            "compute_deterministic_research_metrics",
            "record_replayable_research_evidence",
            "produce_content_addressed_research_result",
        ],
        "prohibited_operations": [
            "create_trading_signal",
            "create_trading_recommendation",
            "publish_operator_alert",
            "handoff_to_qseries_execution",
            "create_market_order",
            "modify_market_order",
            "cancel_market_order",
            "move_funds",
            "mutate_portfolio",
            "mutate_source_corpus",
        ],
        "completion_requirements": [
            "source_lineage_hashes_verified",
            "research_inputs_content_addressed",
            "research_method_policy_identified",
            "research_output_deterministically_hashed",
            "replay_produces_identical_output",
            "no_prohibited_operation_requested",
        ],
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "dispatch_status": DISPATCH_READY,
        "reason_codes": [
            "oia_019_work_item_verified",
            "work_item_identity_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            "deterministic_dispatch_sequence_assigned",
            "research_dispatch_definition_only",
        ],
        "source_eligibility_decision_hash": (
            f"{index:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{index + 100:064x}"[-64:]
        ),
        "source_tier_record_hash": (
            f"{index + 200:064x}"[-64:]
        ),
        "source_queue_record_hash": (
            f"{index + 300:064x}"[-64:]
        ),
        "source_work_item_hash": (
            f"{index + 400:064x}"[-64:]
        ),
    }

    return {
        **body,
        "dispatch_entry_hash": dispatch_hash(
            body
        ),
    }


def make_batch(
    *,
    manifest_id: str,
    batch_number: int,
    entries: list[dict],
    batch_size: int,
) -> dict:
    body = {
        "manifest_id": manifest_id,
        "batch_id": (
            f"oia020-batch-{batch_number:032x}"
        ),
        "batch_number": batch_number,
        "batch_size_limit": batch_size,
        "entry_count": len(entries),
        "first_dispatch_sequence": (
            entries[0]["dispatch_sequence"]
        ),
        "last_dispatch_sequence": (
            entries[-1]["dispatch_sequence"]
        ),
        "first_queue_position": (
            entries[0]["queue_position"]
        ),
        "last_queue_position": (
            entries[-1]["queue_position"]
        ),
        "dispatch_entry_hashes": [
            entry["dispatch_entry_hash"]
            for entry in entries
        ],
        "source_work_item_hashes": [
            entry["source_work_item_hash"]
            for entry in entries
        ],
    }

    return {
        **body,
        "batch_hash": dispatch_hash(
            body
        ),
    }


def write_manifest(
    directory: Path,
) -> dict:
    manifest_id = (
        "oia020-manifest-"
        + "a" * 32
    )

    entries = [
        make_entry(
            index=1,
            batch_number=1,
            batch_position=1,
            tier=TIER_1,
            score="88.00000000",
        ),
        make_entry(
            index=2,
            batch_number=1,
            batch_position=2,
            tier=TIER_1,
            score="78.00000000",
        ),
        make_entry(
            index=3,
            batch_number=2,
            batch_position=1,
            tier=TIER_2,
            score="62.00000000",
        ),
        make_entry(
            index=4,
            batch_number=2,
            batch_position=2,
            tier=TIER_3,
            score="42.00000000",
        ),
    ]

    batches = [
        make_batch(
            manifest_id=manifest_id,
            batch_number=1,
            entries=entries[:2],
            batch_size=2,
        ),
        make_batch(
            manifest_id=manifest_id,
            batch_number=2,
            entries=entries[2:],
            batch_size=2,
        ),
    ]

    body = {
        "schema_version": "OIA-020",
        "engine_id": "OIA-020",
        "generated_at": NOW,
        "manifest_id": manifest_id,
        "manifest_status": MANIFEST_READY,
        "work_item_directory": "work-items",
        "dispatch_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "batch_size": 2,
        "source_work_item_count": 4,
        "dispatch_entry_count": 4,
        "dispatch_batch_count": 2,
        "tier_1_dispatch_count": 2,
        "tier_2_dispatch_count": 1,
        "tier_3_dispatch_count": 1,
        "entries": entries,
        "batches": batches,
        "source_work_item_report_hash": (
            "f" * 64
        ),
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
        "dispatch_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "manifest_hash": dispatch_hash(
            body
        ),
    }

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory
        / "current.json"
    ).write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: (
                value.isoformat()
            ),
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        dispatch_directory = (
            root
            / "dispatch"
        )

        claim_directory = (
            root
            / "claims"
        )

        source_manifest = write_manifest(
            dispatch_directory
        )

        gate = (
            OracleQualifiedResearchDispatchClaimGate(
                dispatch_directory=(
                    dispatch_directory
                ),
                claim_directory=(
                    claim_directory
                ),
            )
        )

        claim = gate.claim(
            worker_id="oracle-research-worker-01",
            batch_number=2,
            generated_at=NOW,
            persist=True,
        )

        assert (
            claim.schema_version
            == SCHEMA_VERSION
            == "OIA-021"
        )

        assert (
            claim.engine_id
            == ENGINE_ID
            == "OIA-021"
        )

        assert claim.claim_status == CLAIM_READY
        assert (
            claim.worker_id
            == "oracle-research-worker-01"
        )
        assert claim.selected_batch_number == 2
        assert claim.selected_batch_entry_count == 2
        assert claim.claim_policy_id == CLAIM_POLICY_ID

        assert [
            entry.claim_sequence
            for entry in claim.entries
        ] == [
            1,
            2,
        ]

        assert [
            entry.dispatch_sequence
            for entry in claim.entries
        ] == [
            3,
            4,
        ]

        assert [
            entry.batch_position
            for entry in claim.entries
        ] == [
            1,
            2,
        ]

        assert all(
            entry.claim_status == CLAIMED
            for entry in claim.entries
        )

        assert [
            entry.tier
            for entry in claim.entries
        ] == [
            TIER_2,
            TIER_3,
        ]

        assert (
            claim.source_manifest_hash
            == source_manifest[
                "manifest_hash"
            ]
        )

        assert (
            claim.source_batch_hash
            == source_manifest[
                "batches"
            ][1]["batch_hash"]
        )

        for entry in claim.entries:
            payload = dict(
                entry.to_dict()
            )

            digest = payload.pop(
                "claim_entry_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert (
                "create_market_order"
                in entry.prohibited_operations
            )

            assert (
                "handoff_to_qseries_execution"
                in entry.prohibited_operations
            )

        claim_payload = dict(
            claim.to_dict()
        )

        claim_digest = claim_payload.pop(
            "claim_hash"
        )

        assert claim_digest == stable_hash(
            claim_payload
        )

        assert claim.claim_id.startswith(
            "oia021-claim-"
        )

        assert claim.read_only_corpus
        assert not claim.research_execution_allowed
        assert not claim.execution_allowed
        assert not claim.alerts_allowed
        assert not claim.qseries_handoff_allowed
        assert not claim.signals_allowed
        assert (
            not claim.trading_recommendations_allowed
        )
        assert not claim.source_mutation_allowed
        assert (
            not claim.market_order_creation_allowed
        )
        assert not claim.funds_movement_allowed
        assert (
            not claim.portfolio_mutation_allowed
        )
        assert (
            claim.claim_artifact_persistence_allowed
        )

        current_path = (
            claim_directory
            / "current.json"
        )

        immutable_path = (
            claim_directory
            / "claims"
            / (
                f"{claim.claim_id}-"
                f"{claim.claim_hash}.json"
            )
        )

        worker_path = (
            claim_directory
            / "workers"
            / "oracle-research-worker-01"
            / (
                "batch-2-"
                f"{claim.claim_id}.json"
            )
        )

        assert current_path.exists()
        assert immutable_path.exists()
        assert worker_path.exists()

        current_bytes = (
            current_path.read_bytes()
        )

        immutable_bytes = (
            immutable_path.read_bytes()
        )

        replay = gate.claim(
            worker_id="ORACLE-RESEARCH-WORKER-01",
            batch_number=2,
            generated_at=NOW,
            persist=True,
        )

        assert replay.claim_id == claim.claim_id
        assert replay.claim_hash == claim.claim_hash

        assert (
            current_path.read_bytes()
            == current_bytes
        )

        assert (
            immutable_path.read_bytes()
            == immutable_bytes
        )

        rendered = format_claim(
            claim
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH CLAIM"
            in rendered
        )

        assert "oracle-research-worker-01" in rendered
        assert "candidate-3|300" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        try:
            gate.claim(
                worker_id="x",
                batch_number=1,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Malformed worker identity was not rejected."
            )

        try:
            gate.claim(
                worker_id="oracle-worker-02",
                batch_number=99,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Unknown dispatch batch was not rejected."
            )

        tampered = json.loads(
            (
                dispatch_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["entries"][0][
            "priority_score"
        ] = "1.00000000"

        (
            dispatch_directory
            / "current.json"
        ).write_text(
            json.dumps(
                tampered,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        try:
            gate.claim(
                worker_id="oracle-worker-03",
                batch_number=1,
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchClaimInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-020 manifest was not rejected."
            )

    print(
        "[PASS] OIA-021 Oracle Qualified Research "
        "Dispatch Claim Gate"
    )


if __name__ == "__main__":
    run_test()
