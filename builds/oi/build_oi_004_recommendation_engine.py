"""
build_oi_004_recommendation_engine.py
OI-004 Recommendation Engine Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OI = ROOT / "qseries_v2" / "oi"


def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")


engine_code = '''"""
OI-004 Recommendation Engine

Oracle researches, scores, explains, and learns.
Oracle does NOT execute trades.
"""

class RecommendationEngine:

    def recommend(self, ticker, market_yes_price, fair_yes_price, confidence):
        edge = round(float(fair_yes_price) - float(market_yes_price), 2)
        confidence = float(confidence)

        if confidence < 55:
            action = "PASS"
            reason = "Confidence below minimum threshold."
        elif edge >= 7:
            action = "BUY_YES"
            reason = "Fair value is meaningfully above market price."
        elif edge <= -7:
            action = "BUY_NO"
            reason = "Market YES price is meaningfully above fair value."
        else:
            action = "PASS"
            reason = "No strong edge after confidence and price comparison."

        return {
            "ticker": ticker,
            "action": action,
            "market_yes_price": round(float(market_yes_price), 2),
            "fair_yes_price": round(float(fair_yes_price), 2),
            "edge": edge,
            "confidence": round(confidence, 2),
            "reason": reason,
            "oracle_executes": False,
        }


recommendation_engine = RecommendationEngine()
'''

test_code = '''from qseries_v2.oi.recommendation_engine import recommendation_engine

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
'''

print("=" * 40)
print(" OI-004 INSTALLER")
print(" Recommendation Engine")
print("=" * 40)

write(OI / "recommendation_engine.py", engine_code)
write(ROOT / "test_oi_004_recommendation_engine.py", test_code)

print("\n[DONE] OI-004 installed")
print("\nRun:")
print("python test_oi_004_recommendation_engine.py")