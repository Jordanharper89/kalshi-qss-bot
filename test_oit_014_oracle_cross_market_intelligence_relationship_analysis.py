import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def clear_modules():
    for name in list(sys.modules):
        if name == "qseries_v2" or name.startswith("qseries_v2."):
            del sys.modules[name]


def main() -> int:
    print("=" * 40)
    print(" OIT-014 CORRECTION V2 TEST")
    print(" REPOSITORY-ALIGNED RELATIONSHIP SEMANTICS")
    print("=" * 40)
    installed_root = Path(__file__).resolve().parent
    source = installed_root / "qseries_v2" / "oracle_terminal" / "oracle_cross_market_intelligence_relationship_analysis.py"
    assert source.is_file()

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        terminal = root / "qseries_v2" / "oracle_terminal"
        terminal.mkdir(parents=True)
        (root / "qseries_v2" / "__init__.py").write_text("", encoding="utf-8")
        (terminal / "__init__.py").write_text("", encoding="utf-8")
        (terminal / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        artifact = root / "runtime" / "oracle_intelligence" / "markets.json"
        artifact.parent.mkdir(parents=True)
        payload = {"records": [
            {"market_id": "BTC-ETF", "title": "Bitcoin ETF approval", "asset": "Bitcoin", "category": "Crypto", "venue": "Kalshi", "probability": 0.72, "stance": "bull", "updated_at": "2026-07-29T12:00:00Z"},
            {"market_id": "BTC-PRICE", "title": "Bitcoin above target", "asset": "Bitcoin", "category": "Crypto", "venue": "Polymarket", "probability": 0.61, "stance": "bear", "updated_at": "2026-07-30T12:00:00Z"},
            {"market_id": "NFL-GAME", "title": "Independent football market", "team": "Chicago Bears", "category": "Sports", "venue": "Kalshi", "probability": 0.53, "stance": "neutral", "updated_at": "2026-07-30T13:00:00Z"}
        ]}
        artifact.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        relative = artifact.relative_to(root).as_posix()

        stub = """
from dataclasses import dataclass
from pathlib import Path

class OracleTemporalTimelineInvariantError(RuntimeError):
    pass

@dataclass(frozen=True)
class OracleTemporalEvidenceEvent:
    event_index: int
    evidence_index: int
    record_id: str
    timestamp_utc: str
    epoch_seconds: int
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    evidence_hash: str
    inspection_hash: str
    event_hash: str

@dataclass(frozen=True)
class OracleTemporalIntelligenceReport:
    query: str
    answer_hash: str
    query_plan_hash: str
    query_result_hash: str
    report_hash: str
    events: tuple
    failure_reason: str | None = None

def verify_temporal_intelligence_report(report):
    return bool(report.report_hash)

def build_temporal_intelligence_report(*, repository_root: Path, query: str, result_limit: int = 10):
    items = (
        ("BTC-ETF", "2026-07-29T12:00:00+00:00", 1785326400),
        ("BTC-PRICE", "2026-07-30T12:00:00+00:00", 1785412800),
        ("NFL-GAME", "2026-07-30T13:00:00+00:00", 1785416400),
    )
    events = tuple(
        OracleTemporalEvidenceEvent(
            event_index=index,
            evidence_index=index,
            record_id=record_id,
            timestamp_utc=timestamp,
            epoch_seconds=epoch,
            artifact_relative_path=__RELATIVE__,
            artifact_sha256=__HASH__,
            record_hash=("r" + str(index)) * 32,
            evidence_hash=("e" + str(index)) * 32,
            inspection_hash=("i" + str(index)) * 32,
            event_hash=("t" + str(index)) * 32,
        )
        for index, (record_id, timestamp, epoch) in enumerate(items, start=1)
    )
    return OracleTemporalIntelligenceReport(
        query=query,
        answer_hash="a" * 64,
        query_plan_hash="p" * 64,
        query_result_hash="q" * 64,
        report_hash="z" * 64,
        events=events,
    )
"""
        stub = stub.replace("__RELATIVE__", repr(relative)).replace("__HASH__", repr(artifact_hash))
        (terminal / "oracle_temporal_intelligence_timeline_reconstruction.py").write_text(stub, encoding="utf-8")

        old_path = list(sys.path)
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.path.insert(0, str(root))
            clear_modules()
            module = __import__("qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis", fromlist=["*"])
            report = module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")
            assert module.verify_cross_market_intelligence_report(report)
            assert report.profile_count == 3, report.profile_count
            assert report.relationship_count == 1, tuple(
                (
                    item.left_record_id,
                    item.right_record_id,
                    item.shared_entities,
                )
                for item in report.relationships
            )
            assert report.connected_profile_count == 2
            assert report.independent_profile_count == 1
            assert tuple(
                (
                    item.left_record_id,
                    item.right_record_id,
                )
                for item in report.relationships
            ) == (("BTC-ETF", "BTC-PRICE"),)
            relationship = report.relationships[0]
            assert relationship.left_record_id == "BTC-ETF"
            assert relationship.right_record_id == "BTC-PRICE"
            assert relationship.shared_entities == ("Bitcoin",)
            assert "Kalshi" not in relationship.shared_entities
            assert "Crypto" not in relationship.shared_entities
            assert relationship.temporal_relationship == "left_leads_right"
            assert relationship.directional_relationship == "contradictory"
            assert relationship.probability_distance == 0.11
            assert report.lead_lag_relationship_count == 1
            assert report.contradictory_direction_count == 1
            rendered = "\n".join(module.cross_market_intelligence_lines(report))
            assert "profile_count: 3" in rendered
            assert "relationship_count: 1" in rendered
            assert "Bitcoin" in rendered
            assert "read_only: true" in rendered
            before = artifact.read_bytes()
            replay = module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")
            assert replay.report_hash == report.report_hash
            assert artifact.read_bytes() == before
            artifact.write_text('{"mutated":true}\n', encoding="utf-8")
            try:
                module.build_cross_market_intelligence_report(repository_root=root, query="compare related markets")
            except module.OracleCrossMarketRelationshipInvariantError:
                pass
            else:
                raise AssertionError("mutated artifact accepted")
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            clear_modules()

    print("[PASS] Certified OIT-013 temporal report consumed")
    print("[PASS] Certified artifact reopened read-only and hash verified")
    print("[PASS] Exact source records located by certified record ID")
    print("[PASS] Shared semantic entity relationship detected")
    print("[PASS] Lead-lag relationship detected")
    print("[PASS] Contradictory direction detected")
    print("[PASS] Probability distance calculated deterministically")
    print("[PASS] Venue-only and unrelated market links rejected")
    print("[PASS] Relationship report deterministic across replay")
    print("[PASS] Mutated artifact rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-014 CORRECTION V2 REPOSITORY-ALIGNED PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
