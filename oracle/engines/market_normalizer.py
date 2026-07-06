"""
Oracle Market Normalization & Quality Engine

ORACLE-006

Purpose:
- Classify Kalshi markets into useful research categories.
- Score market quality before fair value modeling.
- Filter out low-quality/noisy markets.
- No trading.
"""

import json
from typing import Dict, Any

from oracle.database.db import get_connection, init_db


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def classify_category(title: str, ticker: str, category: str) -> str:
    text = f"{title} {ticker} {category}".lower()

    if any(word in text for word in ["btc", "bitcoin", "eth", "ethereum", "crypto"]):
        return "crypto"

    if any(word in text for word in ["cpi", "fed", "rates", "inflation", "jobs", "unemployment", "treasury"]):
        return "macro"

    if any(word in text for word in ["trump", "biden", "election", "senate", "house", "president"]):
        return "politics"

    if any(word in text for word in [
        "yankees", "dodgers", "mlb", "nba", "nfl", "nhl",
        "soccer", "goals", "runs", "wins", "1st half",
        "france", "spain", "belgium", "houston", "pittsburgh"
    ]):
        return "sports"

    return "unknown"


def classify_subtype(title: str) -> str:
    text = title.lower()

    if "," in title and title.count(",") >= 3:
        return "multi_leg_bundle"

    if "wins by" in text or "over" in text or "under" in text:
        return "spread_total"

    if "btc" in text or "bitcoin" in text or "eth" in text or "ethereum" in text:
        return "price_target"

    if "will" in text:
        return "binary_event"

    return "general_binary"


def score_market_quality(
    yes_price,
    volume,
    open_interest,
    category: str,
    subtype: str,
) -> float:
    score = 0.0

    yes_price = yes_price or 0
    volume = volume or 0
    open_interest = open_interest or 0

    if 5 <= yes_price <= 95:
        score += 20

    if 15 <= yes_price <= 85:
        score += 10

    score += clamp(volume / 1000 * 25, 0, 25)
    score += clamp(open_interest / 1000 * 25, 0, 25)

    if category in ["crypto", "macro", "politics"]:
        score += 20
    elif category == "sports":
        score += 10

    if subtype == "multi_leg_bundle":
        score -= 25
    elif subtype in ["price_target", "binary_event"]:
        score += 10

    return clamp(score)


def grade_quality(score: float) -> str:
    if score >= 85:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 65:
        return "A-"
    if score >= 55:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def normalize_markets(limit: int = 500) -> int:
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticker, market_title, category, yes_price, volume, open_interest
        FROM markets
        WHERE yes_price IS NOT NULL
        ORDER BY open_interest DESC, volume DESC, updated_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    saved = 0

    for row in rows:
        ticker = row["ticker"]
        title = row["market_title"] or ""
        raw_category = row["category"] or ""

        normalized_category = classify_category(title, ticker, raw_category)
        subtype = classify_subtype(title)

        quality_score = score_market_quality(
            row["yes_price"],
            row["volume"],
            row["open_interest"],
            normalized_category,
            subtype,
        )

        quality_grade = grade_quality(quality_score)

        normalized_payload: Dict[str, Any] = {
            "normalized_category": normalized_category,
            "subtype": subtype,
            "market_quality_score": quality_score,
            "market_quality_grade": quality_grade,
        }

        cursor.execute(
            """
            UPDATE markets
            SET raw_json = json_set(
                COALESCE(raw_json, '{}'),
                '$.oracle_normalization',
                json(?)
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE ticker = ?
            """,
            (
                json.dumps(normalized_payload),
                ticker,
            ),
        )

        saved += 1

    conn.commit()
    conn.close()

    print("Market normalization complete.")
    print(f"Markets normalized: {saved}")

    return saved


def preview_normalized_markets(limit: int = 20) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticker, market_title, yes_price, volume, open_interest, raw_json
        FROM markets
        WHERE raw_json LIKE '%oracle_normalization%'
        ORDER BY open_interest DESC, volume DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    print("")
    print("Top normalized markets:")
    print("-" * 80)

    for row in rows:
        raw = json.loads(row["raw_json"])
        norm = raw.get("oracle_normalization", {})

        print(
            f"{norm.get('market_quality_grade')} | "
            f"{norm.get('market_quality_score')} | "
            f"{norm.get('normalized_category')} | "
            f"{norm.get('subtype')} | "
            f"YES {row['yes_price']} | "
            f"VOL {row['volume']} | "
            f"OI {row['open_interest']} | "
            f"{row['ticker']}"
        )


if __name__ == "__main__":
    normalize_markets()
    preview_normalized_markets()