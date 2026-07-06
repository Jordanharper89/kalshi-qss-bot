"""
Oracle Database Layer

Purpose:
- Manage Oracle SQLite database.
- Store markets, snapshots, trades, features, signals.
- Store run history and data quality reports.
"""

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "oracle_data.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS markets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE NOT NULL,
        market_title TEXT,
        category TEXT,
        expiration_time TEXT,
        status TEXT,
        yes_price REAL,
        no_price REAL,
        volume INTEGER,
        open_interest INTEGER,
        raw_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_book_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        best_yes_bid REAL,
        best_yes_ask REAL,
        best_no_bid REAL,
        best_no_ask REAL,
        spread REAL,
        yes_bid_depth REAL,
        yes_ask_depth REAL,
        no_bid_depth REAL,
        no_ask_depth REAL,
        order_imbalance REAL,
        raw_json TEXT,
        snapshot_time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        trade_time TEXT,
        price REAL,
        size INTEGER,
        side TEXT,
        raw_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        snapshot_time TEXT DEFAULT CURRENT_TIMESTAMP,
        market_probability REAL,
        liquidity_score REAL,
        spread_score REAL,
        volatility_score REAL,
        momentum_score REAL,
        order_book_imbalance REAL,
        behavioral_bias_score REAL,
        time_decay_score REAL,
        market_efficiency_score REAL,
        raw_json TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        signal_time TEXT DEFAULT CURRENT_TIMESTAMP,
        market_title TEXT,
        yes_price REAL,
        no_price REAL,
        bid REAL,
        ask REAL,
        spread REAL,
        volume INTEGER,
        open_interest INTEGER,
        expiration_time TEXT,
        market_probability REAL,
        oracle_fair_value REAL,
        edge_percent REAL,
        confidence_score REAL,
        reasons TEXT,
        grade TEXT,
        raw_json TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oracle_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE NOT NULL,
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        finished_at TEXT,
        duration_seconds REAL,
        status TEXT,
        notes TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        step_name TEXT NOT NULL,
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        finished_at TEXT,
        duration_seconds REAL,
        status TEXT,
        records_processed INTEGER DEFAULT 0,
        error_message TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_quality_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        report_time TEXT DEFAULT CURRENT_TIMESTAMP,
        total_markets INTEGER,
        unique_markets INTEGER,
        useful_priced_markets INTEGER,
        snapshots_total INTEGER,
        features_total INTEGER,
        signals_total INTEGER,
        missing_market_probability INTEGER,
        missing_spread_score INTEGER,
        avg_confidence REAL,
        grade_a_plus INTEGER,
        grade_a INTEGER,
        grade_a_minus INTEGER,
        grade_b INTEGER,
        grade_c INTEGER,
        grade_d INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        market_title TEXT,
        category TEXT,
        status TEXT,
        yes_price REAL,
        no_price REAL,
        volume INTEGER,
        open_interest INTEGER,
        expiration_time TEXT,
        raw_json TEXT,
        captured_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_timeseries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        previous_capture_time TEXT,
        current_capture_time TEXT,
        previous_yes_price REAL,
        current_yes_price REAL,
        yes_price_change REAL,
        previous_no_price REAL,
        current_no_price REAL,
        no_price_change REAL,
        previous_volume INTEGER,
        current_volume INTEGER,
        volume_change INTEGER,
        previous_open_interest INTEGER,
        current_open_interest INTEGER,
        open_interest_change INTEGER,
        minutes_elapsed REAL,
        price_velocity REAL,
        momentum_score REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def test_db():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in cursor.fetchall()]

    conn.close()

    print("Oracle database initialized successfully.")
    print("Database path:", DB_PATH)
    print("Tables created:")
    for table in tables:
        print("-", table)


if __name__ == "__main__":
    test_db()