"""
build_oi_005_explanation_engine.py
OI-005 Explanation Engine Installer
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
OI-005 Explanation Engine

Turns Oracle recommendations into clear, auditable explanations.
Every recommendation must be explainable.
"""

class ExplanationEngine:

    def explain(self, recommendation, evidence=None):
        evidence = evidence or []

        lines = []
        lines.append(f"Ticker: {recommendation.get('ticker')}")
        lines.append(f"Action: {recommendation.get('action')}")
        lines.append(f"Confidence: {recommendation.get('confidence')}%")
        lines.append(f"Market YES Price: {recommendation.get('market_yes_price')}")
        lines.append(f"Oracle Fair YES Price: {recommendation.get('fair_yes_price')}")
        lines.append(f"Edge: {recommendation.get('edge')}")
        lines.append(f"Reason: {recommendation.get('reason')}")
        lines.append("Oracle Execution: Disabled — Q Series handles execution.")

        if evidence:
            lines.append("")
            lines.append("Evidence:")
            for item in evidence:
                source = getattr(item, "source", "unknown")
                category = getattr(item, "category", "unknown")
                value = getattr(item, "value", {})
                lines.append(f"- {category} evidence from {source}: {value}")

        return "\\n".join(lines)


explanation_engine = ExplanationEngine()
'''

test_code = '''from qseries_v2.oi.explanation_engine import explanation_engine

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
'''

print("=" * 40)
print(" OI-005 INSTALLER")
print(" Explanation Engine")
print("=" * 40)

write(OI / "explanation_engine.py", engine_code)
write(ROOT / "test_oi_005_explanation_engine.py", test_code)

print("\n[DONE] OI-005 installed")
print("\nRun:")
print("python test_oi_005_explanation_engine.py")