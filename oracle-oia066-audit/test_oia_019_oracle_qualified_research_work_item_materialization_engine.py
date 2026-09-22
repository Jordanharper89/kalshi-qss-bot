from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    RANKING_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    QUEUE_ADMITTED,
    QUEUE_POLICY_ID,
    stable_hash as queue_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import (
    ENGINE_ID,
    READY,
    RESEARCH_OBJECTIVE,
    SCHEMA_VERSION,
    WORK_ITEM_POLICY_ID,
    OracleQualifiedResearchWorkItemMaterializationEngine,
    QualifiedResearchWorkItemInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    7,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_queue_record(
    *,
    source_rank: int,
    queue_position: int | None,
    key: str,
    tier: str,
    score: str,
    queue_status: str,
    decisive_count: int,
) -> dict:
    body = {
        "source_rank": source_rank,
        "queue_position": queue_position,
        "dimension": (
            "candidate_family_horizon"
        ),
        "key": key,
        "tier": tier,
        "tier_status": ADMITTED,
        "queue_status": queue_status,
        "priority_score": score,
        "decisive_count": decisive_count,
        "empirical_win_rate": "0.65000000",
        "confidence_lower_bound": "0.59000000",
        "calibration_quality": "0.80000000",
        "reliability_quality": "0.80000000",
        "resolution_quality": "0.40000000",
        "sample_strength": "1.00000000",
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "reason_codes": [
            "oia_017_tier_record_verified",
            "source_rank_preserved",
            "source_tier_preserved",
            "deterministic_queue_policy_applied",
            "research_scheduling_only",
        ],
        "source_eligibility_decision_hash": (
            f"{source_rank:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{source_rank + 100:064x}"[-64:]
        ),
        "source_tier_record_hash": (
            f"{source_rank + 200:064x}"[-64:]
        ),
    }

    return {
        **body,
        "queue_record_hash": queue_hash(body),
    }


def write_queue_report(
    directory: Path,
    records: list[dict],
    *,
    queue_capacity: int,
) -> dict:
    admitted_count = sum(
        record["queue_status"]
        == QUEUE_ADMITTED
        for record in records
    )

    deferred_count = sum(
        record["queue_status"]
        == CAPACITY_DEFERRED
        for record in records
    )

    body = {
        "schema_version": "OIA-018",
        "engine_id": "OIA-018",
        "generated_at": NOW,
        "tier_directory": "tiers",
        "queue_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "queue_capacity": queue_capacity,
        "source_tier_record_count": len(records),
        "queue_admitted_count": admitted_count,
        "capacity_deferred_count": deferred_count,
        "queue_denied_count": 0,
        "tier_1_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_1
            for record in records
        ),
        "tier_2_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_2
            for record in records
        ),
        "tier_3_admitted_count": sum(
            record["queue_status"]
            == QUEUE_ADMITTED
            and record["tier"] == TIER_3
            for record in records
        ),
        "records": records,
        "source_tier_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "queue_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": queue_hash(body),
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

        queue_directory = (
            root
            / "queue"
        )

        work_item_directory = (
            root
            / "work-items"
        )

        source_records = [
            make_queue_record(
                source_rank=1,
                queue_position=1,
                key="momentum|300",
                tier=TIER_1,
                score="82.50000000",
                queue_status=QUEUE_ADMITTED,
                decisive_count=700,
            ),
            make_queue_record(
                source_rank=2,
                queue_position=2,
                key="reversion|900",
                tier=TIER_2,
                score="63.25000000",
                queue_status=QUEUE_ADMITTED,
                decisive_count=500,
            ),
            make_queue_record(
                source_rank=3,
                queue_position=None,
                key="momentum|3600",
                tier=TIER_3,
                score="49.75000000",
                queue_status=CAPACITY_DEFERRED,
                decisive_count=350,
            ),
        ]

        source_report = write_queue_report(
            queue_directory,
            source_records,
            queue_capacity=2,
        )

        engine = (
            OracleQualifiedResearchWorkItemMaterializationEngine(
                queue_directory=(
                    queue_directory
                ),
                work_item_directory=(
                    work_item_directory
                ),
            )
        )

        report = engine.materialize(
            generated_at=NOW,
            persist=True,
        )

        assert (
            report.schema_version
            == SCHEMA_VERSION
            == "OIA-019"
        )

        assert (
            report.engine_id
            == ENGINE_ID
            == "OIA-019"
        )

        assert (
            report.ranking_policy_id
            == RANKING_POLICY_ID
        )

        assert (
            report.tier_policy_id
            == TIER_POLICY_ID
        )

        assert (
            report.queue_policy_id
            == QUEUE_POLICY_ID
        )

        assert (
            report.work_item_policy_id
            == WORK_ITEM_POLICY_ID
        )

        assert (
            report.source_queue_record_count
            == 3
        )

        assert (
            report.source_queue_admitted_count
            == 2
        )

        assert (
            report.source_capacity_deferred_count
            == 1
        )

        assert (
            report.work_item_count
            == 2
        )

        assert (
            report.excluded_record_count
            == 1
        )

        assert (
            report.tier_1_work_item_count
            == 1
        )

        assert (
            report.tier_2_work_item_count
            == 1
        )

        assert (
            report.tier_3_work_item_count
            == 0
        )

        first = report.work_items[0]
        second = report.work_items[1]

        assert first.queue_position == 1
        assert first.source_rank == 1
        assert first.tier == TIER_1
        assert first.key == "momentum|300"
        assert first.work_item_status == READY

        assert second.queue_position == 2
        assert second.source_rank == 2
        assert second.tier == TIER_2
        assert second.key == "reversion|900"
        assert second.work_item_status == READY

        assert first.research_objective == (
            RESEARCH_OBJECTIVE
        )

        assert (
            first.source_queue_record_hash
            == source_records[0][
                "queue_record_hash"
            ]
        )

        assert (
            second.source_queue_record_hash
            == source_records[1][
                "queue_record_hash"
            ]
        )

        assert (
            source_records[2][
                "queue_record_hash"
            ]
            in report.excluded_queue_record_hashes
        )

        assert (
            len(
                report.excluded_queue_record_hashes
            )
            == 1
        )

        assert (
            report.source_queue_report_hash
            == source_report["report_hash"]
        )

        for work_item in report.work_items:
            payload = dict(
                work_item.to_dict()
            )

            digest = payload.pop(
                "work_item_hash"
            )

            assert digest == stable_hash(
                payload
            )

            assert work_item.work_item_id.startswith(
                "oia019-"
            )

            assert (
                "oia_018_queue_record_verified"
                in work_item.reason_codes
            )

            assert (
                "queue_position_preserved"
                in work_item.reason_codes
            )

            assert (
                "create_market_order"
                in work_item.prohibited_operations
            )

            assert (
                "handoff_to_qseries_execution"
                in work_item.prohibited_operations
            )

            assert (
                "research_output_deterministically_hashed"
                in work_item.completion_requirements
            )

        report_payload = dict(
            report.to_dict()
        )

        report_digest = report_payload.pop(
            "report_hash"
        )

        assert report_digest == stable_hash(
            report_payload
        )

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert (
            not report.trading_recommendations_allowed
        )
        assert not report.source_mutation_allowed
        assert (
            not report.market_order_creation_allowed
        )
        assert not report.funds_movement_allowed
        assert (
            not report.portfolio_mutation_allowed
        )
        assert (
            report.work_item_artifact_persistence_allowed
        )

        current_path = (
            work_item_directory
            / "current.json"
        )

        immutable_report_path = (
            work_item_directory
            / "reports"
            / (
                "work-item-report-"
                f"{report.report_hash}.json"
            )
        )

        first_item_path = (
            work_item_directory
            / "items"
            / f"{first.work_item_id}.json"
        )

        second_item_path = (
            work_item_directory
            / "items"
            / f"{second.work_item_id}.json"
        )

        assert current_path.exists()
        assert immutable_report_path.exists()
        assert first_item_path.exists()
        assert second_item_path.exists()

        first_current_bytes = (
            current_path.read_bytes()
        )

        first_report_bytes = (
            immutable_report_path.read_bytes()
        )

        first_item_bytes = (
            first_item_path.read_bytes()
        )

        replay = engine.materialize(
            generated_at=NOW,
            persist=True,
        )

        assert (
            replay.report_hash
            == report.report_hash
        )

        assert (
            replay.work_items[0].work_item_id
            == first.work_item_id
        )

        assert (
            replay.work_items[0].work_item_hash
            == first.work_item_hash
        )

        assert (
            current_path.read_bytes()
            == first_current_bytes
        )

        assert (
            immutable_report_path.read_bytes()
            == first_report_bytes
        )

        assert (
            first_item_path.read_bytes()
            == first_item_bytes
        )

        rendered = format_report(
            report
        )

        assert (
            "ORACLE QUALIFIED RESEARCH "
            "WORK-ITEM MATERIALIZATION"
            in rendered
        )

        assert "momentum|300" in rendered
        assert "oia019-" in rendered
        assert "NO SIGNALS" in rendered

        tampered = json.loads(
            (
                queue_directory
                / "current.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        tampered["records"][0][
            "priority_score"
        ] = "1.00000000"

        (
            queue_directory
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
            engine.materialize(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchWorkItemInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-018 queue report "
                "was not rejected."
            )

        write_queue_report(
            queue_directory,
            [
                make_queue_record(
                    source_rank=1,
                    queue_position=2,
                    key="invalid-position",
                    tier=TIER_1,
                    score="80.00000000",
                    queue_status=QUEUE_ADMITTED,
                    decisive_count=500,
                ),
            ],
            queue_capacity=2,
        )

        try:
            engine.materialize(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchWorkItemInvariantError:
            pass
        else:
            raise AssertionError(
                "Non-contiguous OIA-018 queue position "
                "was not rejected."
            )

    print(
        "[PASS] OIA-019 Oracle Qualified Research "
        "Work-Item Materialization Engine"
    )


if __name__ == "__main__":
    run_test()
