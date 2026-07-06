"""
ORACLE-045 — Cross-Market Arbitrage Engine

Purpose:
- Find pricing contradictions across Kalshi markets
- Detect related markets that cannot all be priced correctly
- Identify time-ladder inconsistencies
- Identify mutually exclusive event over/under-pricing
- Produce arbitrage / relative-value alerts

Safe:
- No trading
- No orders
"""

import json
import time
import re
from pathlib import Path
from math import isfinite
from collections import defaultdict

UNIVERSE_FILE = Path("oracle_market_universe.json")
ARBITRAGE_FILE = Path("oracle_cross_market_arbitrage.json")


def now():
    return time.time()


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if not isfinite(value):
            return default
        return value
    except Exception:
        return default


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, safe_float(value)))


def load_markets(limit=2000):
    if not UNIVERSE_FILE.exists():
        return []

    try:
        data = json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
        markets = data.get("markets", [])
        if not isinstance(markets, list):
            return []
        return markets[:int(limit)]
    except Exception:
        return []


def yes_mid(m):
    bid = safe_float(m.get("yes_bid"))
    ask = safe_float(m.get("yes_ask"))
    last = safe_float(m.get("last_price"))
    price = safe_float(m.get("market_price"))

    if bid > 0 and ask > 0:
        return round((bid + ask) / 2, 4)

    return price or last or ask or bid or 0.0


def no_mid(m):
    bid = safe_float(m.get("no_bid"))
    ask = safe_float(m.get("no_ask"))

    if bid > 0 and ask > 0:
        return round((bid + ask) / 2, 4)

    y = yes_mid(m)
    return round(1 - y, 4) if y > 0 else 0.0


def spread(m):
    bid = safe_float(m.get("yes_bid"))
    ask = safe_float(m.get("yes_ask"))

    if bid > 0 and ask > 0:
        return round(abs(ask - bid), 4)

    return 1.0


def activity(m):
    return max(
        safe_float(m.get("volume")),
        safe_float(m.get("volume_24h")),
        safe_float(m.get("liquidity")),
        safe_float(m.get("open_interest")),
    )


def tradable(m):
    if str(m.get("status", "")).lower() not in ("active", "open"):
        return False

    p = yes_mid(m)
    if p <= 0 or p >= 1:
        return False

    if spread(m) > 0.35:
        return False

    if activity(m) <= 0:
        return False

    return True


def event_key(m):
    return str(m.get("event_ticker") or "").upper()


def series_key(m):
    return str(m.get("series_ticker") or "").upper()


def title_key(m):
    title = str(m.get("event_title") or m.get("title") or "").lower()
    title = re.sub(r"before\s+[a-z]{3,9}\s+\d{1,2},?\s+\d{4}", "before DATE", title)
    title = re.sub(r"before\s+\d{4}", "before YEAR", title)
    title = re.sub(r"\d{4}", "YEAR", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def extract_year(m):
    text = " ".join([
        str(m.get("ticker") or ""),
        str(m.get("title") or ""),
        str(m.get("event_title") or ""),
        str(m.get("close_time") or ""),
        str(m.get("expiration_time") or ""),
    ])
    years = re.findall(r"(20\d{2}|19\d{2}|21\d{2})", text)
    if not years:
        return None
    try:
        return min(int(y) for y in years)
    except Exception:
        return None



def is_candidate_set_market(m):
    """
    True when markets are different candidates/options in the same event,
    not a time ladder.
    """
    blob = " ".join([
        str(m.get("title") or ""),
        str(m.get("event_title") or ""),
        str(m.get("ticker") or ""),
    ]).lower()

    phrases = [
        "who will",
        "which ",
        "next prime minister",
        "next speaker",
        "next ceo",
        "first to leave office",
        "ipo first",
        "host for",
        "perform as",
        "next james bond",
        "country will",
        "person will",
        "team will",
    ]

    return any(p in blob for p in phrases)


def is_true_time_ladder_group(items):
    """
    Time ladder groups should be same underlying event with different dates/deadlines.
    Candidate sets must be excluded.
    """
    if len(items) < 2:
        return False

    if any(is_candidate_set_market(m) for m in items):
        return False

    years = [extract_year(m) for m in items if extract_year(m) is not None]
    if len(set(years)) < 2:
        return False

    blob = " ".join(
        (str(m.get("title") or "") + " " + str(m.get("event_title") or "")).lower()
        for m in items
    )

    ladder_terms = [
        "before",
        "by ",
        "through",
        "end of",
        "on or before",
        "at least",
        "above",
        "below",
        "over",
        "under",
    ]

    return any(term in blob for term in ladder_terms)



def subject_key(m):
    """
    Extract a rough same-subject key.
    Time ladders should compare same subject across different deadlines,
    not different candidates/people/teams.
    """
    raw = m.get("raw", {}) if isinstance(m.get("raw"), dict) else {}
    custom = raw.get("custom_strike", {}) if isinstance(raw.get("custom_strike"), dict) else {}

    subject_parts = []

    for key in [
        "Company",
        "Person",
        "Individual",
        "Artist",
        "Team",
        "Country",
        "City",
        "State",
        "golf_competitor",
    ]:
        if custom.get(key):
            subject_parts.append(str(custom.get(key)).lower())

    if subject_parts:
        return "|".join(subject_parts)

    title = str(m.get("title") or "").lower()
    title = re.sub(r"before\s+[a-z]{3,9}\s+\d{1,2},?\s+\d{4}", "before DATE", title)
    title = re.sub(r"before\s+\d{4}", "before YEAR", title)
    title = re.sub(r"\d{4}", "YEAR", title)
    title = re.sub(r"\d{1,2}[:/.-]\d{1,2}[:/.-]?\d*", "DATE", title)
    title = re.sub(r"\s+", " ", title).strip()

    return title


def same_subject(a, b):
    return subject_key(a) == subject_key(b)


def alert(kind, title, markets, edge, confidence, recommendation, reason):
    return {
        "kind": kind,
        "title": title,
        "markets": markets,
        "edge": round(safe_float(edge), 4),
        "edge_pct": round(safe_float(edge) * 100, 2),
        "confidence": round(clamp(confidence), 2),
        "recommendation": recommendation,
        "reason": reason,
        "created_at": now(),
    }


def detect_time_ladder(markets):
    """
    If event is cumulative:
    P(before later date) should usually be >= P(before earlier date).
    Example: AGI before 2028 should be >= AGI before 2027.
    """
    alerts = []

    groups = defaultdict(list)

    for m in markets:
        key = series_key(m) or title_key(m)
        year = extract_year(m)

        if not key or year is None:
            continue

        groups[key].append(m)

    for key, items in groups.items():
        if len(items) < 2:
            continue

        if not is_true_time_ladder_group(items):
            continue

        items = sorted(items, key=lambda x: extract_year(x) or 9999)

        for i in range(len(items) - 1):
            early = items[i]
            later = items[i + 1]

            if not same_subject(early, later):
                continue

            if not same_subject(early, later):
                continue

            y1 = yes_mid(early)
            y2 = yes_mid(later)

            if y1 <= 0 or y2 <= 0:
                continue

            violation = y1 - y2

            if violation >= 0.04:
                conf = 70 + min(violation * 250, 25)
                alerts.append(alert(
                    kind="time_ladder_violation",
                    title="Time ladder contradiction",
                    markets=[
                        {
                            "ticker": early.get("ticker"),
                            "title": early.get("title"),
                            "year": extract_year(early),
                            "yes_mid": y1,
                            "spread": spread(early),
                        },
                        {
                            "ticker": later.get("ticker"),
                            "title": later.get("title"),
                            "year": extract_year(later),
                            "yes_mid": y2,
                            "spread": spread(later),
                        },
                    ],
                    edge=violation,
                    confidence=conf,
                    recommendation=f"Relative value: later market may be underpriced vs earlier market",
                    reason=(
                        f"Earlier deadline market is priced {round(violation*100,2)} points "
                        f"above the later deadline market. For cumulative 'before date' style markets, "
                        f"later should generally be at least as likely as earlier."
                    ),
                ))

    return alerts


def detect_mutually_exclusive_sum(markets):
    """
    For mutually exclusive events, sum of YES probabilities should usually be near 1.
    Large deviation can indicate broad mispricing or bad/liquid markets.
    """
    alerts = []

    groups = defaultdict(list)

    for m in markets:
        event = m.get("event")
        if not isinstance(event, dict):
            continue

        if not event.get("mutually_exclusive"):
            continue

        key = event_key(m)
        if key:
            groups[key].append(m)

    for key, items in groups.items():
        if len(items) < 2:
            continue

        probs = [yes_mid(m) for m in items if yes_mid(m) > 0]
        if len(probs) < 2:
            continue

        total = sum(probs)

        if total >= 1.08:
            edge = total - 1.0
            alerts.append(alert(
                kind="mutually_exclusive_overpriced",
                title="Mutually exclusive set overpriced",
                markets=[
                    {
                        "ticker": m.get("ticker"),
                        "title": m.get("title"),
                        "yes_mid": yes_mid(m),
                        "spread": spread(m),
                    }
                    for m in items[:20]
                ],
                edge=edge,
                confidence=70 + min(edge * 100, 20),
                recommendation="Mutually exclusive set appears overpriced; investigate NO on overpriced legs",
                reason=f"YES probabilities in this mutually exclusive event sum to {round(total*100,2)}%.",
            ))

        elif total <= 0.92:
            edge = 1.0 - total
            alerts.append(alert(
                kind="mutually_exclusive_underpriced",
                title="Mutually exclusive set underpriced",
                markets=[
                    {
                        "ticker": m.get("ticker"),
                        "title": m.get("title"),
                        "yes_mid": yes_mid(m),
                        "spread": spread(m),
                    }
                    for m in items[:20]
                ],
                edge=edge,
                confidence=70 + min(edge * 100, 20),
                recommendation="Mutually exclusive set appears underpriced; investigate YES basket only if all outcomes are represented",
                reason=f"YES probabilities in this mutually exclusive event sum to only {round(total*100,2)}%.",
            ))

    return alerts


def detect_duplicate_price_disagreement(markets):
    """
    Finds similarly titled markets with materially different prices.
    """
    alerts = []
    groups = defaultdict(list)

    for m in markets:
        key = title_key(m)
        if key:
            groups[key].append(m)

    for key, items in groups.items():
        if len(items) < 2:
            continue

        items = [m for m in items if yes_mid(m) > 0]
        if len(items) < 2:
            continue

        items = sorted(items, key=yes_mid)
        low = items[0]
        high = items[-1]

        diff = yes_mid(high) - yes_mid(low)

        if diff >= 0.08:
            alerts.append(alert(
                kind="related_market_price_disagreement",
                title="Related market price disagreement",
                markets=[
                    {
                        "ticker": low.get("ticker"),
                        "title": low.get("title"),
                        "yes_mid": yes_mid(low),
                        "spread": spread(low),
                    },
                    {
                        "ticker": high.get("ticker"),
                        "title": high.get("title"),
                        "yes_mid": yes_mid(high),
                        "spread": spread(high),
                    },
                ],
                edge=diff,
                confidence=60 + min(diff * 200, 25),
                recommendation="Investigate cheaper leg vs expensive related leg",
                reason=f"Very similar market titles differ by {round(diff*100,2)} probability points.",
            ))

    return alerts


def run_arbitrage_scan(limit=2000):
    raw = load_markets(limit=limit)
    markets = [m for m in raw if tradable(m)]

    all_alerts = []
    all_alerts.extend(detect_time_ladder(markets))
    all_alerts.extend(detect_mutually_exclusive_sum(markets))
    all_alerts.extend(detect_duplicate_price_disagreement(markets))

    all_alerts.sort(
        key=lambda x: (
            x.get("confidence", 0),
            abs(safe_float(x.get("edge"))),
        ),
        reverse=True,
    )

    payload = {
        "version": "ORACLE-045",
        "updated_at": now(),
        "raw_markets": len(raw),
        "tradable_markets": len(markets),
        "alert_count": len(all_alerts),
        "alerts": all_alerts,
    }

    ARBITRAGE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_top_arbitrage(limit=10):
    if not ARBITRAGE_FILE.exists():
        run_arbitrage_scan()

    try:
        data = json.loads(ARBITRAGE_FILE.read_text(encoding="utf-8"))
        return data.get("alerts", [])[:int(limit)]
    except Exception:
        return []


def format_arbitrage_alert(a, rank=None):
    rank_line = f"Rank #{rank}" if rank else "Arbitrage Alert"

    markets = a.get("markets", [])
    market_lines = []
    for m in markets[:8]:
        market_lines.append(
            f"• {m.get('ticker')} | {m.get('yes_mid')} | spread {m.get('spread')}\n  {m.get('title')}"
        )

    if not market_lines:
        market_lines.append("None")

    return f"""
⚡ ORACLE CROSS-MARKET ARBITRAGE

{rank_line}

Type:
{a.get("kind")}

Title:
{a.get("title")}

Edge:
{a.get("edge_pct")}%

Confidence:
{a.get("confidence")}

Recommendation:
{a.get("recommendation")}

Reason:
{a.get("reason")}

Markets:
{chr(10).join(market_lines)}
""".strip()


def format_top_arbitrage(limit=10):
    alerts = get_top_arbitrage(limit=limit)

    if not alerts:
        return "No cross-market arbitrage alerts found."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_arbitrage_alert(a, rank=i)
        for i, a in enumerate(alerts[:int(limit)], start=1)
    )


def diagnostics():
    payload = run_arbitrage_scan()

    return {
        "module": "oracle_cross_market_arbitrage",
        "status": "ok",
        "raw_markets": payload.get("raw_markets"),
        "tradable_markets": payload.get("tradable_markets"),
        "alerts": payload.get("alert_count"),
        "top": [
            {
                "kind": a.get("kind"),
                "edge_pct": a.get("edge_pct"),
                "confidence": a.get("confidence"),
                "recommendation": a.get("recommendation"),
            }
            for a in payload.get("alerts", [])[:5]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top_arbitrage(limit=5))
