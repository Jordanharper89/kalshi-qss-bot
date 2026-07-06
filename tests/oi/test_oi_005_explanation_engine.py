from qseries_v2.oi.explanation_engine import explanation_engine

recommendation = {
    "ticker": "TEST-MARKET",
    "action": "BUY_YES",
    "market_yes_price": 80.0,
    "fair_yes_price": 91.67,
    "edge": 11.67,
    "confidence": 91.67,
    "reason": "Fair value is meaningfully above market price.",
    "oracle_executes": False,
}

text = explanation_engine.explain(recommendation)

assert "TEST-MARKET" in text
assert "BUY_YES" in text
assert "Q Series handles execution" in text

print("[PASS] OI-005 Explanation Engine")
print(text)
