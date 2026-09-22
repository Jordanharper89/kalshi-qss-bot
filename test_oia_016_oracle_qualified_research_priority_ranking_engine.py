from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_ranking_eligibility_gate import (
    ELIGIBLE,
    INELIGIBLE,
    PROVISIONAL,
    stable_hash as eligibility_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    ENGINE_ID,
    RANKING_POLICY_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchPriorityRankingEngine,
    QualifiedResearchPriorityRankingInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(2026, 7, 21, 4, 0, 0, tzinfo=timezone.utc)


def make_decision(
    *,
    dimension: str,
    key: str,
    status: str,
    decisive_count: int,
    win_rate: str,
    lower: str,
    upper: str,
    calibration_error: str,
    brier_score: str,
    reliability: str,
    resolution: str,
    evidence_sufficiency: str = "strong",
    sample_sufficiency: str = "established",
) -> dict:
    body = {
        "dimension": dimension,
        "key": key,
        "status": status,
        "decisive_count": decisive_count,
        "empirical_win_rate": win_rate,
        "confidence_lower_bound": lower,
        "confidence_upper_bound": upper,
        "calibration_error": calibration_error,
        "brier_score": brier_score,
        "reliability": reliability,
        "resolution": resolution,
        "evidence_sufficiency": evidence_sufficiency,
        "sample_sufficiency": sample_sufficiency,
        "reason_codes": ["test_fixture"],
        "calibration_bucket_hash": "a" * 64,
        "reliability_component_hash": "b" * 64,
        "confidence_component_hash": "c" * 64,
    }
    return {
        **body,
        "decision_hash": eligibility_hash(body),
    }


def write_eligibility_report(
    directory: Path,
    decisions: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-015",
        "engine_id": "OIA-015",
        "generated_at": NOW,
        "calibration_directory": "calibration",
        "reliability_directory": "reliability",
        "confidence_directory": "confidence",
        "eligibility_directory": str(directory),
        "matched_component_count": len(decisions),
        "eligible_count": sum(
            item["status"] == ELIGIBLE
            for item in decisions
        ),
        "provisional_count": sum(
            item["status"] == PROVISIONAL
            for item in decisions
        ),
        "ineligible_count": sum(
            item["status"] == INELIGIBLE
            for item in decisions
        ),
        "insufficient_evidence_count": 0,
        "decisions": decisions,
        "source_calibration_report_hash": "d" * 64,
        "source_reliability_report_hash": "e" * 64,
        "source_confidence_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "eligibility_artifact_persistence_allowed": True,
    }
    payload = {
        **body,
        "report_hash": eligibility_hash(body),
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
        eligibility_directory = root / "eligibility"
        ranking_directory = root / "ranking"

        strongest = make_decision(
            dimension="candidate_family_horizon",
            key="momentum|300",
            status=ELIGIBLE,
            decisive_count=600,
            win_rate="0.70000000",
            lower="0.66000000",
            upper="0.73800000",
            calibration_error="0.01000000",
            brier_score="0.21000000",
            reliability="0.00500000",
            resolution="0.05000000",
        )
        second = make_decision(
            dimension="candidate_family_horizon",
            key="reversion|900",
            status=ELIGIBLE,
            decisive_count=420,
            win_rate="0.64000000",
            lower="0.59000000",
            upper="0.68600000",
            calibration_error="0.03000000",
            brier_score="0.23000000",
            reliability="0.02000000",
            resolution="0.03000000",
        )
        provisional = make_decision(
            dimension="horizon",
            key="3600",
            status=PROVISIONAL,
            decisive_count=90,
            win_rate="0.60000000",
            lower="0.49000000",
            upper="0.70000000",
            calibration_error="0.02000000",
            brier_score="0.24000000",
            reliability="0.02000000",
            resolution="0.02000000",
            evidence_sufficiency="provisional",
            sample_sufficiency="provisional",
        )
        ineligible = make_decision(
            dimension="research_direction_horizon",
            key="no|300",
            status=INELIGIBLE,
            decisive_count=500,
            win_rate="0.42000000",
            lower="0.38000000",
            upper="0.46300000",
            calibration_error="0.12000000",
            brier_score="0.27000000",
            reliability="0.06000000",
            resolution="0.00000000",
        )

        source_report = write_eligibility_report(
            eligibility_directory,
            [
                second,
                ineligible,
                strongest,
                provisional,
            ],
        )

        engine = OracleQualifiedResearchPriorityRankingEngine(
            eligibility_directory=eligibility_directory,
            ranking_directory=ranking_directory,
        )

        report = engine.rank(
            generated_at=NOW,
            persist=True,
        )

        assert report.schema_version == SCHEMA_VERSION == "OIA-016"
        assert report.engine_id == ENGINE_ID == "OIA-016"
        assert report.ranking_policy_id == RANKING_POLICY_ID

        assert report.source_decision_count == 4
        assert report.qualified_decision_count == 2
        assert report.excluded_decision_count == 2
        assert report.ranking_count == 2

        assert report.rankings[0].rank == 1
        assert report.rankings[0].key == "momentum|300"
        assert report.rankings[1].rank == 2
        assert report.rankings[1].key == "reversion|900"

        assert (
            float(report.rankings[0].priority_score)
            > float(report.rankings[1].priority_score)
        )

        assert (
            report.rankings[0].source_eligibility_decision_hash
            == strongest["decision_hash"]
        )
        assert (
            report.rankings[1].source_eligibility_decision_hash
            == second["decision_hash"]
        )

        assert set(report.excluded_decision_hashes) == {
            provisional["decision_hash"],
            ineligible["decision_hash"],
        }

        for item in report.rankings:
            payload = dict(item.to_dict())
            digest = payload.pop("record_hash")
            assert digest == stable_hash(payload)

        report_payload = dict(report.to_dict())
        report_digest = report_payload.pop("report_hash")
        assert report_digest == stable_hash(report_payload)

        assert (
            report.source_eligibility_report_hash
            == source_report["report_hash"]
        )

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert not report.trading_recommendations_allowed
        assert not report.source_mutation_allowed
        assert report.ranking_artifact_persistence_allowed

        current_path = ranking_directory / "current.json"
        immutable_path = (
            ranking_directory
            / "reports"
            / f"ranking-{report.report_hash}.json"
        )
        assert current_path.exists()
        assert immutable_path.exists()

        first_current = current_path.read_bytes()
        first_immutable = immutable_path.read_bytes()

        replay = engine.rank(
            generated_at=NOW,
            persist=True,
        )
        assert replay.report_hash == report.report_hash
        assert current_path.read_bytes() == first_current
        assert immutable_path.read_bytes() == first_immutable

        rendered = format_report(report)
        assert "ORACLE QUALIFIED RESEARCH PRIORITY RANKING" in rendered
        assert "momentum|300" in rendered
        assert "NO SIGNALS" in rendered

        tampered = json.loads(
            (
                eligibility_directory / "current.json"
            ).read_text(encoding="utf-8")
        )
        tampered["eligible_count"] = 999
        (
            eligibility_directory / "current.json"
        ).write_text(
            json.dumps(tampered, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            engine.rank(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchPriorityRankingInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-015 report was not rejected."
            )

    print(
        "[PASS] OIA-016 Oracle Qualified Research "
        "Priority Ranking Engine"
    )


if __name__ == "__main__":
    run_test()
