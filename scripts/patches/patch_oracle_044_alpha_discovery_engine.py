from pathlib import Path

TARGET = Path("oracle_alpha_discovery.py")

TARGET.write_text(r'''
"""
ORACLE-044 — Alpha Discovery Engine

Purpose:
- Explain WHY a prediction market may be mispriced
- Convert final fusion cards into alpha discovery reports
- Identify catalyst type, likely data sources, market reaction quality, alpha score, and urgency
- Safe: no trades, no orders
"""

import json
import time
from pathlib import Path
from math import isfinite

from oracle_final_fusion import run_final_fusion, get_top_final

ALPHA_FILE = Path("oracle_alpha_discovery.json")


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


def get_raw_market(card):
    raw_market = card.get("raw_market")
    if isinstance(raw_market, dict):
        return raw_market

    raw = card.get("raw")
    if isinstance(raw, dict):
        rm = raw.get("raw_market")
        if isinstance(rm, dict):
            return rm

    return {}


def get_event(card):
    raw_market = get_raw_market(card)
    event = raw_market.get("event")
    return event if isinstance(event, dict) else {}


def get_classification(card):
    cls = card.get("classification")
    if isinstance(cls, dict):
        return cls

    raw = card.get("raw")
    if isinstance(raw, dict) and isinstance(raw.get("classification"), dict):
        return raw.get("classification")

    return {
        "domain": "unknown",
        "subtype": "general",
        "category": card.get("category", "unknown"),
    }


def text_blob(card):
    raw_market = get_raw_market(card)
    raw = raw_market.get("raw", {}) if isinstance(raw_market.get("raw"), dict) else {}
    event = get_event(card)

    parts = [
        card.get("ticker", ""),
        card.get("title", ""),
        card.get("event_title", ""),
        card.get("category", ""),
        raw.get("rules_primary", ""),
        raw.get("rules_secondary", ""),
        raw.get("yes_sub_title", ""),
        raw.get("no_sub_title", ""),
        event.get("title", ""),
        event.get("sub_title", ""),
    ]

    return " ".join(str(x or "") for x in parts).lower()


def settlement_sources(card):
    event = get_event(card)
    sources = event.get("settlement_sources")
    return sources if isinstance(sources, list) else []


def source_names(card):
    names = []
    for src in settlement_sources(card):
        if isinstance(src, dict):
            name = src.get("name")
            if name:
                names.append(str(name))
    return names


def identify_catalyst(card):
    blob = text_blob(card)
    cls = get_classification(card)
    domain = str(cls.get("domain", "unknown"))

    if any(x in blob for x in ["ipo", "sec", "filing", "nasdaq", "nyse", "shares"]):
        return {
            "type": "SEC / listing catalyst",
            "sources": ["SEC EDGAR", "NYSE", "NASDAQ", "Reuters", "Bloomberg"],
        }

    if any(x in blob for x in ["agi", "openai", "anthropic", "artificial intelligence"]):
        return {
            "type": "AI announcement catalyst",
            "sources": ["Company announcements", "Reuters", "Bloomberg", "SEC", "The Information"],
        }

    if any(x in blob for x in ["election", "prime minister", "president", "parliament", "seat", "vote"]):
        return {
            "type": "political outcome catalyst",
            "sources": ["Official election sources", "AP", "Reuters", "polling", "local news"],
        }

    if any(x in blob for x in ["temperature", "snow", "rain", "hurricane", "storm", "earthquake"]):
        return {
            "type": "weather/geological catalyst",
            "sources": ["NOAA", "NWS", "USGS", "official weather data"],
        }

    if any(x in blob for x in ["nba", "nfl", "mlb", "pga", "golf", "f1", "soccer", "championship", "retire"]):
        return {
            "type": "sports information catalyst",
            "sources": ["Sports odds", "official league sources", "injury/news reports", "ESPN"],
        }

    if any(x in blob for x in ["bitcoin", "crypto", "ethereum", "solana"]):
        return {
            "type": "crypto market catalyst",
            "sources": ["CoinGecko", "exchange prices", "funding rates", "liquidations", "news"],
        }

    return {
        "type": f"{domain} catalyst",
        "sources": ["official sources", "news", "market movement"],
    }


def market_reaction_score(card):
    edge = abs(safe_float(card.get("edge")))
    final_score = safe_float(card.get("final_score"))
    evidence_score = safe_float(card.get("evidence_score"))
    confidence = safe_float(card.get("confidence"))
    price = safe_float(card.get("market_price"))

    score = 50

    if edge >= 0.08:
        score += 20
    elif edge >= 0.05:
        score += 12
    elif edge >= 0.035:
        score += 7
    else:
        score -= 12

    if confidence >= 85:
        score += 10
    elif confidence < 65:
        score -= 12

    if evidence_score >= 85:
        score += 8
    elif evidence_score < 55:
        score -= 10

    if 0.08 <= price <= 0.92:
        score += 4
    else:
        score -= 6

    if final_score >= 80:
        score += 8
    elif final_score < 55:
        score -= 8

    return round(clamp(score), 2)


def alpha_source_gap(card):
    """
    Measures whether Oracle knows which outside data sources matter but has not yet verified them.
    A large gap means there may be alpha if external data confirms the thesis.
    """
    catalyst = identify_catalyst(card)
    needed = catalyst.get("sources", [])
    settlement = source_names(card)

    settlement_text = " ".join(settlement).lower()
    missing = []

    for src in needed:
        src_l = src.lower()
        if src_l not in settlement_text:
            missing.append(src)

    gap_score = min(len(missing) * 8, 32)

    return {
        "missing_sources": missing,
        "gap_score": gap_score,
    }


def alpha_risk_penalty(card):
    penalty = 0
    risks = []

    raw_market = get_raw_market(card)
    spread = safe_float(card.get("spread"))
    liquidity_score = safe_float(card.get("liquidity_score"))
    price = safe_float(card.get("market_price"))
    close_time = str(raw_market.get("close_time") or raw_market.get("expiration_time") or "")

    if spread >= 0.15:
        penalty += 18
        risks.append("Very wide spread")
    elif spread >= 0.08:
        penalty += 9
        risks.append("Moderate spread risk")

    if liquidity_score < 55:
        penalty += 12
        risks.append("Thin liquidity/activity")

    if price <= 0.03 or price >= 0.97:
        penalty += 10
        risks.append("Extreme price risk")

    if any(year in close_time for year in ["2035", "2040", "2045", "2099"]):
        penalty += 14
        risks.append("Very long-dated market")
    elif any(year in close_time for year in ["2030", "2031"]):
        penalty += 7
        risks.append("Long-dated market")

    return {
        "penalty": penalty,
        "risks": risks,
    }


def alpha_urgency(card):
    final_rec = str(card.get("final_recommendation") or "PASS").upper()
    edge = abs(safe_float(card.get("edge")))
    spread = safe_float(card.get("spread"))
    score = safe_float(card.get("final_score"))

    if final_rec in ("BUY YES", "BUY NO") and score >= 85:
        return "HIGH"

    if final_rec in ("LEAN YES", "LEAN NO") and edge >= 0.04 and spread <= 0.06:
        return "MEDIUM"

    if final_rec == "WATCH":
        return "LOW"

    return "NONE"


def discover_alpha(card):
    catalyst = identify_catalyst(card)
    reaction = market_reaction_score(card)
    gap = alpha_source_gap(card)
    risk = alpha_risk_penalty(card)

    final_score = safe_float(card.get("final_score"))
    evidence_score = safe_float(card.get("evidence_score"))
    similarity_adjustment = safe_float(card.get("similarity_adjustment"))

    alpha_score = clamp(
        final_score * 0.35
        + evidence_score * 0.25
        + reaction * 0.25
        + gap.get("gap_score", 0) * 0.15
        + similarity_adjustment
        - risk.get("penalty", 0)
    )

    output = dict(card)
    output["alpha_catalyst"] = catalyst
    output["market_reaction_score"] = reaction
    output["alpha_source_gap"] = gap
    output["alpha_risk"] = risk
    output["alpha_score"] = round(alpha_score, 2)
    output["alpha_urgency"] = alpha_urgency(card)
    output["alpha_summary"] = build_alpha_summary(output)
    output["alpha_created_at"] = now()

    return output


def build_alpha_summary(card):
    catalyst = card.get("alpha_catalyst", {})
    gap = card.get("alpha_source_gap", {})
    risk = card.get("alpha_risk", {})

    lines = []

    lines.append(f"{card.get('ticker')}: {card.get('final_recommendation')} / {card.get('final_grade')}")
    lines.append(f"Alpha Score: {card.get('alpha_score')}")
    lines.append(f"Urgency: {card.get('alpha_urgency')}")
    lines.append(f"Catalyst Type: {catalyst.get('type')}")
    lines.append("")

    lines.append("Why this may be mispriced:")
    edge_pct = round(safe_float(card.get("edge")) * 100, 2)
    lines.append(f"• Oracle estimated edge is {edge_pct}%.")
    lines.append(f"• Evidence score is {card.get('evidence_score')}.")
    lines.append(f"• Market reaction score is {card.get('market_reaction_score')}.")

    missing = gap.get("missing_sources", [])
    if missing:
        lines.append(f"• Alpha source gap: needs confirmation from {', '.join(missing[:4])}.")
    else:
        lines.append("• Settlement/source coverage is already strong.")

    risks = risk.get("risks", [])
    if risks:
        lines.append("")
        lines.append("Main risks:")
        for item in risks[:4]:
            lines.append(f"• {item}")

    lines.append("")
    lines.append("Next research sources:")
    for src in catalyst.get("sources", [])[:6]:
        lines.append(f"• {src}")

    return "\n".join(lines)


def run_alpha_discovery(limit=50):
    run_final_fusion(limit=limit)
    cards = get_top_final(limit=limit)

    alpha_cards = [discover_alpha(card) for card in cards]

    alpha_cards.sort(
        key=lambda x: (
            x.get("alpha_score", 0),
            x.get("final_rank_score", 0),
            x.get("final_score", 0),
        ),
        reverse=True,
    )

    payload = {
        "version": "ORACLE-044",
        "updated_at": now(),
        "count": len(alpha_cards),
        "cards": alpha_cards,
    }

    ALPHA_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def get_top_alpha(limit=10):
    if not ALPHA_FILE.exists():
        run_alpha_discovery(limit=max(50, limit))

    try:
        data = json.loads(ALPHA_FILE.read_text(encoding="utf-8"))
        cards = data.get("cards", [])
        return cards[:int(limit)]
    except Exception:
        return []


def format_alpha_card(card, rank=None):
    rank_line = f"Rank #{rank}" if rank else "Alpha Card"

    return f"""
⚡ ORACLE ALPHA DISCOVERY

{rank_line}

Ticker:
{card.get("ticker")}

Title:
{card.get("title")}

Final Recommendation:
{card.get("final_recommendation")}

Final Grade:
{card.get("final_grade")}

Alpha Score:
{card.get("alpha_score")}

Urgency:
{card.get("alpha_urgency")}

Catalyst:
{card.get("alpha_catalyst", {}).get("type")}

Final Score:
{card.get("final_score")}

Evidence Score:
{card.get("evidence_score")}

Market Price:
{card.get("market_price")}

Fair Value:
{card.get("fair_value")}

Edge:
{round(safe_float(card.get("edge")) * 100, 2)}%

Alpha Summary:
{card.get("alpha_summary")}
""".strip()


def format_top_alpha(limit=10):
    cards = get_top_alpha(limit=limit)

    if not cards:
        return "No Oracle alpha discovery cards found."

    return "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_alpha_card(card, rank=i)
        for i, card in enumerate(cards[:int(limit)], start=1)
    )


def diagnostics():
    payload = run_alpha_discovery(limit=50)

    return {
        "module": "oracle_alpha_discovery",
        "status": "ok",
        "cards": payload.get("count"),
        "top": [
            {
                "ticker": c.get("ticker"),
                "recommendation": c.get("final_recommendation"),
                "grade": c.get("final_grade"),
                "alpha_score": c.get("alpha_score"),
                "urgency": c.get("alpha_urgency"),
                "catalyst": c.get("alpha_catalyst", {}).get("type"),
            }
            for c in payload.get("cards", [])[:5]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2))
    print()
    print(format_top_alpha(limit=5))
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-044 INSTALLED")
print(" Alpha Discovery Engine")
print("===================================")
print()
print("Created:")
print(" oracle_alpha_discovery.py")
print()
print("Test:")
print(" python oracle_alpha_discovery.py")