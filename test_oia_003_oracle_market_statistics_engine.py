from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleMarketStatisticsEngine,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 4, 0, 0, tzinfo=timezone.utc)


class Cursor:
    def __init__(self, mode):
        self.mode = mode
        self.closed = False

    def execute(self, sql, params=None):
        upper = sql.upper()
        assert "INSERT" not in upper and "UPDATE" not in upper and "DELETE" not in upper
        if self.mode == "quality":
            assert "oia002:market_quality" in sql
            assert params == (50,)
        else:
            assert "oia003:accepted_market_history" in sql
            assert params == (["KXACTIVE"], 100)

    def fetchall(self):
        if self.mode == "quality":
            return [
                ("KXACTIVE", 4, datetime(2026, 7, 20, 3, 59, 50, tzinfo=timezone.utc), "0.40", "0.42", "0.41"),
                ("KXSTALE", 4, datetime(2026, 7, 20, 3, 30, 0, tzinfo=timezone.utc), "0.50", "0.54", "0.52"),
                ("KXCROSS", 4, datetime(2026, 7, 20, 3, 59, 55, tzinfo=timezone.utc), "0.70", "0.60", "0.65"),
            ]
        return [
            ("KXACTIVE", datetime(2026, 7, 20, 3, 57, 0, tzinfo=timezone.utc), 1, "0.38", "0.42", "0.40", "100", "500"),
            ("KXACTIVE", datetime(2026, 7, 20, 3, 58, 0, tzinfo=timezone.utc), 2, "0.39", "0.43", "0.41", "120", "550"),
            ("KXACTIVE", datetime(2026, 7, 20, 3, 59, 0, tzinfo=timezone.utc), 3, "0.40", "0.42", "0.41", "140", "600"),
            ("KXACTIVE", datetime(2026, 7, 20, 4, 0, 0, tzinfo=timezone.utc), 4, "0.43", "0.45", "0.44", "160", "650"),
        ]

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, mode):
        self.cursor_value = Cursor(mode)
        self.closed = False

    def cursor(self):
        return self.cursor_value

    def close(self):
        self.closed = True


def run_test():
    modes = iter(("quality", "statistics"))
    connections = []

    def factory():
        connection = Connection(next(modes))
        connections.append(connection)
        return connection

    engine = OracleMarketStatisticsEngine(
        connection_factory=factory,
        stale_after_seconds=300,
        minimum_observations=3,
        market_limit=50,
        history_limit_per_market=100,
    )
    report = engine.analyze(analyzed_at=NOW)
    assert report.schema_version == SCHEMA_VERSION == "OIA-003"
    assert report.engine_id == ENGINE_ID == "OIA-003"
    assert report.quality_market_count == 3
    assert report.accepted_market_count == 1
    assert report.statistics_market_count == 1
    assert report.total_observations_analyzed == 4
    assert report.total_price_transitions == 2
    market = report.markets[0]
    assert market.market_id == "KXACTIVE"
    assert market.observation_count == 4
    assert market.priced_observation_count == 4
    assert market.history_duration_seconds == 180.0
    assert market.average_update_interval_seconds == 60.0
    assert market.price_transition_count == 2
    assert round(market.transition_rate, 6) == round(2 / 3, 6)
    assert market.first_price_dollars == "0.40"
    assert market.latest_price_dollars == "0.44"
    assert market.minimum_price_dollars == "0.40"
    assert market.maximum_price_dollars == "0.44"
    assert market.price_range_dollars == "0.04"
    assert market.absolute_price_change_dollars == "0.04"
    assert market.average_spread_dollars == "0.03"
    assert market.maximum_spread_dollars == "0.04"
    assert market.latest_volume_fp == "160"
    assert market.latest_liquidity_dollars == "650"
    market_payload = dict(market.to_dict())
    market_hash = market_payload.pop("statistics_hash")
    assert market_hash == stable_hash(market_payload)
    report_payload = dict(report.to_dict())
    report_hash = report_payload.pop("report_hash")
    assert report_hash == stable_hash(report_payload)
    assert report.read_only is True
    assert report.signals_allowed is False
    assert report.raw_corpus_mutation_allowed is False
    rendered = format_report(report)
    assert "KXACTIVE" in rendered and "Price transitions:" in rendered
    assert all(connection.closed for connection in connections)
    assert all(connection.cursor_value.closed for connection in connections)
    print("[PASS] OIA-003 Oracle Market Statistics Engine")


if __name__ == "__main__":
    run_test()
