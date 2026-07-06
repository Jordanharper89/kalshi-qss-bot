import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.historical_pattern_recognition_engine import HistoricalPatternRecognitionEngine


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
    for i in range(160):
        ts = base - timedelta(hours=i % 72)
        category = "crypto" if i < 110 else "sports"
        exp = ts + timedelta(hours=(i % 8) + 1)

        if category == "crypto":
            yes_price = 48 + (i % 8)
            no_price = 52 - (i % 8)
            volume = 900 + (i * 8)
            liquidity = 2500 + (i * 12)
            bid = yes_price - 2
            ask = yes_price + 2
        else:
            yes_price = 30 + (i % 15)
            no_price = 70 - (i % 15)
            volume = 300 + (i * 3)
            liquidity = 800 + (i * 5)
            bid = yes_price - 3
            ask = yes_price + 3

        rows.append((
            ts.isoformat(),
            f"TEST-{i}",
            category,
            yes_price,
            no_price,
            bid,
            ask,
            volume,
            liquidity,
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_025_historical_pattern_recognition_engine():
    db_path = Path("test_oi_025_history.sqlite3")
    build_test_db(db_path)

    engine = HistoricalPatternRecognitionEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "LIVE-CRYPTO",
        "category": "crypto",
        "timestamp": datetime(2026, 6, 29, 14, 30, tzinfo=timezone.utc).isoformat(),
        "expiration": datetime(2026, 6, 29, 19, 30, tzinfo=timezone.utc).isoformat(),
        "yes_price": 52,
        "no_price": 48,
        "bid": 50,
        "ask": 54,
        "volume": 1200,
        "liquidity": 3000,
    }

    result = engine.find_similar_markets(live_market, top_n=8)
    assert result["status"] == "ok"
    assert result["live_market"]["category"] == "crypto"
    assert result["top_matches"]
    assert len(result["top_matches"]) == 8
    assert result["top_matches"][0]["similarity"] >= result["top_matches"][-1]["similarity"]
    assert result["pattern_summary"]["occurrences"] > 0
    assert result["confidence"]["sample_size"] > 0
    assert result["read_only"] is True
    assert result["execution_allowed"] is False

    top = engine.top_patterns()
    assert top["status"] == "ok"
    assert top["patterns"]

    stats = engine.pattern_statistics()
    assert stats["status"] == "ok"
    assert stats["statistics"]["occurrences"] > 0

    compare = engine.compare_pattern(live_market)
    assert compare["status"] == "ok"
    assert compare["read_only"] is True
    assert compare["execution_allowed"] is False

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-025 Historical Pattern Recognition Engine")
    print({
        "matches_found": result["matches_found"],
        "top_similarity": result["top_matches"][0]["similarity"],
        "confidence": result["confidence"]["label"],
        "sample_size": result["confidence"]["sample_size"],
    })


if __name__ == "__main__":
    test_oi_025_historical_pattern_recognition_engine()
