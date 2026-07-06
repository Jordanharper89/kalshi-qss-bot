"""
Oracle Feature Engine

ORACLE-005

Purpose:
- Convert raw order book snapshots into calculated market features.
- Store those features in the features table.
- No trading.
- No fair value signals yet.
"""

from typing import Optional

from oracle.database.db import get_connection, init_db


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def calculate_market_probability(best_yes_bid: Optional[float], best_yes_ask: Optional[float]) -> Optional[float]:
    if best_yes_bid is None and best_yes_ask is None:
        return None

    if best_yes_bid is not None and best_yes_ask is not None:
        return (best_yes_bid + best_yes_ask) / 2

    return best_yes_bid if best_yes_bid is not None else best_yes_ask


def calculate_spread_score(spread: Optional[float]) -> Optional[float]:
    if spread is None:
        return None

    # Lower spread = better market efficiency.
    # 0¢ spread = 100 score, 20¢+ spread = 0 score.
    return clamp(100 - (spread * 5))


def calculate_liquidity_score(yes_depth: Optional[float], no_depth: Optional[float]) -> float:
    yes_depth = yes_depth or 0
    no_depth = no_depth or 0
    total_depth = yes_depth + no_depth

    # Simple placeholder:
    # 1000+ contracts depth = max score.
    return clamp((total_depth / 1000) * 100)


def calculate_imbalance_score(order_imbalance: Optional[float]) -> Optional[float]:
    if order_imbalance is None:
        return None

    # Convert -1 to +1 imbalance into 0 to 100 score.
    return clamp((order_imbalance + 1) * 50)


def calculate_market_efficiency_score(spread_score: Optional[float], liquidity_score: Optional[float]) -> Optional[float]:
    scores = [s for s in [spread_score, liquidity_score] if s is not None]

    if not scores:
        return None

    return sum(scores) / len(scores)


def get_latest_snapshots(limit: int = 50):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s.*
        FROM order_book_snapshots s
        INNER JOIN (
            SELECT ticker, MAX(snapshot_time) AS latest_time
            FROM order_book_snapshots
            GROUP BY ticker
        ) latest
        ON s.ticker = latest.ticker
        AND s.snapshot_time = latest.latest_time
        ORDER BY s.snapshot_time DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def save_features(snapshot) -> bool:
    market_probability = calculate_market_probability(
        snapshot["best_yes_bid"],
        snapshot["best_yes_ask"],
    )

    spread_score = calculate_spread_score(snapshot["spread"])

    liquidity_score = calculate_liquidity_score(
        snapshot["yes_bid_depth"],
        snapshot["no_bid_depth"],
    )

    order_book_imbalance = snapshot["order_imbalance"]

    market_efficiency_score = calculate_market_efficiency_score(
        spread_score,
        liquidity_score,
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO features (
            ticker,
            market_probability,
            liquidity_score,
            spread_score,
            volatility_score,
            momentum_score,
            order_book_imbalance,
            behavioral_bias_score,
            time_decay_score,
            market_efficiency_score,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot["ticker"],
            market_probability,
            liquidity_score,
            spread_score,
            None,
            None,
            order_book_imbalance,
            None,
            None,
            market_efficiency_score,
            None,
        ),
    )

    conn.commit()
    conn.close()

    return True


def build_features(limit: int = 50) -> int:
    snapshots = get_latest_snapshots(limit=limit)

    print(f"Building features from {len(snapshots)} latest snapshots...")

    saved = 0

    for snapshot in snapshots:
        save_features(snapshot)
        saved += 1

    print("Feature build complete.")
    print(f"Features saved: {saved}")

    return saved


if __name__ == "__main__":
    build_features()