from qseries_v2.oi.recommendation_engine import recommendation_engine

rec = recommendation_engine.recommend(
    ticker="TEST-MARKET",
    market_yes_price=80,
    fair_yes_price=91.67,
    confidence=91.67,
)

assert rec["action"] == "BUY_YES"
assert rec["oracle_executes"] is False
assert rec["edge"] > 0

print("[PASS] OI-004 Recommendation Engine")
print(rec)
