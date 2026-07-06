"""
build_oi_002_confidence_engine.py
OI-002 Confidence Engine Installer
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


confidence_engine = '''"""
OI-002 Confidence Engine
"""

class ConfidenceEngine:

    def __init__(self):
        self.weights = {
            "market": 1.00,
            "news": 0.90,
            "historical": 0.85,
            "social": 0.60,
        }

    def score(self, evidence_list):
        if not evidence_list:
            return 0.0

        total = 0.0

        for evidence in evidence_list:
            weight = self.weights.get(evidence.category.lower(), 0.50)
            total += weight

        confidence = (total / len(evidence_list)) * 100
        return round(min(confidence, 100.0), 2)


confidence_engine = ConfidenceEngine()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.confidence_engine import confidence_engine

evidence = [
    Evidence(source="Market", category="market", value={}),
    Evidence(source="History", category="historical", value={}),
    Evidence(source="News", category="news", value={})
]

score = confidence_engine.score(evidence)

assert score > 0

print(f"[PASS] OI-002 Confidence Engine ({score}%)")
'''

print("=" * 40)
print(" OI-002 INSTALLER")
print(" Confidence Engine")
print("=" * 40)

write(OI / "confidence_engine.py", confidence_engine)
write(ROOT / "test_oi_002_confidence_engine.py", test_code)

print("\n[DONE] OI-002 installed")
print("\nRun:")
print("python test_oi_002_confidence_engine.py")