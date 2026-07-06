import sys
import re
import requests
from datetime import datetime, timezone

from config import BASE_URL
from q4_edge_engine import score_market, snapshot
from q5_volume_scalp import q5_scalp_score
from q6_trend_filter import q6_trend_score
from final_trade_decision import final_trade_decision
from ticker_diagnoser import diagnose_market
from market_memory import remember_market, get_window_volume, get_price_change


def extract_ticker(text):
    raw = str(text or "").strip()

    if "op_market_ticker=" in raw:
        match = re.search(r"op_market_ticker=([^&\s]+)", raw, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper()

    if "kalshi.com" not in raw.lower():
        return raw.upper()

    raw = raw.split("?")[0].rstrip("/")
    parts = raw.split("/")

    for part in reversed(parts):
        part = part.strip()
        if "-" in part and any(c.isdigit() for c in part):
            return part.upper()

    return raw.upper()


def cents(value):
    if value is None:
        return None

    try:
        value = float(value)
        if value <= 1:
            value *= 100
        return round(value, 1)
    except Exception:
        return None


def get_market(ticker):
    response = requests.get(f"{BASE_URL}/markets/{ticker}", timeout=20)

    if response.status_code != 200:
        return None

    return response.json().get("market")


def minutes_until_close(market):
    close_time = market.get("close_time") or market.get("expiration_time")

    if not close_time:
        return None

    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    return int((close_dt - now).total_seconds() / 60)


def grade(score):
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "A-"
    if score >= 60:
        return "B+"
    return "PASS"


def get_yes_no_prices(market, snap):
    yes_bid = cents(snap.get("yes_bid"))
    yes_ask = cents(snap.get("yes_ask"))

    no_bid = cents(market.get("no_bid"))
    no_ask = cents(market.get("no_ask"))

    if no_ask is None and yes_bid is not None:
        no_ask = round(100 - yes_bid, 1)

    if no_bid is None and yes_ask is not None:
        no_bid = round(100 - yes_ask, 1)

    return {
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
    }


def score_5m_volume(volume_5m, valid):
    if not valid:
        return 50, "building"

    if volume_5m >= 50000:
        return 98, "explosive"
    if volume_5m >= 20000:
        return 90, "heavy"
    if volume_5m >= 7500:
        return 78, "strong"
    if volume_5m >= 2500:
        return 65, "usable"
    if volume_5m >= 500:
        return 50, "light"

    return 30, "weak"


def score_momentum(price_change_5m, valid, move):
    score = 35
    reason = "flat"

    if move >= 20:
        score = 90
        reason = "explosive"
    elif move >= 10:
        score = 80
        reason = "strong"
    elif move >= 5:
        score = 68
        reason = "building"

    if valid:
        if price_change_5m >= 10:
            score += 15
            reason = "5m acceleration"
        elif price_change_5m >= 5:
            score += 10
            reason = "5m building"
        elif price_change_5m <= -8:
            score -= 15
            reason = "fading"

    return max(0, min(100, round(score, 1))), reason


def score_clock(minutes_left):
    if minutes_left is None:
        return 50, "unknown"

    if 5 <= minutes_left <= 20:
        return 90, "prime"
    if 2 <= minutes_left < 5:
        return 72, "fast"
    if 20 < minutes_left <= 60:
        return 75, "good"
    if minutes_left < 2:
        return 25, "risky"

    return 55, "long"


def build_trade_scan(user_input):
    ticker = extract_ticker(user_input)
    market = get_market(ticker)

    if not market:
        return f"TICKER NOT FOUND\nTicker: {ticker}"

    snap = snapshot(market)
    prices = get_yes_no_prices(market, snap)
    minutes_left = minutes_until_close(market)

    remember_market(
        ticker=ticker,
        price=snap["last"],
        volume_24h=snap["volume_24h"],
        bid=snap["yes_bid"],
        ask=snap["yes_ask"],
    )

    vol5 = get_window_volume(ticker, window_seconds=300)
    chg5 = get_price_change(ticker, window_seconds=300)

    q4 = score_market(market)
    diagnosis = diagnose_market(market)

    if not q4:
        return f"""
TRADE SCAN
{ticker}

NO TRADE

Reason: {diagnosis.get("reason")}

YES: {prices["yes_ask"]}c
NO: {prices["no_ask"]}c
Spread: {snap["spread"]}c
Clock: {minutes_left}m
""".strip()

    q5 = q5_scalp_score(
        market_probability=q4["market_probability"],
        bot_probability=q4["bot_probability"],
        spread=snap["spread"],
        volume_24h=snap["volume_24h"],
        move=snap["move"],
        minutes_left=minutes_left,
        side=None,
    )

    q6 = q6_trend_score(
        current_price=None,
        target_price=None,
        market_probability=q4["market_probability"],
        move=snap["move"],
        volume_24h=snap["volume_24h"],
        minutes_left=minutes_left,
        chart_bias="unknown",
    )

    final = final_trade_decision(
        q4_grade=q4["grade"],
        q4_edge=q4["edge"],
        q5_score=q5["q5_score"],
        q5_grade=q5["q5_grade"],
        q6_score=q6["q6_score"],
        q6_grade=q6["q6_grade"],
        market_probability=q4["market_probability"],
        minutes_left=minutes_left,
    )

    vol_score, vol_reason = score_5m_volume(vol5["window_volume"], vol5["valid"])
    mom_score, mom_reason = score_momentum(chg5["price_change"], chg5["valid"], snap["move"])
    clock_score, clock_reason = score_clock(minutes_left)

    confidence = round(
        (final["confidence"] * 0.45)
        + (vol_score * 0.20)
        + (mom_score * 0.25)
        + (clock_score * 0.10),
        1,
    )

    final_grade = grade(confidence)

    action = q5["side"]
    if action == "BUY YES":
        action_price = prices["yes_ask"]
        fair_value = q4["bot_probability"]
    elif action == "BUY NO":
        action_price = prices["no_ask"]
        fair_value = round(100 - q4["bot_probability"], 1)
    else:
        action_price = prices["yes_ask"]
        fair_value = q4["bot_probability"]

    if action_price is None:
        action_price = q4["market_probability"]

    target_1 = round(action_price + 10, 1)
    target_2 = round(action_price + 16, 1)
    stop = round(max(1, action_price - 5), 1)

    reasons = []

    if snap["spread"] <= 2:
        reasons.append("tight spread")

    if q4["edge"] >= 8:
        reasons.append("strong edge")

    reasons.append(f"momentum {mom_reason}")
    reasons.append(f"5m volume {vol_reason}")
    reasons.append(f"clock {clock_reason}")

    why = " | ".join(reasons[:5])

    return f"""
TRADE SCAN

{ticker}

FINAL: {final_grade} | {confidence}/100
ACTION: {action} @ {action_price}c
LEAN: {final["lean"]}

YES: {prices["yes_ask"]}c | NO: {prices["no_ask"]}c
Fair: {fair_value}c | Edge: +{q4["edge"]}c
Spread: {snap["spread"]}c | Clock: {minutes_left}m

Volume 24h: {snap["volume_24h"]}
5m Vol: {vol5["window_volume"]} | {vol_reason}
Momentum: {mom_reason}
Trend: {q6["trend"]}

PLAN:
Entry: {action_price}c
Target 1: {target_1}c
Target 2: {target_2}c
Stop: {stop}c

WHY:
{why}

Kalshi:
{q4["url"]}
""".strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trade_scan.py TICKER_OR_LINK")
    else:
        print(build_trade_scan(" ".join(sys.argv[1:])))