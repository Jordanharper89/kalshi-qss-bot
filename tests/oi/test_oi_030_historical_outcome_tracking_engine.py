import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.historical_outcome_tracking_engine import HistoricalOutcomeTrackingEngine


def build_test_db(path: Path):
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE market_history (
            timestamp TEXT,
            ticker TEXT,
            category TEXT,
            yes_price REAL,
            no_price REAL,
            bid REAL,
            ask REAL,
            volume REAL,
            liquidity REAL
        )
    """)

    base = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)
    rows = []

    for ticker_num in range(20):
        ticker = f"TEST-{ticker_num}"
        category = "crypto" if ticker_num < 12 else "sports"

        for step in range(40):
            ts = base + timedelta(minutes=5 * step)
            yes_price = 45 + (ticker_num % 5) + (step * 0.25)
            no_price = 100 - yes_price
            bid = yes_price - 2
            ask = yes_price + 2
            volume = 1000 + ticker_num * 20 + step * 10
            liquidity = 2500 + ticker_num * 30 + step * 15

            rows.append((
                ts.isoformat(),
                ticker,
                category,
                yes_price,
                no_price,
                bid,
                ask,
                volume,
                liquidity,
            ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_030_historical_outcome_tracking_engine():
    db_path = Path("test_oi_030_history.sqlite3")
    build_test_db(db_path)

    engine = HistoricalOutcomeTrackingEngine(
        str(db_path),
        horizons_minutes=[5, 15, 30, 60],
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "LIVE-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T12:00:00+00:00",
        "yes_price": 47,
        "no_price": 53,
        "bid": 45,
        "ask": 49,
        "volume": 1100,
        "liquidity": 2600,
    }

    packet = engine.forward_outcomes(live_market)
    assert packet["status"] == "ok"
    assert packet["matches_found"] > 0
    assert packet["horizon_statistics"]
    assert packet["horizon_statistics"]["5"]["observations"] > 0
    assert packet["horizon_statistics"]["15"]["yes_price_change"]["mean"] > 0
    assert packet["outcome_curve"]["curve"]
    assert packet["confidence"]["score"] > 0
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    curve = engine.outcome_curve(live_market)
    assert len(curve["curve"]) == 4

    stats = engine.horizon_statistics(live_market)
    assert "60" in stats

    pattern = engine.analyze_pattern()
    assert pattern["status"] == "ok"
    assert pattern["outcome_curve"]

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-030 Historical Outcome Tracking Engine")
    print({
        "matches_found": packet["matches_found"],
        "confidence": packet["confidence"],
        "curve_points": len(packet["outcome_curve"]["curve"]),
        "horizon_15_yes_mean": packet["horizon_statistics"]["15"]["yes_price_change"]["mean"],
    })


if __name__ == "__main__":
    test_oi_030_historical_outcome_tracking_engine()
