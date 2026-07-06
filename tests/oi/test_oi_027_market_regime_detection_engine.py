import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.market_regime_detection_engine import MarketRegimeDetectionEngine


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

    base = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(300):
        ts = base - timedelta(minutes=i * 10)
        exp = ts + timedelta(hours=(i % 10) + 1)

        rows.append((
            ts.isoformat(),
            f"REGIME-{i}",
            "crypto" if i % 2 == 0 else "sports",
            45 + (i % 20),
            43 + (i % 10),
            47 + (i % 10),
            1500 + (i * 8),
            3000 + (i * 12),
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_027_market_regime_detection_engine():
    db_path = Path("test_oi_027_history.sqlite3")
    build_test_db(db_path)

    engine = MarketRegimeDetectionEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "LIVE-REGIME",
        "category": "crypto",
        "timestamp": datetime(2026, 6, 29, 14, 30, tzinfo=timezone.utc).isoformat(),
        "expiration": datetime(2026, 6, 29, 17, 30, tzinfo=timezone.utc).isoformat(),
        "yes_price": 88,
        "bid": 86,
        "ask": 91,
        "volume": 9000,
        "liquidity": 12000,
    }

    packet = engine.detect_regime(live_market)
    assert packet["status"] == "ok"
    assert packet["rows_analyzed"] == 300
    assert packet["current_regime"]["name"]
    assert packet["current_regime"]["score"] >= 0
    assert packet["regime_scores"]
    assert packet["regime_features"]["sample_size"] > 0
    assert packet["oracle_context"]["context_type"] == "market_regime"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    context = engine.regime_context()
    assert context["status"] == "ok"
    assert context["current_regime"]["name"] == packet["current_regime"]["name"]
    assert context["read_only"] is True
    assert context["execution_allowed"] is False

    summary = engine.transition_summary()
    assert summary["transition_count"] >= 1
    assert summary["read_only"] is True
    assert summary["execution_allowed"] is False

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-027 Market Regime Detection Engine")
    print({
        "regime": packet["current_regime"]["name"],
        "score": packet["current_regime"]["score"],
        "confidence": packet["current_regime"]["confidence"],
        "transitions": summary["transition_count"],
    })


if __name__ == "__main__":
    test_oi_027_market_regime_detection_engine()
