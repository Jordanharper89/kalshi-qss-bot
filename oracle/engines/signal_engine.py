"""
Oracle Signal Engine

ORACLE-007

Purpose:
- Convert markets + features into Oracle research signals.
- Create placeholder fair value.
- Calculate edge, confidence, reasons, and grade.
- No trading.
"""

import json
from typing import Optional, List

from oracle.database.db import get_connection, init_db


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def safe_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_normalization(raw_json: str) -> dict:
    if not raw_json:
        return {}

    try:
        raw = json.loads(raw_json)
        return raw.get("oracle_normalization", {}) or {}
    except Exception:
        return {}


def placeholder_fair_value(market_probability: float, liquidity_score: float, market_quality_score: float) -> float:
    """
    Placeholder fair value model.

    For now:
    - Start with market probability.
    - Slightly reward liquid/high-quality markets.
    - This is NOT a real prediction model yet.
    """

    adjustment = 0.0

    if liquidity_score >= 75:
        adjustment += 1.0

    if market_quality_score >= 70:
        adjustment += 1.0

    return clamp(market_probability + adjustment)


def calculate_confidence(liquidity_score: float, market_efficiency_score: float, market_quality_score: float) -> float:
    scores = [
        liquidity_score or 0,
        market_efficiency_score or 0,
        market_quality_score or 0,
    ]

    return clamp(sum(scores) / len(scores))


def grade_signal(edge: float, confidence: float) -> str:
    if edge >= 10 and confidence >= 80:
        return "A+"
    if edge >= 7 and confidence >= 70:
        return "A"
    if edge >= 5 and confidence >= 60:
        return "A-"
    if edge >= 3 and confidence >= 50:
        return "B"
    if edge >= 1:
        return "C"
    return "D"


def build_reasons(
    edge: float,
    liquidity_score: float,
    market_quality_score: float,
    market_efficiency_score: float,
) -> List[str]:
    reasons = []

    if edge > 0:
        reasons.append("Positive placeholder edge")

    if liquidity_score >= 75:
        reasons.append("Strong liquidity")

    if market_quality_score >= 70:
        reasons.append("High market quality")

    if market_efficiency_score >= 70:
        reasons.append("Efficient market structure")

    if not reasons:
        reasons.append("Low-confidence placeholder signal")

    return reasons


def get_latest_feature_rows(limit: int = 50):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            f.ticker,
            f.market_probability,
            f.liquidity_score,
            f.spread_score,
            f.order_book_imbalance,
            f.market_efficiency_score,
            m.market_title,
            m.yes_price,
            m.no_price,
            m.volume,
            m.open_interest,
            m.expiration_time,
            m.raw_json
        FROM features f
        JOIN markets m ON m.ticker = f.ticker
        INNER JOIN (
            SELECT ticker, MAX(snapshot_time) AS latest_time
            FROM features
            GROUP BY ticker
        ) latest
        ON latest.ticker = f.ticker
        AND latest.latest_time = f.snapshot_time
        WHERE f.market_probability IS NOT NULL
        ORDER BY f.id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def save_signal(row) -> bool:
    norm = extract_normalization(row["raw_json"])

    market_probability = safe_float(row["market_probability"], 0.0) or 0.0
    liquidity_score = safe_float(row["liquidity_score"], 0.0) or 0.0
    market_efficiency_score = safe_float(row["market_efficiency_score"], 0.0) or 0.0
    market_quality_score = safe_float(norm.get("market_quality_score"), 0.0) or 0.0

    oracle_fair_value = placeholder_fair_value(
        market_probability,
        liquidity_score,
        market_quality_score,
    )

    edge_percent = oracle_fair_value - market_probability

    confidence_score = calculate_confidence(
        liquidity_score,
        market_efficiency_score,
        market_quality_score,
    )

    reasons = build_reasons(
        edge_percent,
        liquidity_score,
        market_quality_score,
        market_efficiency_score,
    )

    grade = grade_signal(edge_percent, confidence_score)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO signals (
            ticker,
            market_title,
            yes_price,
            no_price,
            bid,
            ask,
            spread,
            volume,
            open_interest,
            expiration_time,
            market_probability,
            oracle_fair_value,
            edge_percent,
            confidence_score,
            reasons,
            grade,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["ticker"],
            row["market_title"],
            row["yes_price"],
            row["no_price"],
            row["market_probability"],
            None,
            None,
            row["volume"],
            row["open_interest"],
            row["expiration_time"],
            market_probability,
            oracle_fair_value,
            edge_percent,
            confidence_score,
            json.dumps(reasons),
            grade,
            json.dumps(
                {
                    "normalization": norm,
                    "model": "placeholder_fair_value_v1",
                },
                sort_keys=True,
            ),
        ),
    )

    conn.commit()
    conn.close()

    return True


def build_signals(limit: int = 50) -> int:
    rows = get_latest_feature_rows(limit=limit)

    print(f"Building Oracle signals from {len(rows)} feature rows...")

    saved = 0

    for row in rows:
        save_signal(row)
        saved += 1

    print("Signal build complete.")
    print(f"Signals saved: {saved}")

    return saved


def preview_signals(limit: int = 10) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ticker,
            market_title,
            market_probability,
            oracle_fair_value,
            edge_percent,
            confidence_score,
            grade,
            reasons
        FROM signals
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    print("")
    print("Latest Oracle signals:")
    print("-" * 80)

    for row in rows:
        print(
            f"{row['grade']} | "
            f"Market {round(row['market_probability'], 2)} | "
            f"Oracle {round(row['oracle_fair_value'], 2)} | "
            f"Edge {round(row['edge_percent'], 2)} | "
            f"Conf {round(row['confidence_score'], 2)} | "
            f"{row['ticker']}"
        )


if __name__ == "__main__":
    build_signals()
    preview_signals()