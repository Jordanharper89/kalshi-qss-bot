import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.historical_market_baseline_engine import HistoricalMarketBaselineEngine


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
            liquidity REAL,
            expiration TEXT
        )
    """)

    base = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(120):
        ts = base - timedelta(hours=i % 48)
        category = "crypto" if i < 80 else "sports"
        exp = ts + timedelta(hours=(i % 12) + 1)

        rows.append((
            ts.isoformat(),
            f"TEST-{i}",
            category,
            45 + (i % 10),
            55 - (i % 10),
            43 + (i % 5),
            47 + (i % 5),
            100 + i,
            1000 + (i * 10),
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_024_historical_market_baseline_engine():
    db_path = Path("test_oi_024_history.sqlite3")
    build_test_db(db_path)

    engine = HistoricalMarketBaselineEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    baseline = engine.get_baseline()
    assert baseline["status"] == "ok"
    assert baseline["rows_analyzed"] == 120
    assert baseline["rolling_windows"]["last_24h"]["records"] > 0
    assert baseline["rolling_windows"]["last_7d"]["records"] == 120
    assert baseline["category_baselines"]["crypto"]["records"] == 80
    assert baseline["category_baselines"]["sports"]["records"] == 40
    assert baseline["hourly_baselines"]
    assert baseline["weekday_baselines"]
    assert baseline["expiration_baselines"]
    assert baseline["read_only"] is True
    assert baseline["execution_allowed"] is False

    crypto_baseline = engine.category_baseline("crypto")
    assert crypto_baseline["records"] == 80
    assert crypto_baseline["metrics"]["liquidity"]["mean"] > 0
    assert crypto_baseline["metrics"]["spread"]["std"] >= 0

    hourly_baseline = engine.hourly_baseline("14")
    assert "metrics" in hourly_baseline

    live_market = {
        "ticker": "TEST-LIVE",
        "category": "crypto",
        "timestamp": datetime(2026, 6, 29, 14, 30, tzinfo=timezone.utc).isoformat(),
        "expiration": datetime(2026, 6, 29, 18, 30, tzinfo=timezone.utc).isoformat(),
        "yes_price": 90,
        "no_price": 10,
        "bid": 88,
        "ask": 92,
        "volume": 5000,
        "liquidity": 10000,
    }

    comparison = engine.compare_live_market(live_market)
    assert comparison["status"] == "ok"
    assert comparison["market"]["category"] == "crypto"
    assert comparison["comparisons"]["category"]["liquidity"]["current"] == 10000
    assert comparison["abnormality_score"]["metrics_checked"] > 0
    assert comparison["read_only"] is True
    assert comparison["execution_allowed"] is False

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-024 Historical Market Baseline Engine")
    print({
        "rows_analyzed": baseline["rows_analyzed"],
        "categories": list(baseline["category_baselines"].keys()),
        "comparison_label": comparison["abnormality_score"]["label"],
        "comparison_score": comparison["abnormality_score"]["score"],
    })


if __name__ == "__main__":
    test_oi_024_historical_market_baseline_engine()
