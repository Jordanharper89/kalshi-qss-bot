"""
Oracle Data Quality Report

ORACLE-008

Purpose:
- Print Oracle database health after every pipeline run.
- Store quality report in SQLite.
"""

from oracle.database.db import get_connection, init_db


def fetch_one(cursor, query: str, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0] if row else 0


def build_data_quality_report(run_id: str) -> None:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    total_markets = fetch_one(cursor, "SELECT COUNT(*) FROM markets")
    unique_markets = fetch_one(cursor, "SELECT COUNT(DISTINCT ticker) FROM markets")

    useful_priced_markets = fetch_one(
        cursor,
        """
        SELECT COUNT(*)
        FROM markets
        WHERE yes_price > 0
        AND yes_price < 100
        """
    )

    snapshots_total = fetch_one(cursor, "SELECT COUNT(*) FROM order_book_snapshots")
    features_total = fetch_one(cursor, "SELECT COUNT(*) FROM features")
    signals_total = fetch_one(cursor, "SELECT COUNT(*) FROM signals")

    missing_market_probability = fetch_one(
        cursor,
        """
        SELECT COUNT(*)
        FROM features
        WHERE market_probability IS NULL
        """
    )

    missing_spread_score = fetch_one(
        cursor,
        """
        SELECT COUNT(*)
        FROM features
        WHERE spread_score IS NULL
        """
    )

    avg_confidence = fetch_one(
        cursor,
        """
        SELECT COALESCE(AVG(confidence_score), 0)
        FROM signals
        """
    )

    grade_a_plus = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'A+'")
    grade_a = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'A'")
    grade_a_minus = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'A-'")
    grade_b = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'B'")
    grade_c = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'C'")
    grade_d = fetch_one(cursor, "SELECT COUNT(*) FROM signals WHERE grade = 'D'")

    cursor.execute(
        """
        INSERT INTO data_quality_reports (
            run_id,
            total_markets,
            unique_markets,
            useful_priced_markets,
            snapshots_total,
            features_total,
            signals_total,
            missing_market_probability,
            missing_spread_score,
            avg_confidence,
            grade_a_plus,
            grade_a,
            grade_a_minus,
            grade_b,
            grade_c,
            grade_d
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            total_markets,
            unique_markets,
            useful_priced_markets,
            snapshots_total,
            features_total,
            signals_total,
            missing_market_probability,
            missing_spread_score,
            avg_confidence,
            grade_a_plus,
            grade_a,
            grade_a_minus,
            grade_b,
            grade_c,
            grade_d,
        ),
    )

    conn.commit()
    conn.close()

    duplicates = total_markets - unique_markets

    print("")
    print("=" * 70)
    print("ORACLE DATA QUALITY REPORT")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    print("")
    print("Markets")
    print("-" * 70)
    print(f"Total markets:              {total_markets}")
    print(f"Unique markets:             {unique_markets}")
    print(f"Duplicate rows:             {duplicates}")
    print(f"Useful priced markets:      {useful_priced_markets}")
    print("")
    print("Snapshots / Features / Signals")
    print("-" * 70)
    print(f"Orderbook snapshots:        {snapshots_total}")
    print(f"Features total:             {features_total}")
    print(f"Signals total:              {signals_total}")
    print(f"Missing market probability: {missing_market_probability}")
    print(f"Missing spread score:       {missing_spread_score}")
    print("")
    print("Signal Grades")
    print("-" * 70)
    print(f"A+:                         {grade_a_plus}")
    print(f"A:                          {grade_a}")
    print(f"A-:                         {grade_a_minus}")
    print(f"B:                          {grade_b}")
    print(f"C:                          {grade_c}")
    print(f"D:                          {grade_d}")
    print(f"Average confidence:         {round(avg_confidence, 2)}")
    print("=" * 70)