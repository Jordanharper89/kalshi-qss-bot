from qseries_v2.oi.learning_ledger import LearningLedger
from qseries_v2.oi.learning_loop import oracle_learning_loop

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
    "action": "BUY_YES",
    "confidence": 82,
    "fair_yes_price": 82,
    "market_yes_price": 76,
    "edge": 6,
}

ledger.record_recommendation(rec1)
ledger.record_recommendation(rec2)

ledger.resolve("TEST-1", "YES")
ledger.resolve("TEST-2", "NO")

result = oracle_learning_loop.run(ledger.records)

assert result["performance"]["total_records"] == 2
assert result["performance"]["wins"] == 1
assert result["performance"]["losses"] == 1
assert result["oracle_executes"] is False
assert "adjustments" in result["feedback"]

print("[PASS] OI-010 Oracle Learning Loop")
print(result)
