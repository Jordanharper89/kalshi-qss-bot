import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.market_relationship_engine import MarketRelationshipEngine


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
            volume REAL,
            liquidity REAL
        )
    """)

    base = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)
    rows = []

    for i in range(80):
        ts = base + timedelta(minutes=i)

        btc = 40 + i * 0.25
        eth = 30 + i * 0.20
        gold = 70 - i * 0.15
        oil = 50 + ((i % 5) * 0.1)

        rows.extend([
            (ts.isoformat(), "BTC", "crypto", btc, 1000 + i, 3000 + i),
            (ts.isoformat(), "ETH", "crypto", eth, 900 + i, 2500 + i),
            (ts.isoformat(), "GOLD", "macro", gold, 700 + i, 1800 + i),
            (ts.isoformat(), "OIL", "macro", oil, 600 + i, 1600 + i),
        ])

    cur.executemany("INSERT INTO market_history VALUES (?, ?, ?, ?, ?, ?)", rows)

    conn.commit()
    conn.close()


def test_oi_037_market_relationship_engine():
    db_path = Path("test_oi_037_history.sqlite3")
    build_test_db(db_path)

    engine = MarketRelationshipEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_markets = [
        {"ticker": "BTC", "category": "crypto", "yes_price": 62},
        {"ticker": "ETH", "category": "crypto", "yes_price": 55},
    ]

    packet = engine.correlation_snapshot(live_markets=live_markets)

    assert packet["status"] == "ok"
    assert packet["rows_analyzed"] == 320
    assert packet["market_correlations"]["pair_count"] > 0
    assert packet["category_correlations"]["pair_count"] > 0
    assert packet["lead_lag"]["relationship_count"] >= 0
    assert packet["influence_scores"]
    assert packet["live_context"]["status"] == "ok"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    market_corr = engine.market_correlations()
    assert market_corr["pair_count"] > 0

    category_corr = engine.category_correlations()
    assert category_corr["pair_count"] > 0

    influence = engine.influence_score()
    assert influence

    latest = engine.latest()
    assert latest["status"] == "ok"

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-037 Market Relationship Engine")
    print({
        "rows_analyzed": packet["rows_analyzed"],
        "top_market_pair": packet["market_correlations"]["pairs"][0],
        "top_influence": list(packet["influence_scores"].values())[0],
        "live_relationships": len(packet["live_context"]["relevant_relationships"]),
    })


if __name__ == "__main__":
    test_oi_037_market_relationship_engine()
