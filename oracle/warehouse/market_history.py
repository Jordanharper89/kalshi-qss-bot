"""
Oracle Market History Warehouse

ORACLE-009

Purpose:
- Copy current market states into permanent history.
- Build Oracle's time-series memory.
- Nothing is deleted.
"""

from oracle.database.db import get_connection, init_db


def capture_market_history(limit: int = 1000) -> int:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ticker,
            market_title,
            category,
            status,
            yes_price,
            no_price,
            volume,
            open_interest,
            expiration_time,
            raw_json
        FROM markets
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    saved = 0

    for row in rows:
        cursor.execute(
            """
            INSERT INTO market_history (
                ticker,
                market_title,
                category,
                status,
                yes_price,
                no_price,
                volume,
                open_interest,
                expiration_time,
                raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["ticker"],
                row["market_title"],
                row["category"],
                row["status"],
                row["yes_price"],
                row["no_price"],
                row["volume"],
                row["open_interest"],
                row["expiration_time"],
                row["raw_json"],
            ),
        )

        saved += 1

    conn.commit()
    conn.close()

    print("Market history capture complete.")
    print(f"History rows saved: {saved}")

    return saved


if __name__ == "__main__":
    capture_market_history()