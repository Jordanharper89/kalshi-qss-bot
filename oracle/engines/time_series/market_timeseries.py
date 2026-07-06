"""
Oracle Market Time-Series Engine

ORACLE-010

Purpose:
- Compare the latest market history row against the previous row.
- Calculate price change, volume change, OI change, velocity, and momentum.
- Store market movement data forever.
"""

from datetime import datetime
from oracle.database.db import get_connection, init_db


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00").replace(" ", "T"))
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def calculate_momentum_score(price_change, volume_change, oi_change):
    score = 50.0

    score += price_change * 4

    if volume_change > 0:
        score += min(volume_change / 100, 20)

    if oi_change > 0:
        score += min(oi_change / 100, 20)

    if price_change < 0:
        score += price_change * 2

    return max(0, min(100, score))


def build_market_timeseries(limit=500):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT ticker
        FROM market_history
        ORDER BY ticker
        LIMIT ?
        """,
        (limit,),
    )

    tickers = [row["ticker"] for row in cursor.fetchall()]
    saved = 0
    skipped = 0

    for ticker in tickers:
        cursor.execute(
            """
            SELECT *
            FROM market_history
            WHERE ticker = ?
            ORDER BY captured_at DESC
            LIMIT 2
            """,
            (ticker,),
        )

        rows = cursor.fetchall()

        if len(rows) < 2:
            skipped += 1
            continue

        current = rows[0]
        previous = rows[1]

        current_time = parse_time(current["captured_at"])
        previous_time = parse_time(previous["captured_at"])

        minutes_elapsed = None

        if current_time and previous_time:
            minutes_elapsed = max(
                (current_time - previous_time).total_seconds() / 60,
                0.0001,
            )

        previous_yes = safe_float(previous["yes_price"])
        current_yes = safe_float(current["yes_price"])
        yes_change = current_yes - previous_yes

        previous_no = safe_float(previous["no_price"])
        current_no = safe_float(current["no_price"])
        no_change = current_no - previous_no

        previous_volume = safe_int(previous["volume"])
        current_volume = safe_int(current["volume"])
        volume_change = current_volume - previous_volume

        previous_oi = safe_int(previous["open_interest"])
        current_oi = safe_int(current["open_interest"])
        oi_change = current_oi - previous_oi

        price_velocity = None

        if minutes_elapsed:
            price_velocity = yes_change / minutes_elapsed

        momentum_score = calculate_momentum_score(
            yes_change,
            volume_change,
            oi_change,
        )

        cursor.execute(
            """
            INSERT INTO market_timeseries (
                ticker,
                previous_capture_time,
                current_capture_time,
                previous_yes_price,
                current_yes_price,
                yes_price_change,
                previous_no_price,
                current_no_price,
                no_price_change,
                previous_volume,
                current_volume,
                volume_change,
                previous_open_interest,
                current_open_interest,
                open_interest_change,
                minutes_elapsed,
                price_velocity,
                momentum_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker,
                previous["captured_at"],
                current["captured_at"],
                previous_yes,
                current_yes,
                yes_change,
                previous_no,
                current_no,
                no_change,
                previous_volume,
                current_volume,
                volume_change,
                previous_oi,
                current_oi,
                oi_change,
                minutes_elapsed,
                price_velocity,
                momentum_score,
            ),
        )

        saved += 1

    conn.commit()
    conn.close()

    print("Market time-series build complete.")
    print(f"Time-series rows saved: {saved}")
    print(f"Markets skipped, not enough history: {skipped}")

    return saved


def preview_market_timeseries(limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ticker,
            previous_yes_price,
            current_yes_price,
            yes_price_change,
            volume_change,
            open_interest_change,
            minutes_elapsed,
            price_velocity,
            momentum_score
        FROM market_timeseries
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    print("")
    print("Latest market time-series rows:")
    print("-" * 80)

    for row in rows:
        print(
            f"Momentum {round(row['momentum_score'], 2)} | "
            f"YES {row['previous_yes_price']} -> {row['current_yes_price']} | "
            f"Change {round(row['yes_price_change'], 2)} | "
            f"Vol Δ {row['volume_change']} | "
            f"OI Δ {row['open_interest_change']} | "
            f"Vel {row['price_velocity']} | "
            f"{row['ticker']}"
        )


if __name__ == "__main__":
    build_market_timeseries()
    preview_market_timeseries()