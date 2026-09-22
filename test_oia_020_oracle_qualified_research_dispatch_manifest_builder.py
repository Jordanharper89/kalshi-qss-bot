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
    stable_hash as work_item_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import (
    DISPATCH_POLICY_ID,
    DISPATCH_READY,
    ENGINE_ID,
    MANIFEST_READY,
    SCHEMA_VERSION,
    OracleQualifiedResearchDispatchManifestBuilder,
    QualifiedResearchDispatchManifestInvariantError,
    format_manifest,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    8,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_work_item(
    *,
    index: int,
    tier: str,
    score: str,
    key: str,
) -> dict:
    body = {
        "work_item_id": (
            f"oia019-{index:032x}"
        ),
        "work_item_status": READY,
        "queue_position": index,
        "source_rank": index,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": key,
        "tier": tier,
        "priority_score": score,
        "decisive_count": (
            800 - index
        ),
        "empirical_win_rate": (
            "0.65000000"
        ),
        "confidence_lower_bound": (
            "0.59000000"
        ),
        "calibration_quality": (
            "0.80000000"
        ),
        "reliability_quality": (
            "0.80000000"
        ),
        "resolution_quality": (
            "0.40000000"
        ),
        "sample_strength": (
            "1.00000000"
        ),
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
        "ranking_policy_id": (
            RANKING_POLICY_ID
        ),
        "tier_policy_id": (
            TIER_POLICY_ID
        ),
        "queue_policy_id": (
            QUEUE_POLICY_ID
        ),
        "work_item_policy_id": (
            WORK_ITEM_POLICY_ID
        ),
        "reason_codes": [
            "oia_018_queue_record_verified",
            "queue_admission_preserved",
            "queue_position_preserved",
            "upstream_lineage_preserved",
            "deterministic_work_item_id_created",
            "research_work_definition_only",
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
    }

    return {
        **body,
        "work_item_hash": (
            work_item_hash(body)
        ),
    }


def write_work_item_report(
    directory: Path,
    work_items: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-019",
        "engine_id": "OIA-019",
        "generated_at": NOW,
        "queue_directory": "queue",
        "work_item_directory": str(
            directory
        ),
        "ranking_policy_id": (
            RANKING_POLICY_ID
        ),
        "tier_policy_id": (
            TIER_POLICY_ID
        ),
        "queue_policy_id": (
            QUEUE_POLICY_ID
        ),
        "work_item_policy_id": (
            WORK_ITEM_POLICY_ID
        ),
        "source_queue_record_count": len(
            work_items
        ),
        "source_queue_admitted_count": len(
            work_items
        ),
        "source_capacity_deferred_count": 0,
        "work_item_count": len(
            work_items
        ),
        "excluded_record_count": 0,
        "tier_1_work_item_count": sum(
            item["tier"] == TIER_1
            for item in work_items
        ),
        "tier_2_work_item_count": sum(
            item["tier"] == TIER_2
            for item in work_items
        ),
        "tier_3_work_item_count": sum(
            item["tier"] == TIER_3
            for item in work_items
        ),
        "work_items": work_items,
        "excluded_queue_record_hashes": [],
        "source_queue_report_hash": (
            "f" * 64
        ),
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "work_item_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": (
            work_item_hash(body)
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

        work_item_directory = (
            root
            / "work-items"
        )

        dispatch_directory = (
            root
            / "dispatch"
        )

        source_work_items = [
            make_work_item(
                index=1,
                tier=TIER_1,
                score="84.00000000",
                key="momentum|300",
            ),
            make_work_item(
                index=2,
                tier=TIER_1,
                score="76.00000000",
                key="reversion|300",
            ),
            make_work_item(
                index=3,
                tier=TIER_2,
                score="64.00000000",
                key="momentum|900",
            ),
            make_work_item(
                index=4,
                tier=TIER_2,
                score="55.00000000",
                key="reversion|900",
            ),
            make_work_item(
                index=5,
                tier=TIER_3,
                score="43.00000000",
                key="momentum|3600",
            ),
        ]

        source_report = (
            write_work_item_report(
                work_item_directory,
                source_work_items,
            )
        )

        builder = (
            OracleQualifiedResearchDispatchManifestBuilder(
                work_item_directory=(
                    work_item_directory
                ),
                dispatch_directory=(
                    dispatch_directory
                ),
                batch_size=2,
            )
        )

        manifest = builder.build(
            generated_at=NOW,
            persist=True,
        )

        assert (
            manifest.schema_version
            == SCHEMA_VERSION
            == "OIA-020"
        )

        assert (
            manifest.engine_id
            == ENGINE_ID
            == "OIA-020"
        )

        assert (
            manifest.manifest_status
            == MANIFEST_READY
        )

        assert (
            manifest.dispatch_policy_id
            == DISPATCH_POLICY_ID
        )

        assert manifest.batch_size == 2
        assert manifest.source_work_item_count == 5
        assert manifest.dispatch_entry_count == 5
        assert manifest.dispatch_batch_count == 3

        assert manifest.tier_1_dispatch_count == 2
        assert manifest.tier_2_dispatch_count == 2
        assert manifest.tier_3_dispatch_count == 1

        assert [
            entry.dispatch_sequence
            for entry in manifest.entries
        ] == [
            1,
            2,
            3,
            4,
            5,
        ]

        assert [
            entry.queue_position
            for entry in manifest.entries
        ] == [
            1,
            2,
            3,
            4,
            5,
        ]

        assert [
            entry.batch_number
            for entry in manifest.entries
        ] == [
            1,
            1,
            2,
            2,
            3,
        ]

        assert [
            entry.batch_position
            for entry in manifest.entries
        ] == [
            1,
            2,
            1,
            2,
            1,
        ]

        assert all(
            entry.dispatch_status
            == DISPATCH_READY
            for entry in manifest.entries
        )

        assert [
            entry.source_work_item_hash
            for entry in manifest.entries
        ] == [
            item["work_item_hash"]
            for item in source_work_items
        ]

        assert (
            manifest.source_work_item_report_hash
            == source_report["report_hash"]
        )

        assert len(manifest.batches) == 3

        assert manifest.batches[0].batch_number == 1
        assert manifest.batches[0].entry_count == 2
        assert (
            manifest.batches[0].first_dispatch_sequence
            == 1
        )
        assert (
            manifest.batches[0].last_dispatch_sequence
            == 2
        )

        assert manifest.batches[1].batch_number == 2
        assert manifest.batches[1].entry_count == 2

        assert manifest.batches[2].batch_number == 3
        assert manifest.batches[2].entry_count == 1

        for entry in manifest.entries:
            payload = dict(
                entry.to_dict()
            )

            digest = payload.pop(
                "dispatch_entry_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert (
                "oia_019_work_item_verified"
                in entry.reason_codes
            )

            assert (
                "queue_position_preserved"
                in entry.reason_codes
            )

            assert (
                "research_dispatch_definition_only"
                in entry.reason_codes
            )

            assert (
                "handoff_to_qseries_execution"
                in entry.prohibited_operations
            )

            assert (
                "create_market_order"
                in entry.prohibited_operations
            )

        for batch in manifest.batches:
            payload = dict(
                batch.to_dict()
            )

            digest = payload.pop(
                "batch_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert batch.batch_id.startswith(
                "oia020-batch-"
            )

        manifest_payload = dict(
            manifest.to_dict()
        )

        manifest_digest = (
            manifest_payload.pop(
                "manifest_hash"
            )
        )

        assert manifest_digest == stable_hash(
            manifest_payload
        )

        assert manifest.manifest_id.startswith(
            "oia020-manifest-"
        )

        assert manifest.read_only_corpus
        assert not manifest.research_execution_allowed
        assert not manifest.execution_allowed
        assert not manifest.alerts_allowed
        assert not manifest.qseries_handoff_allowed
        assert not manifest.signals_allowed
        assert (
            not manifest.trading_recommendations_allowed
        )
        assert not manifest.source_mutation_allowed
        assert (
            not manifest.market_order_creation_allowed
        )
        assert not manifest.funds_movement_allowed
        assert (
            not manifest.portfolio_mutation_allowed
        )
        assert (
            manifest.dispatch_artifact_persistence_allowed
        )

        current_path = (
            dispatch_directory
            / "current.json"
        )

        immutable_manifest_path = (
            dispatch_directory
            / "manifests"
            / (
                f"{manifest.manifest_id}-"
                f"{manifest.manifest_hash}.json"
            )
        )

        batch_paths = [
            (
                dispatch_directory
                / "batches"
                / f"{batch.batch_id}.json"
            )
            for batch in manifest.batches
        ]

        assert current_path.exists()
        assert immutable_manifest_path.exists()

        for path in batch_paths:
            assert path.exists()

        current_bytes = (
            current_path.read_bytes()
        )

        manifest_bytes = (
            immutable_manifest_path.read_bytes()
        )

        first_batch_bytes = (
            batch_paths[0].read_bytes()
        )

        replay = builder.build(
            generated_at=NOW,
            persist=True,
        )

        assert (
            replay.manifest_id
            == manifest.manifest_id
        )

        assert (
            replay.manifest_hash
            == manifest.manifest_hash
        )

        assert (
            replay.batches[0].batch_id
            == manifest.batches[0].batch_id
        )

        assert (
            current_path.read_bytes()
            == current_bytes
        )

        assert (
            immutable_manifest_path.read_bytes()
            == manifest_bytes
        )

        assert (
            batch_paths[0].read_bytes()
            == first_batch_bytes
        )

        rendered = format_manifest(
            manifest
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "DISPATCH MANIFEST"
            in rendered
        )

        assert "momentum|300" in rendered
        assert "oia020-manifest-" in rendered
        assert "NO RESEARCH EXECUTION" in rendered

        tampered = json.loads(
            (
                work_item_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["work_items"][0][
            "priority_score"
        ] = "1.00000000"

        (
            work_item_directory
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
            builder.build(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchManifestInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-019 report was not rejected."
            )

        invalid_items = [
            make_work_item(
                index=1,
                tier=TIER_1,
                score="80.00000000",
                key="first",
            ),
            make_work_item(
                index=2,
                tier=TIER_1,
                score="90.00000000",
                key="second",
            ),
        ]

        write_work_item_report(
            work_item_directory,
            invalid_items,
        )

        try:
            builder.build(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchDispatchManifestInvariantError:
            pass
        else:
            raise AssertionError(
                "Out-of-order OIA-019 priority scores "
                "were not rejected."
            )

    print(
        "[PASS] OIA-020 Oracle Qualified Research "
        "Dispatch Manifest Builder"
    )


if __name__ == "__main__":
    run_test()
