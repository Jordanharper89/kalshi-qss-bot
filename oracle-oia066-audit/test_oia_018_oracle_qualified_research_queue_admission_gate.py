from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    QUALIFIED,
    RANKING_POLICY_ID,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
    stable_hash as tier_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import (
    CAPACITY_DEFERRED,
    ENGINE_ID,
    QUEUE_ADMITTED,
    QUEUE_POLICY_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchQueueAdmissionGate,
    QualifiedResearchQueueAdmissionInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    6,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_tier_record(
    *,
    rank: int,
    key: str,
    score: str,
    tier: str,
    decisive_count: int,
) -> dict:
    body = {
        "rank": rank,
        "dimension": "candidate_family_horizon",
        "key": key,
        "qualification_status": QUALIFIED,
        "tier_status": ADMITTED,
        "tier": tier,
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
        "reason_codes": [
            "oia_016_qualified_ranking_verified",
            "source_rank_preserved",
            "deterministic_tier_policy_applied",
            "research_classification_only",
        ],
        "source_eligibility_decision_hash": (
            f"{rank:064x}"[-64:]
        ),
        "source_ranking_record_hash": (
            f"{rank + 100:064x}"[-64:]
        ),
    }

    return {
        **body,
        "tier_record_hash": tier_hash(body),
    }


def write_tier_report(
    directory: Path,
    records: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-017",
        "engine_id": "OIA-017",
        "generated_at": NOW,
        "ranking_directory": "ranking",
        "tier_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "source_ranking_count": len(records),
        "admitted_count": len(records),
        "denied_count": 0,
        "tier_1_count": sum(
            record["tier"] == TIER_1
            for record in records
        ),
        "tier_2_count": sum(
            record["tier"] == TIER_2
            for record in records
        ),
        "tier_3_count": sum(
            record["tier"] == TIER_3
            for record in records
        ),
        "records": records,
        "source_ranking_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "tier_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": tier_hash(body),
    }

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (directory / "current.json").write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: value.isoformat(),
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        tier_directory = root / "tiers"
        queue_directory = root / "queue"

        source_records = [
            make_tier_record(
                rank=1,
                key="momentum|300",
                score="82.50000000",
                tier=TIER_1,
                decisive_count=700,
            ),
            make_tier_record(
                rank=2,
                key="reversion|900",
                score="63.25000000",
                tier=TIER_2,
                decisive_count=500,
            ),
            make_tier_record(
                rank=3,
                key="momentum|3600",
                score="49.75000000",
                tier=TIER_3,
                decisive_count=350,
            ),
        ]

        source_report = write_tier_report(
            tier_directory,
            source_records,
        )

        gate = OracleQualifiedResearchQueueAdmissionGate(
            tier_directory=tier_directory,
            queue_directory=queue_directory,
            queue_capacity=2,
        )

        report = gate.evaluate(
            generated_at=NOW,
            persist=True,
        )

        assert report.schema_version == SCHEMA_VERSION == "OIA-018"
        assert report.engine_id == ENGINE_ID == "OIA-018"
        assert report.ranking_policy_id == RANKING_POLICY_ID
        assert report.tier_policy_id == TIER_POLICY_ID
        assert report.queue_policy_id == QUEUE_POLICY_ID

        assert report.queue_capacity == 2
        assert report.source_tier_record_count == 3
        assert report.queue_admitted_count == 2
        assert report.capacity_deferred_count == 1
        assert report.queue_denied_count == 0

        assert report.tier_1_admitted_count == 1
        assert report.tier_2_admitted_count == 1
        assert report.tier_3_admitted_count == 0

        assert report.records[0].source_rank == 1
        assert report.records[0].queue_position == 1
        assert report.records[0].queue_status == QUEUE_ADMITTED
        assert report.records[0].tier == TIER_1
        assert report.records[0].key == "momentum|300"

        assert report.records[1].source_rank == 2
        assert report.records[1].queue_position == 2
        assert report.records[1].queue_status == QUEUE_ADMITTED
        assert report.records[1].tier == TIER_2
        assert report.records[1].key == "reversion|900"

        assert report.records[2].source_rank == 3
        assert report.records[2].queue_position is None
        assert (
            report.records[2].queue_status
            == CAPACITY_DEFERRED
        )
        assert report.records[2].tier == TIER_3
        assert report.records[2].key == "momentum|3600"

        assert [
            record.source_tier_record_hash
            for record in report.records
        ] == [
            record["tier_record_hash"]
            for record in source_records
        ]

        assert [
            record.source_ranking_record_hash
            for record in report.records
        ] == [
            record["source_ranking_record_hash"]
            for record in source_records
        ]

        assert [
            record.source_eligibility_decision_hash
            for record in report.records
        ] == [
            record["source_eligibility_decision_hash"]
            for record in source_records
        ]

        assert (
            report.source_tier_report_hash
            == source_report["report_hash"]
        )

        for record in report.records:
            payload = dict(record.to_dict())
            digest = payload.pop("queue_record_hash")

            assert digest == stable_hash(payload)
            assert (
                "oia_017_tier_record_verified"
                in record.reason_codes
            )
            assert (
                "source_rank_preserved"
                in record.reason_codes
            )
            assert (
                "source_tier_preserved"
                in record.reason_codes
            )
            assert (
                "research_scheduling_only"
                in record.reason_codes
            )

        report_payload = dict(report.to_dict())
        report_digest = report_payload.pop("report_hash")

        assert report_digest == stable_hash(report_payload)

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert not report.trading_recommendations_allowed
        assert not report.source_mutation_allowed
        assert report.queue_artifact_persistence_allowed

        current_path = queue_directory / "current.json"

        immutable_path = (
            queue_directory
            / "reports"
            / f"queue-report-{report.report_hash}.json"
        )

        assert current_path.exists()
        assert immutable_path.exists()

        first_current_bytes = current_path.read_bytes()
        first_immutable_bytes = immutable_path.read_bytes()

        replay = gate.evaluate(
            generated_at=NOW,
            persist=True,
        )

        assert replay.report_hash == report.report_hash
        assert current_path.read_bytes() == first_current_bytes
        assert immutable_path.read_bytes() == first_immutable_bytes

        rendered = format_report(report)

        assert (
            "ORACLE QUALIFIED RESEARCH QUEUE ADMISSION"
            in rendered
        )
        assert "momentum|300" in rendered
        assert "capacity_deferred" in rendered
        assert "NO SIGNALS" in rendered

        zero_capacity_gate = (
            OracleQualifiedResearchQueueAdmissionGate(
                tier_directory=tier_directory,
                queue_directory=root / "zero-capacity",
                queue_capacity=0,
            )
        )

        zero_capacity_report = zero_capacity_gate.evaluate(
            generated_at=NOW,
            persist=False,
        )

        assert zero_capacity_report.queue_admitted_count == 0
        assert zero_capacity_report.capacity_deferred_count == 3

        tampered = json.loads(
            (tier_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )

        tampered["records"][0]["priority_score"] = "1.00000000"

        (tier_directory / "current.json").write_text(
            json.dumps(
                tampered,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        try:
            gate.evaluate(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchQueueAdmissionInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-017 tier report was not rejected."
            )

        write_tier_report(
            tier_directory,
            [
                make_tier_record(
                    rank=1,
                    key="first",
                    score="60.00000000",
                    tier=TIER_2,
                    decisive_count=400,
                ),
                make_tier_record(
                    rank=2,
                    key="second",
                    score="80.00000000",
                    tier=TIER_1,
                    decisive_count=500,
                ),
            ],
        )

        try:
            gate.evaluate(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchQueueAdmissionInvariantError:
            pass
        else:
            raise AssertionError(
                "Out-of-order OIA-017 records were not rejected."
            )

    print(
        "[PASS] OIA-018 Oracle Qualified Research "
        "Queue Admission Gate"
    )


if __name__ == "__main__":
    run_test()
