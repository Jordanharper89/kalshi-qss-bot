from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_corpus_quality_analyzer import (
    ACCEPTED,
    QUARANTINED,
    REJECTED,
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleCorpusQualityAnalyzer,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 3, 0, 0, tzinfo=timezone.utc)


class Cursor:
    def __init__(self):
        self.closed = False

    def execute(self, sql, params=None):
        upper = sql.upper()
        assert "INSERT" not in upper and "UPDATE" not in upper and "DELETE" not in upper
        assert "oia002:market_quality" in sql
        assert params == (50,)

    def fetchall(self):
        return [
            ("KXGOOD", 12, datetime(2026, 7, 20, 2, 59, 30, tzinfo=timezone.utc), "0.41", "0.43", "0.42"),
            ("KXSTALE", 12, datetime(2026, 7, 20, 2, 40, 0, tzinfo=timezone.utc), "0.50", "0.52", "0.51"),
            ("KXNEW", 1, datetime(2026, 7, 20, 2, 59, 40, tzinfo=timezone.utc), "0.20", "0.22", "0.21"),
            ("KXCROSS", 7, datetime(2026, 7, 20, 2, 59, 45, tzinfo=timezone.utc), "0.65", "0.61", "0.63"),
            ("KXMISSING", 5, datetime(2026, 7, 20, 2, 59, 50, tzinfo=timezone.utc), None, None, None),
        ]

    def close(self):
        self.closed = True


class Connection:
    def __init__(self):
        self.cursor_value = Cursor()
        self.closed = False

    def cursor(self):
        return self.cursor_value

    def close(self):
        self.closed = True


def run_test():
    connections = []

    def factory():
        connection = Connection()
        connections.append(connection)
        return connection

    analyzer = OracleCorpusQualityAnalyzer(
        connection_factory=factory,
        stale_after_seconds=300,
        minimum_observations=3,
        market_limit=50,
    )
    report = analyzer.analyze(analyzed_at=NOW)
    assert report.schema_version == SCHEMA_VERSION == "OIA-002"
    assert report.engine_id == ENGINE_ID == "OIA-002"
    assert report.market_count == 5
    assert report.accepted_count == 1
    assert report.quarantined_count == 2
    assert report.rejected_count == 2
    by_id = {item.market_id: item for item in report.markets}
    assert by_id["KXGOOD"].status == ACCEPTED
    assert by_id["KXSTALE"].status == QUARANTINED
    assert "stale_market" in by_id["KXSTALE"].reason_codes
    assert by_id["KXNEW"].status == QUARANTINED
    assert "insufficient_history" in by_id["KXNEW"].reason_codes
    assert by_id["KXCROSS"].status == REJECTED
    assert "crossed_spread" in by_id["KXCROSS"].reason_codes
    assert by_id["KXMISSING"].status == REJECTED
    assert "missing_price" in by_id["KXMISSING"].reason_codes
    for record in report.markets:
        payload = dict(record.to_dict())
        expected = payload.pop("quality_hash")
        assert expected == stable_hash(payload)
    report_payload = dict(report.to_dict())
    expected_report_hash = report_payload.pop("report_hash")
    assert expected_report_hash == stable_hash(report_payload)
    assert report.read_only is True
    assert report.raw_corpus_mutation_allowed is False
    assert report.execution_allowed is False
    rendered = format_report(report)
    assert "KXGOOD" in rendered and "Acceptance rate:" in rendered
    assert connections[0].closed is True
    assert connections[0].cursor_value.closed is True
    print("[PASS] OIA-002 Oracle Corpus Quality Analyzer")


if __name__ == "__main__":
    run_test()
