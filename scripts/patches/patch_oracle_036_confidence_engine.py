from pathlib import Path

root = Path.cwd()

confidence_file = root / "oracle_confidence_engine.py"
engine_file = root / "oracle_research_engine.py"

confidence_code = r'''
"""
ORACLE-036 — Confidence Engine

Purpose:
- Add Oracle confidence score to each opportunity.
"""

def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def calculate_confidence(market):

    score = float(market.get("oracle_score", 0))
    edge = abs(float(market.get("oracle_edge", 0)))
    volume = float(market.get("volume", 0))
    liquidity = float(market.get("liquidity", 0))

    confidence = 40.0

    confidence += score * 0.35
    confidence += min(edge * 4, 15)
    confidence += min(volume / 10000, 10)
    confidence += min(liquidity / 5000, 10)

    market = dict(market)
    market["oracle_confidence"] = round(clamp(confidence), 2)

    return market


def apply_confidence(markets):

    return [calculate_confidence(m) for m in markets]
'''

confidence_file.write_text(confidence_code, encoding="utf-8")

print("[OK] Created oracle_confidence_engine.py")

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle036_backup"
backup.write_text(text, encoding="utf-8")

if "from oracle_confidence_engine import apply_confidence" not in text:
    text = "from oracle_confidence_engine import apply_confidence\n" + text

old = '''
            ranked = apply_fair_values(ranked)
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

new = '''
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)

            self.snapshot["opportunities"] = ranked[:25]
'''

if old not in text:
    print("[WARN] Expected fair value block not found. Import/file created only.")
else:
    text = text.replace(old, new, 1)

engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-036 Confidence Engine installed")