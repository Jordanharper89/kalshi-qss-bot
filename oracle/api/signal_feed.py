import json
from typing import Any, Dict, List, Optional

from oracle.database.db import get_connection, init_db


GRADE_RANK = {"A+": 1, "A": 2, "A-": 3, "B": 4, "C": 5, "D": 6}


def row_to_dict(row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def parse_reasons(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except Exception:
        return [value]


def parse_raw_json(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {}


def format_signal(row) -> Dict[str, Any]:
    data = row_to_dict(row)
    data["reasons"] = parse_reasons(data.get("reasons"))
    raw = parse_raw_json(data.get("raw_json"))
    data["normalization"] = raw.get("normalization", {})
    return data


def is_clean_signal(signal: Dict[str, Any], hide_multileg: bool = True) -> bool:
    norm = signal.get("normalization", {})
    subtype = norm.get("subtype", "")

    if hide_multileg and subtype == "multi_leg_bundle":
        return False

    return True


def get_latest_signals(limit_pool: int = 300) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.ticker,
            s.market_title,
            s.yes_price,
            s.no_price,
            s.market_probability,
            s.oracle_fair_value,
            s.edge_percent,
            s.confidence_score,
            s.grade,
            s.reasons,
            s.signal_time,
            s.raw_json
        FROM signals s
        INNER JOIN (
            SELECT ticker, MAX(id) AS latest_id
            FROM signals
            GROUP BY ticker
        ) latest
        ON latest.latest_id = s.id
        ORDER BY s.confidence_score DESC, s.edge_percent DESC, s.signal_time DESC
        LIMIT ?
        """,
        (limit_pool,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [format_signal(row) for row in rows]


def get_top_signals(limit: int = 10, min_grade: str = "B", hide_multileg: bool = True) -> List[Dict[str, Any]]:
    signals = get_latest_signals(limit_pool=500)
    min_rank = GRADE_RANK.get(min_grade, 4)

    filtered = []

    for signal in signals:
        grade = signal.get("grade", "D")
        rank = GRADE_RANK.get(grade, 6)

        if rank > min_rank:
            continue

        if not is_clean_signal(signal, hide_multileg=hide_multileg):
            continue

        filtered.append(signal)

    filtered.sort(
        key=lambda s: (
            GRADE_RANK.get(s.get("grade", "D"), 6) * -1,
            s.get("edge_percent") or 0,
            s.get("confidence_score") or 0,
        ),
        reverse=True,
    )

    return filtered[:limit]


def get_watchlist_signals(limit: int = 10) -> List[Dict[str, Any]]:
    signals = get_latest_signals(limit_pool=500)

    filtered = []

    for signal in signals:
        if not is_clean_signal(signal, hide_multileg=True):
            continue

        if signal.get("market_probability") is None:
            continue

        filtered.append(signal)

    filtered.sort(
        key=lambda s: (
            s.get("confidence_score") or 0,
            s.get("edge_percent") or 0,
        ),
        reverse=True,
    )

    return filtered[:limit]


def get_signal_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
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
            grade,
            reasons,
            signal_time,
            raw_json
        FROM signals
        WHERE ticker = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (ticker,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return format_signal(row)


def get_latest_quality_report() -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM data_quality_reports
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    conn.close()

    return row_to_dict(row) if row else None


def print_top_signals(limit: int = 10) -> None:
    signals = get_top_signals(limit=limit)

    print("")
    print("ORACLE TOP SIGNALS — CLEAN B+ ONLY")
    print("=" * 80)

    if not signals:
        print("No clean B+ or better Oracle signals found yet.")
        return

    for signal in signals:
        print(
            f"{signal['grade']} | "
            f"Market {round(signal['market_probability'] or 0, 2)} | "
            f"Oracle {round(signal['oracle_fair_value'] or 0, 2)} | "
            f"Edge {round(signal['edge_percent'] or 0, 2)} | "
            f"Conf {round(signal['confidence_score'] or 0, 2)} | "
            f"{signal['ticker']}"
        )


def print_quality_report() -> None:
    report = get_latest_quality_report()

    print("")
    print("ORACLE LATEST QUALITY REPORT")
    print("=" * 80)

    if not report:
        print("No quality report found.")
        return

    print(f"Run ID:                    {report.get('run_id')}")
    print(f"Report time:               {report.get('report_time')}")
    print(f"Useful priced markets:     {report.get('useful_priced_markets')}")
    print(f"Signals total:             {report.get('signals_total')}")
    print(f"Average confidence:        {round(report.get('avg_confidence') or 0, 2)}")


if __name__ == "__main__":
    print_top_signals(limit=10)
    print_quality_report()