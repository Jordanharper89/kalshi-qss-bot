from pathlib import Path

root = Path.cwd()

fair_file = root / "oracle_fair_value_engine.py"
engine_file = root / "oracle_research_engine.py"

fair_code = r'''
"""
ORACLE-035 — Fair Value Engine

Purpose:
- Estimate Oracle fair value for every normalized market.
- Future versions will use historical data, news, weather,
  sentiment, volatility, and custom models.
"""

def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def calculate_fair_value(market):

    yes = float(market.get("yes_price", 0))
    volume = float(market.get("volume", 0))
    liquidity = float(market.get("liquidity", 0))

    adjustment = 0.0

    if volume > 50000:
        adjustment += 2.5
    elif volume > 10000:
        adjustment += 1.0

    if liquidity > 10000:
        adjustment += 2.0
    elif liquidity > 2500:
        adjustment += 0.5

    fair = clamp(yes + adjustment)

    edge = round(fair - yes, 2)

    market = dict(market)

    market["oracle_fair_value"] = round(fair, 2)
    market["oracle_edge"] = edge

    return market


def apply_fair_values(markets):

    output = []

    for market in markets:
        output.append(calculate_fair_value(market))

    return output
'''

fair_file.write_text(fair_code, encoding="utf-8")

print("[OK] Created oracle_fair_value_engine.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle035_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_fair_value_engine import apply_fair_values" not in text:
    text = (
        "from oracle_fair_value_engine import apply_fair_values\n"
        + text
    )

old = '''
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

new = '''
            ranked = apply_fair_values(ranked)
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

if old in text:
    text = text.replace(old, new)

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-035 Fair Value Engine installed")