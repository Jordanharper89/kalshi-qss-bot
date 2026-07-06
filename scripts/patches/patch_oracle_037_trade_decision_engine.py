from pathlib import Path

root = Path.cwd()

decision_file = root / "oracle_trade_decision_engine.py"
engine_file = root / "oracle_research_engine.py"

decision_code = r'''
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
'''

decision_file.write_text(decision_code, encoding="utf-8")

print("[OK] Created oracle_trade_decision_engine.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle037_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_trade_decision_engine import apply_trade_decisions" not in text:
    text = (
        "from oracle_trade_decision_engine import apply_trade_decisions\n"
        + text
    )

old = '''
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

new = '''
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)
            ranked = apply_trade_decisions(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

if old in text:
    text = text.replace(old, new, 1)
else:
    print("[WARN] Expected pipeline block not found. Import/file created only.")

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-037 Trade Decision Engine installed")