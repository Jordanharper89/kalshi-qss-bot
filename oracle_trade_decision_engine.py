
"""
ORACLE-037 — Trade Decision Engine

Purpose:
Convert Oracle analytics into actionable trade decisions.
This engine recommends BUY YES, BUY NO, WATCH, or PASS.
"""


def build_trade_decision(market):

    market = dict(market)

    yes_price = float(market.get("yes_price", 0))
    fair_value = float(market.get("oracle_fair_value", yes_price))
    edge = float(market.get("oracle_edge", 0))
    confidence = float(market.get("oracle_confidence", 0))

    decision = "PASS"

    if confidence >= 90 and edge >= 4:
        decision = "BUY YES"

    elif confidence >= 80 and edge >= 2:
        decision = "BUY YES"

    elif confidence >= 75 and edge <= -3:
        decision = "BUY NO"

    elif confidence >= 65:
        decision = "WATCH"

    market["oracle_decision"] = decision
    market["entry_price"] = yes_price
    market["target_price"] = round(fair_value, 2)
    market["expected_edge"] = round(edge, 2)

    return market


def apply_trade_decisions(markets):

    return [build_trade_decision(m) for m in markets]
