from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    QUALIFIED,
    RANKING_POLICY_ID,
    stable_hash as ranking_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import (
    ADMITTED,
    ENGINE_ID,
    SCHEMA_VERSION,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_POLICY_ID,
    OracleQualifiedResearchPriorityTierAssignmentGate,
    QualifiedResearchPriorityTierInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(
    2026,
    7,
    21,
    5,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_ranking_record(
    *,
    rank: int,
    key: str,
    score: str,
    decisive_count: int,
) -> dict:
    body = {
        "rank": rank,
        "qualification_status": QUALIFIED,
        "dimension": "candidate_family_horizon",
        "key": key,
        "decisive_count": decisive_count,
        "empirical_win_rate": "0.65000000",
        "confidence_lower_bound": "0.59000000",
        "confidence_upper_bound": "0.70000000",
        "calibration_error": "0.02000000",
        "brier_score": "0.22000000",
        "reliability": "0.01000000",
        "resolution": "0.04000000",
        "evidence_sufficiency": "strong",
        "sample_sufficiency": "established",
        "confidence_edge": "0.18000000",
        "calibration_quality": "0.80000000",
        "reliability_quality": "0.80000000",
        "resolution_quality": "0.40000000",
        "sample_strength": "1.00000000",
        "priority_score": score,
        "ranking_policy_id": RANKING_POLICY_ID,
        "reason_codes": [
            "oia_015_eligible",
            "deterministic_research_priority_scored",
        ],
        "source_eligibility_decision_hash": (
            f"{rank:064x}"[-64:]
        ),
    }

    return {
        **body,
        "record_hash": ranking_hash(body),
    }


def write_ranking_report(
    directory: Path,
    records: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-016",
        "engine_id": "OIA-016",
        "generated_at": NOW,
        "eligibility_directory": "eligibility",
        "ranking_directory": str(directory),
        "ranking_policy_id": RANKING_POLICY_ID,
        "source_decision_count": len(records) + 1,
        "qualified_decision_count": len(records),
        "excluded_decision_count": 1,
        "ranking_count": len(records),
        "rankings": records,
        "excluded_decision_hashes": ["f" * 64],
        "source_eligibility_report_hash": "e" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "ranking_artifact_persistence_allowed": True,
    }

    payload = {
        **body,
        "report_hash": ranking_hash(body),
    }

    directory.mkdir(parents=True, exist_ok=True)
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
        ranking_directory = root / "ranking"
        tier_directory = root / "tiers"

        source_records = [
            make_ranking_record(
                rank=1,
                key="momentum|300",
                score="82.50000000",
                decisive_count=700,
            ),
            make_ranking_record(
                rank=2,
                key="reversion|900",
                score="63.25000000",
                decisive_count=500,
            ),
            make_ranking_record(
                rank=3,
                key="momentum|3600",
                score="49.75000000",
                decisive_count=350,
            ),
        ]

        source_report = write_ranking_report(
            ranking_directory,
            source_records,
        )

        gate = OracleQualifiedResearchPriorityTierAssignmentGate(
            ranking_directory=ranking_directory,
            tier_directory=tier_directory,
        )

        report = gate.evaluate(
            generated_at=NOW,
            persist=True,
        )

        assert report.schema_version == SCHEMA_VERSION == "OIA-017"
        assert report.engine_id == ENGINE_ID == "OIA-017"
        assert report.ranking_policy_id == RANKING_POLICY_ID
        assert report.tier_policy_id == TIER_POLICY_ID

        assert report.source_ranking_count == 3
        assert report.admitted_count == 3
        assert report.denied_count == 0
        assert report.tier_1_count == 1
        assert report.tier_2_count == 1
        assert report.tier_3_count == 1

        assert report.records[0].rank == 1
        assert report.records[0].tier == TIER_1
        assert report.records[0].tier_status == ADMITTED
        assert report.records[0].key == "momentum|300"

        assert report.records[1].rank == 2
        assert report.records[1].tier == TIER_2
        assert report.records[1].key == "reversion|900"

        assert report.records[2].rank == 3
        assert report.records[2].tier == TIER_3
        assert report.records[2].key == "momentum|3600"

        assert [
            record.source_ranking_record_hash
            for record in report.records
        ] == [
            record["record_hash"]
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
            report.source_ranking_report_hash
            == source_report["report_hash"]
        )

        for record in report.records:
            payload = dict(record.to_dict())
            digest = payload.pop("tier_record_hash")
            assert digest == stable_hash(payload)
            assert "source_rank_preserved" in record.reason_codes
            assert (
                "research_classification_only"
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
        assert report.tier_artifact_persistence_allowed

        current_path = tier_directory / "current.json"
        immutable_path = (
            tier_directory
            / "reports"
            / f"tier-report-{report.report_hash}.json"
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
            "ORACLE QUALIFIED RESEARCH PRIORITY TIER ASSIGNMENT"
            in rendered
        )
        assert "momentum|300" in rendered
        assert "tier_1" in rendered
        assert "NO SIGNALS" in rendered

        tampered = json.loads(
            (ranking_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["rankings"][0]["priority_score"] = "1.00000000"

        (ranking_directory / "current.json").write_text(
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
        except QualifiedResearchPriorityTierInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-016 ranking report was not rejected."
            )

        write_ranking_report(
            ranking_directory,
            [
                make_ranking_record(
                    rank=1,
                    key="first",
                    score="60.00000000",
                    decisive_count=400,
                ),
                make_ranking_record(
                    rank=2,
                    key="second",
                    score="80.00000000",
                    decisive_count=500,
                ),
            ],
        )

        try:
            gate.evaluate(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchPriorityTierInvariantError:
            pass
        else:
            raise AssertionError(
                "Out-of-order OIA-016 ranking was not rejected."
            )

    print(
        "[PASS] OIA-017 Oracle Qualified Research "
        "Priority Tier Assignment Gate"
    )


if __name__ == "__main__":
    run_test()
