from pathlib import Path

root = Path.cwd()

risk_file = root / "oracle_risk_engine.py"
engine_file = root / "oracle_research_engine.py"

risk_code = r'''
"""
ORACLE-038 — Risk Engine

Purpose:
Assign a standardized Oracle risk profile to every opportunity.
"""


def calculate_risk(market):

    market = dict(market)

    confidence = float(market.get("oracle_confidence", 0))
    edge = abs(float(market.get("oracle_edge", 0)))
    liquidity = float(market.get("liquidity", 0))
    volume = float(market.get("volume", 0))

    score = 100.0

    if confidence < 90:
        score -= (90 - confidence) * 0.40

    if edge < 2:
        score -= (2 - edge) * 8

    if liquidity < 1000:
        score -= 10

    if volume < 5000:
        score -= 10

    score = max(0.0, min(100.0, score))

    if score >= 90:
        level = "VERY LOW"
    elif score >= 80:
        level = "LOW"
    elif score >= 65:
        level = "MEDIUM"
    elif score >= 50:
        level = "HIGH"
    else:
        level = "VERY HIGH"

    market["oracle_risk_score"] = round(score, 2)
    market["oracle_risk"] = level

    return market


def apply_risk(markets):
    return [calculate_risk(m) for m in markets]
'''

risk_file.write_text(risk_code, encoding="utf-8")

print("[OK] Created oracle_risk_engine.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle038_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_risk_engine import apply_risk" not in text:
    text = "from oracle_risk_engine import apply_risk\n" + text

old = """
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)
            ranked = apply_trade_decisions(ranked)

            self.snapshot["opportunities"] = ranked[:25]
"""

new = """
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)
            ranked = apply_trade_decisions(ranked)
            ranked = apply_risk(ranked)

            self.snapshot["opportunities"] = ranked[:25]
"""

if old in text:
    text = text.replace(old, new, 1)
else:
    print("[WARN] Expected pipeline block not found. Import/file created only.")

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-038 Risk Engine installed")