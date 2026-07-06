from qseries_v2.oi.learning_ledger import learning_ledger

recommendation = {
    "ticker": "TEST-MARKET",
    "action": "BUY_YES",
    "confidence": 91.67,
    "fair_yes_price": 91.67,
    "market_yes_price": 80.0,
    "edge": 11.67,
}

record = learning_ledger.record_recommendation(recommendation)
resolved = learning_ledger.resolve("TEST-MARKET", "YES")
summary = learning_ledger.summary()

assert record.ticker == "TEST-MARKET"
assert resolved.result == "win"
assert summary["wins"] == 1
assert summary["win_rate"] == 100.0

print("[PASS] OI-007 Learning Ledger")
print(summary)
