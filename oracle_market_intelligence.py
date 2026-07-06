"""
ORACLE-040 — Market Intelligence Engine

Purpose:
- Convert raw Kalshi markets into research-style intelligence cards
- Classify market category/subtype
- Select relevant provider types automatically
- Estimate rough fair value from market structure
- Compute edge, confidence, research score, risk, and recommendation
- Prepare data for Oracle Top 10 / dashboard / continuous intelligence

Safe:
- No trading
- No orders
"""

import json
import time
import re
from pathlib import Path
from math import isfinite

UNIVERSE_FILE = Path("oracle_market_universe.json")
INTELLIGENCE_FILE = Path("oracle_market_intelligence.json")


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


def moneyline_price(market):
    yes_bid = safe_float(market.get("yes_bid"))
    yes_ask = safe_float(market.get("yes_ask"))
    last_price = safe_float(market.get("last_price"))
    previous_price = safe_float(market.get("previous_price"))
    market_price = safe_float(market.get("market_price"))

    if yes_bid > 0 and yes_ask > 0:
        return round((yes_bid + yes_ask) / 2, 4)

    return market_price or last_price or previous_price or yes_ask or yes_bid or 0.0


def spread_width(market):
    yes_bid = safe_float(market.get("yes_bid"))
    yes_ask = safe_float(market.get("yes_ask"))

    if yes_bid <= 0 or yes_ask <= 0:
        return 1.0

    return round(abs(yes_ask - yes_bid), 4)


def get_text_blob(market):
    raw = market.get("raw", {}) if isinstance(market.get("raw"), dict) else {}
    event = market.get("event", {}) if isinstance(market.get("event"), dict) else {}

    parts = [
        market.get("ticker", ""),
        market.get("title", ""),
        market.get("event_title", ""),
        market.get("category", ""),
        raw.get("rules_primary", ""),
        raw.get("rules_secondary", ""),
        raw.get("yes_sub_title", ""),
        raw.get("no_sub_title", ""),
        event.get("title", ""),
        event.get("sub_title", ""),
    ]

    return " ".join(str(x or "") for x in parts).lower()


def classify_market(market):
    category = str(market.get("category") or "unknown")
    blob = get_text_blob(market)

    subtype = "general"
    domain = category.lower().replace(" ", "_")

    if any(x in blob for x in ["election", "president", "prime minister", "senate", "house", "parliament", "seat", "vote", "mayor", "governor"]):
        domain = "elections"
        subtype = "politics"

    elif any(x in blob for x in ["ipo", "stock", "shares", "nasdaq", "nyse", "sec filing", "earnings"]):
        domain = "financials"
        subtype = "ipo_or_equity"

    elif any(x in blob for x in ["cpi", "inflation", "fed", "interest rate", "jobs", "unemployment", "gdp"]):
        domain = "economics"
        subtype = "macro_release"

    elif any(x in blob for x in ["temperature", "snow", "rain", "hurricane", "storm", "weather"]):
        domain = "weather"
        subtype = "weather"

    elif any(x in blob for x in ["nba", "nfl", "mlb", "nhl", "soccer", "world cup", "goal", "runs", "strikeouts", "wins by", "corners"]):
        domain = "sports"
        subtype = "sports"

    elif any(x in blob for x in ["bitcoin", "btc", "ethereum", "eth", "solana", "crypto"]):
        domain = "crypto"
        subtype = "crypto"

    elif any(x in blob for x in ["openai", "anthropic", "ai", "artificial intelligence"]):
        domain = "technology"
        subtype = "ai"

    elif any(x in blob for x in ["mars", "moon", "spacex", "nasa", "launch"]):
        domain = "science_and_technology"
        subtype = "space"

    return {
        "domain": domain,
        "subtype": subtype,
        "category": category,
    }


def providers_for_classification(cls):
    domain = cls.get("domain")
    subtype = cls.get("subtype")

    base = ["kalshi_public", "market_memory"]

    mapping = {
        "financials": ["sec", "reuters", "bloomberg", "cnbc", "financial_times", "news"],
        "economics": ["fred", "bls", "bea", "treasury", "federal_reserve", "news"],
        "weather": ["noaa", "national_weather_service", "openweather"],
        "elections": ["polling", "ap", "reuters", "official_election_sources", "news"],
        "sports": ["sports_odds", "injury_reports", "schedule", "weather"],
        "crypto": ["coingecko", "exchange_prices", "funding_rates", "news"],
        "technology": ["sec", "github", "company_news", "reuters", "bloomberg", "news"],
        "science_and_technology": ["nasa", "spacex_news", "reuters", "news"],
    }

    return base + mapping.get(domain, ["news", "official_sources"])


def source_quality_score(market):
    event = market.get("event", {}) if isinstance(market.get("event"), dict) else {}
    sources = event.get("settlement_sources") or []

    if not isinstance(sources, list):
        return 50

    names = " ".join(str(s.get("name", "")) for s in sources if isinstance(s, dict)).lower()

    score = 50

    high_quality = [
        "reuters", "associated press", "ap", "sec", "securities and exchange commission",
        "national weather service", "noaa", "bls", "bea", "federal reserve",
        "treasury", "nyse", "nasdaq"
    ]

    strong_media = [
        "bloomberg", "wall street journal", "financial times", "cnbc",
        "new york times", "bbc", "cnn", "politico"
    ]

    for item in high_quality:
        if item in names:
            score += 8

    for item in strong_media:
        if item in names:
            score += 4

    return clamp(score, 0, 100)


def liquidity_score(market):
    open_interest = safe_float(market.get("open_interest"))
    volume = safe_float(market.get("volume"))
    volume_24h = safe_float(market.get("volume_24h"))
    liquidity = safe_float(market.get("liquidity"))

    activity = max(open_interest, volume, volume_24h, liquidity)

    if activity >= 50000:
        return 95
    if activity >= 25000:
        return 88
    if activity >= 10000:
        return 78
    if activity >= 2500:
        return 65
    if activity > 0:
        return 50
    return 35


def price_quality_score(market):
    price = moneyline_price(market)
    spread = spread_width(market)

    score = 70

    if 0.05 <= price <= 0.95:
        score += 10
    else:
        score -= 15

    if spread <= 0.02:
        score += 15
    elif spread <= 0.05:
        score += 8
    elif spread <= 0.10:
        score -= 5
    else:
        score -= 20

    return clamp(score)


def momentum_signal(market):
    price = moneyline_price(market)
    previous = safe_float(market.get("previous_price"))

    if price <= 0 or previous <= 0:
        return 0.0

    return round(price - previous, 4)


def estimate_fair_value(market, cls):
    """
    V1 fair value estimate.

    This is intentionally conservative until live external APIs are wired.
    It adjusts market midpoint using:
    - source quality
    - liquidity
    - spread quality
    - recent price movement
    """
    price = moneyline_price(market)
    if price <= 0:
        return 0.0

    src_score = source_quality_score(market)
    liq_score = liquidity_score(market)
    px_score = price_quality_score(market)
    momentum = momentum_signal(market)

    adjustment = 0.0

    if src_score >= 80:
        adjustment += 0.005
    if liq_score >= 80:
        adjustment += 0.005
    if px_score < 55:
        adjustment -= 0.01

    if abs(momentum) >= 0.05:
        adjustment += momentum * 0.25
    elif abs(momentum) >= 0.02:
        adjustment += momentum * 0.15

    fair = price + adjustment
    return round(max(0.01, min(0.99, fair)), 4)


def confidence_score(market, cls):
    src = source_quality_score(market)
    liq = liquidity_score(market)
    px = price_quality_score(market)

    confidence = src * 0.35 + liq * 0.35 + px * 0.30

    return round(clamp(confidence), 2)


def research_score(market, cls):
    src = source_quality_score(market)
    liq = liquidity_score(market)
    px = price_quality_score(market)

    provider_count = len(providers_for_classification(cls))

    score = src * 0.35 + liq * 0.25 + px * 0.25 + min(provider_count * 2, 15)

    return round(clamp(score), 2)


def recommendation_from_edge(edge, confidence):
    edge = safe_float(edge)
    confidence = safe_float(confidence)

    # No action without enough confidence.
    if confidence < 65:
        return "WATCH"

    if edge >= 0.07 and confidence >= 80:
        return "BUY YES"
    if edge <= -0.07 and confidence >= 80:
        return "BUY NO"

    if edge >= 0.04 and confidence >= 72:
        return "LEAN YES"
    if edge <= -0.04 and confidence >= 72:
        return "LEAN NO"

    return "PASS"


def grade_from_score(score, recommendation="PASS", confidence=0, risk="HIGH"):
    score = clamp(score)
    recommendation = str(recommendation or "PASS").upper()
    risk = str(risk or "HIGH").upper()
    confidence = safe_float(confidence)

    # Hard cap non-actionable cards.
    if recommendation in ("PASS", "WATCH"):
        if score >= 72:
            score = 71.9

    # Hard cap weak confidence.
    if confidence < 65:
        score = min(score, 63.9)
    elif confidence < 72:
        score = min(score, 74.9)
    elif confidence < 80:
        score = min(score, 83.9)

    # Hard cap high risk.
    if risk == "HIGH":
        score = min(score, 74.9)

    # A grades require real actionability.
    if score >= 92 and recommendation in ("BUY YES", "BUY NO") and confidence >= 85 and risk != "HIGH":
        return "A+"
    if score >= 88 and recommendation in ("BUY YES", "BUY NO") and confidence >= 82 and risk != "HIGH":
        return "A"
    if score >= 84 and recommendation in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO") and confidence >= 78:
        return "A-"
    if score >= 78:
        return "B+"
    if score >= 72:
        return "B"
    if score >= 66:
        return "B-"
    if score >= 58:
        return "C"
    return "PASS"


def build_reason(market, cls, fair_value, edge, confidence, research):
    lines = []

    lines.append(f"Classified as {cls.get('domain')} / {cls.get('subtype')}.")
    lines.append(f"Relevant providers: {', '.join(providers_for_classification(cls)[:6])}.")

    if source_quality_score(market) >= 80:
        lines.append("Strong settlement/source quality detected.")

    if liquidity_score(market) >= 75:
        lines.append("Good open interest / activity profile.")

    if price_quality_score(market) >= 80:
        lines.append("Tight tradable bid/ask structure.")

    momentum = momentum_signal(market)
    if momentum >= 0.03:
        lines.append("Recent price momentum is positive.")
    elif momentum <= -0.03:
        lines.append("Recent price momentum is negative.")

    if abs(edge) < 0.03:
        lines.append("No large fair-value gap yet; pass/watch until external provider evidence improves.")
    elif edge > 0:
        lines.append("Estimated fair value is above market price.")
    else:
        lines.append("Estimated fair value is below market price.")

    return "\n".join(f"• {x}" for x in lines)



def actionability_rank_score(card):
    """
    ORACLE-040.2:
    Rank score prioritizes actionable cards over raw score.
    PASS/WATCH cannot outrank good LEAN/BUY cards just because raw score is high.
    """
    rec = str(card.get("recommendation") or "PASS").upper()
    risk = str(card.get("risk") or "HIGH").upper()

    raw_score = safe_float(card.get("opportunity_score"))
    confidence = safe_float(card.get("confidence"))
    research = safe_float(card.get("research_score"))
    edge_abs = abs(safe_float(card.get("edge")))

    rank = 0.0

    if rec in ("BUY YES", "BUY NO"):
        rank += 50
    elif rec in ("LEAN YES", "LEAN NO"):
        rank += 30
    elif rec == "WATCH":
        rank += 8
    else:
        rank += 0

    rank += raw_score * 0.35
    rank += confidence * 0.25
    rank += research * 0.20
    rank += min(edge_abs * 400, 20)

    if risk == "LOW":
        rank += 10
    elif risk == "MEDIUM":
        rank += 3
    else:
        rank -= 12

    if rec in ("PASS", "WATCH"):
        rank = min(rank, 59.9)

    return round(clamp(rank), 2)


def analyze_market(market):
    cls = classify_market(market)
    price = moneyline_price(market)
    fair_value = estimate_fair_value(market, cls)
    edge = round(fair_value - price, 4)
    confidence = confidence_score(market, cls)
    research = research_score(market, cls)

    liq = liquidity_score(market)
    pxq = price_quality_score(market)

    risk = "LOW" if confidence >= 82 and liq >= 70 else "MEDIUM" if confidence >= 70 else "HIGH"

    # Calibrated opportunity score:
    # Edge helps, but cannot dominate weak confidence / high risk.
    opportunity_score = clamp(
        abs(edge) * 260
        + confidence * 0.30
        + research * 0.30
        + liq * 0.25
        + pxq * 0.15
    )

    # Penalize purely speculative long-dated markets.
    close_time = str(market.get("close_time") or market.get("expiration_time") or "")
    if any(year in close_time for year in ["2030", "2031", "2035", "2040", "2099"]):
        opportunity_score = min(opportunity_score, 76)

    recommendation = recommendation_from_edge(edge, confidence)
    grade = grade_from_score(opportunity_score, recommendation=recommendation, confidence=confidence, risk=risk)

    card = {
        "ticker": market.get("ticker"),
        "title": market.get("title"),
        "event_title": market.get("event_title"),
        "category": market.get("category"),
        "classification": cls,
        "providers_needed": providers_for_classification(cls),
        "market_price": price,
        "fair_value": fair_value,
        "edge": edge,
        "edge_pct": round(edge * 100, 2),
        "confidence": confidence,
        "research_score": research,
        "opportunity_score": round(opportunity_score, 2),
        "grade": grade,
        "recommendation": recommendation,
        "side": "YES" if edge > 0 else "NO" if edge < 0 else "WATCH",
        "risk": risk,
        "source_quality": source_quality_score(market),
        "liquidity_score": liquidity_score(market),
        "price_quality": price_quality_score(market),
        "spread": spread_width(market),
        "open_interest": safe_float(market.get("open_interest")),
        "volume_24h": safe_float(market.get("volume_24h")),
        "reason": build_reason(market, cls, fair_value, edge, confidence, research),
        "raw_market": market,
        "created_at": now(),
    }

    card["rank_score"] = actionability_rank_score(card)
    return card


def load_markets(limit=500):
    if not UNIVERSE_FILE.exists():
        return []

    data = json.loads(UNIVERSE_FILE.read_text(encoding="utf-8"))
    markets = data.get("markets", [])

    if not isinstance(markets, list):
        return []

    return markets[:int(limit)]


def analyze_universe(limit=500, top=25):
    markets = load_markets(limit=limit)
    cards = [analyze_market(m) for m in markets]

    cards.sort(
        key=lambda x: (
            x.get("rank_score", 0),
            x.get("opportunity_score", 0),
            abs(x.get("edge", 0)),
            x.get("confidence", 0),
        ),
        reverse=True,
    )

    payload = {
        "version": "ORACLE-040",
        "updated_at": now(),
        "market_count": len(markets),
        "card_count": len(cards),
        "top_count": min(top, len(cards)),
        "cards": cards[:int(top)],
    }

    INTELLIGENCE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_top_intelligence(limit=10):
    """
    ORACLE-040.3:
    Top intelligence means actionable first.
    PASS cards are hidden from Top 10.
    """
    return get_actionable_intelligence(limit=limit)



def is_actionable_card(card):
    rec = str(card.get("recommendation") or "").upper()
    return rec in ("BUY YES", "BUY NO", "LEAN YES", "LEAN NO")


def get_actionable_intelligence(limit=10):
    if not INTELLIGENCE_FILE.exists():
        analyze_universe(top=50)

    data = json.loads(INTELLIGENCE_FILE.read_text(encoding="utf-8"))
    cards = data.get("cards", [])

    actionable = [c for c in cards if is_actionable_card(c)]
    watch = [c for c in cards if str(c.get("recommendation") or "").upper() == "WATCH"]

    ordered = actionable + watch

    return ordered[:int(limit)]


def format_card(card, rank=None):
    rank_line = f"Rank #{rank}" if rank else "Market Intelligence"

    return f"""
🧠 ORACLE MARKET INTELLIGENCE

{rank_line}

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Class:
{card.get("classification", {}).get("domain")} / {card.get("classification", {}).get("subtype")}

Recommendation:
{card.get("recommendation")}

Grade:
{card.get("grade")}

Market Price:
{card.get("market_price")}

Oracle Fair Value:
{card.get("fair_value")}

Edge:
{card.get("edge_pct")}%

Confidence:
{card.get("confidence")}

Research Score:
{card.get("research_score")}

Opportunity Score:
{card.get("opportunity_score")}

Rank Score:
{card.get("rank_score")}

Risk:
{card.get("risk")}

Reason:
{card.get("reason")}
""".strip()


def format_top(cards=None, limit=10):
    cards = cards if cards is not None else get_top_intelligence(limit=limit)

    if not cards:
        return "No Oracle market intelligence cards found."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_card(card, rank=i)
        for i, card in enumerate(cards[:int(limit)], start=1)
    )


def diagnostics():
    payload = analyze_universe(limit=500, top=25)

    return {
        "module": "oracle_market_intelligence",
        "status": "ok",
        "market_count": payload.get("market_count"),
        "cards": payload.get("card_count"),
        "top": [
            {
                "ticker": c.get("ticker"),
                "grade": c.get("grade"),
                "recommendation": c.get("recommendation"),
                "score": c.get("opportunity_score"),
                "edge_pct": c.get("edge_pct"),
                "class": c.get("classification"),
            }
            for c in get_top_intelligence(limit=5)
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top(limit=5))
