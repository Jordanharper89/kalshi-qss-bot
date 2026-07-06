"""
build_oi_003_probability_engine.py
OI-003 Probability Engine Installer
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
OI-003 Probability Engine
"""

class ProbabilityEngine:

    def probability(self, confidence):
        confidence = max(0.0, min(100.0, float(confidence)))
        return round(confidence / 100.0, 4)

    def fair_yes_price(self, confidence):
        return round(self.probability(confidence) * 100, 2)

    def fair_no_price(self, confidence):
        return round(100 - self.fair_yes_price(confidence), 2)

    def expected_edge(self, market_price, fair_price):
        return round(fair_price - market_price, 2)


probability_engine = ProbabilityEngine()
'''

test_code = '''from qseries_v2.oi.probability_engine import probability_engine

confidence = 91.67

prob = probability_engine.probability(confidence)
yes = probability_engine.fair_yes_price(confidence)
no = probability_engine.fair_no_price(confidence)
edge = probability_engine.expected_edge(85, yes)

assert round(prob,2) == 0.92
assert yes > no
assert edge > 0

print("[PASS] OI-003 Probability Engine")
print(f"Probability : {prob:.4f}")
print(f"Fair YES    : {yes}")
print(f"Fair NO     : {no}")
print(f"Edge        : {edge}")
'''

print("=" * 40)
print(" OI-003 INSTALLER")
print(" Probability Engine")
print("=" * 40)

write(OI / "probability_engine.py", engine_code)
write(ROOT / "test_oi_003_probability_engine.py", test_code)

print("\n[DONE] OI-003 installed")
print("\nRun:")
print("python test_oi_003_probability_engine.py")