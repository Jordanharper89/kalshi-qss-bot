import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.market_rhythm_analyzer import MarketRhythmAnalyzer


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
            bid REAL,
            ask REAL,
            volume REAL,
            liquidity REAL,
            expiration TEXT
        )
    """)

    base = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(48):
        ts = base - timedelta(hours=i)
        exp = ts + timedelta(hours=(i % 12) + 1)

        rows.append((
            ts.isoformat(),
            f"TEST-{i}",
            "crypto" if i % 2 == 0 else "sports",
            40 + (i % 20),
            38 + (i % 10),
            42 + (i % 10),
            100 + i * 5,
            500 + i * 10,
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_021_market_rhythm_analyzer():
    db_path = Path("test_oi_021_history.sqlite3")
    build_test_db(db_path)

    analyzer = MarketRhythmAnalyzer(str(db_path))

    diagnostics = analyzer.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True

    snapshot = analyzer.analyze()
    assert snapshot["status"] == "ok"
    assert snapshot["rows_analyzed"] == 48
    assert snapshot["hourly_activity"]
    assert snapshot["daily_activity"]
    assert snapshot["weekly_activity"]
    assert snapshot["expiration_behavior"]
    assert snapshot["liquidity_curve"]
    assert snapshot["spread_curve"]
    assert snapshot["volume_curve"]
    assert snapshot["volatility_curve"]
    assert snapshot["category_patterns"]
    assert snapshot["category_patterns"]["crypto"]["records"] == 24
    assert snapshot["category_patterns"]["sports"]["records"] == 24

    insights = analyzer.oracle_insights()
    assert insights["read_only"] is True
    assert insights["execution_allowed"] is False
    assert insights["best_activity_hours"]

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-021 Market Rhythm Analyzer")
    print({
        "rows_analyzed": snapshot["rows_analyzed"],
        "categories": list(snapshot["category_patterns"].keys()),
        "top_activity_hours": insights["best_activity_hours"][:3],
    })


if __name__ == "__main__":
    test_oi_021_market_rhythm_analyzer()
