from qseries_v2.oi.learning_ledger import LearningLedger
from qseries_v2.oi.performance_review import performance_review_engine

ledger = LearningLedger()

rec1 = {
    "ticker": "TEST-1",
    "action": "BUY_YES",
    "confidence": 90,
    "fair_yes_price": 90,
    "market_yes_price": 80,
    "edge": 10,
}

rec2 = {
    "ticker": "TEST-2",
    "action": "BUY_NO",
    "confidence": 70,
    "fair_yes_price": 30,
    "market_yes_price": 40,
    "edge": -10,
}

ledger.record_recommendation(rec1)
ledger.record_recommendation(rec2)

ledger.resolve("TEST-1", "YES")
ledger.resolve("TEST-2", "YES")

review = performance_review_engine.review(ledger.records)

assert review["total_records"] == 2
assert review["wins"] == 1
assert review["losses"] == 1
assert review["win_rate"] == 50.0

print("[PASS] OI-008 Performance Review Engine")
print(review)
