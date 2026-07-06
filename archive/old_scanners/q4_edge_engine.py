import requests

from config import BASE_URL
from grading import to_cents, to_float
from probability_engine import probability_from_signals
from edge_engine import analyze_market
from sports_engine import sports_probability
from sport_router import detect_sport
from category_validator import validate_category
from weather_engine import weather_probability


MIN_ENTRY_PRICE = 8
MAX_ENTRY_PRICE = 75
MAX_SPREAD = 8


def kalshi_url(ticker):
    return f"https://kalshi.com/markets/{str(ticker).lower()}"


def snapshot(market):
    yes_bid = to_cents(market.get("yes_bid_dollars"))
    yes_ask = to_cents(market.get("yes_ask_dollars"))
    last = to_cents(market.get("last_price_dollars"))
    previous = to_cents(market.get("previous_price_dollars"))

    return {
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "spread": yes_ask - yes_bid,
        "move": abs(last - previous),
        "last": last,
        "previous": previous,
        "volume_24h": to_float(market.get("volume_24h_fp")),
        "volume_total": to_float(market.get("volume_fp")),
    }


def detect_category(text):
    t = str(text or "").lower()

    if any(x in t for x in ["btc", "bitcoin", "eth", "ethereum", "sol", "solana"]):
        return "crypto"

    if any(x in t for x in [
        "mlb", "baseball", "nba", "basketball", "nfl", "football",
        "nhl", "hockey", "soccer", "world cup", "fifa", "tennis",
        "golf", "rugby", "lacrosse", "winner", "game"
    ]):
        return "sports"

    if any(x in t for x in ["temperature", "temp", "rain", "weather", "snow", "wind", "high", "low"]):
        return "weather"

    if any(x in t for x in ["trump", "election", "poll", "approval", "senate", "president", "governor", "nominee"]):
        return "politics"

    if any(x in t for x in ["song", "album", "billboard", "spotify", "movie", "box office"]):
        return "entertainment"

    if any(x in t for x in ["tesla", "spacex", "starship", "launch"]):
        return "tesla_spacex"

    return "general"


def choose_side(snap):
    side = "BUY YES"
    market_price = snap["yes_ask"]

    if 76 <= snap["yes_ask"] <= 92:
        no_price = round(100 - snap["yes_bid"], 1)
        if 8 <= no_price <= 30:
            side = "BUY NO"
            market_price = no_price

    return side, market_price


def bot_probability_for_market(market, snap, category, side, market_price):
    title = market.get("title", "")
    series_title = market.get("series_title", "")
    title_blob = f"{title} {market.get('ticker')} {market.get('category')} {series_title}"

    if category == "sports":
        result = sports_probability(
            market_price=market_price,
            market_title=title_blob,
            spread=snap["spread"],
            move=snap["move"],
            volume_24h=snap["volume_24h"],
        )
        return {
            "bot_probability": result["bot_probability"],
            "reasons": result.get("reasons", []),
            "component_scores": result.get("component_scores", {}),
        }

    if category == "weather":
        result = weather_probability(
            market_price=market_price,
            spread=snap["spread"],
            move=snap["move"],
            volume_24h=snap["volume_24h"],
            title=title,
            series_title=series_title,
        )
        return {
            "bot_probability": result["bot_probability"],
            "reasons": result.get("reasons", []),
            "component_scores": result.get("component_scores", {}),
        }

    result = probability_from_signals(
        market_price=market_price,
        category=category,
        spread=snap["spread"],
        volume_24h=snap["volume_24h"],
        volume_total=snap["volume_total"],
        move=snap["move"],
        source_strength="None",
        side=side,
    )

    return {
        "bot_probability": result["bot_probability"],
        "reasons": result.get("probability_reasons", []),
        "component_scores": {},
    }


def score_market(market):
    snap = snapshot(market)

    if snap["yes_bid"] <= 0 or snap["yes_ask"] <= 0:
        return None

    if snap["spread"] <= 0 or snap["spread"] > MAX_SPREAD:
        return None

    title_blob = f"{market.get('title')} {market.get('ticker')} {market.get('category')} {market.get('series_title', '')}"
    category = detect_category(title_blob)
    sport = detect_sport(title_blob) if category == "sports" else None

    validation = validate_category(category, sport)

    if not validation["valid"]:
        return None

    side, market_price = choose_side(snap)

    if market_price < MIN_ENTRY_PRICE or market_price > MAX_ENTRY_PRICE:
        return None

    prob = bot_probability_for_market(
        market=market,
        snap=snap,
        category=category,
        side=side,
        market_price=market_price,
    )

    edge = analyze_market(
        bot_probability=prob["bot_probability"],
        market_probability=market_price,
    )

    if edge["grade"] not in ["A-", "A", "A+"]:
        return None

    return {
        "title": market.get("title"),
        "ticker": market.get("ticker"),
        "url": kalshi_url(market.get("ticker")),
        "category": category,
        "sport": sport,
        "validation_reason": validation["reason"],
        "side": side,
        "bot_probability": edge["bot_probability"],
        "market_probability": edge["market_probability"],
        "edge": edge["edge"],
        "grade": edge["grade"],
        "score": edge["score"],
        "decision": edge["decision"],
        "rules": edge["rules"],
        "reasons": prob["reasons"],
        "component_scores": prob["component_scores"],
        "snap": snap,
    }


if __name__ == "__main__":
    print("q4_edge_engine loaded")