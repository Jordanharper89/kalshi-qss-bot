from pathlib import Path

ROOT = Path.cwd()
MODULE_PATH = ROOT / "qseries_v2" / "oracle_intelligence" / "opportunity_operating_system" / "opportunity_ranking_engine.py"
TEST_PATH = ROOT / "test_oos_002_opportunity_ranking_engine.py"

text = MODULE_PATH.read_text(encoding="utf-8")

old = '''    RankingProfile.MAX_EXPECTED_VALUE: {
        "confidence": 0.18,
        "edge": 0.40,
        "liquidity": 0.10,
        "freshness": 0.08,
        "urgency": 0.08,
        "risk": -0.08,
        "execution": -0.06,
        "capital": -0.02,
    },'''

new = '''    RankingProfile.MAX_EXPECTED_VALUE: {
        "confidence": 0.10,
        "edge": 0.68,
        "liquidity": 0.05,
        "freshness": 0.04,
        "urgency": 0.04,
        "risk": -0.04,
        "execution": -0.03,
        "capital": -0.02,
    },'''

if old not in text:
    raise RuntimeError("Expected MAX_EXPECTED_VALUE weights block not found.")

text = text.replace(old, new)
MODULE_PATH.write_text(text, encoding="utf-8")

print("=" * 40)
print(" OOS-002.1 INSTALLER")
print(" Opportunity Ranking Profile Fix")
print("=" * 40)
print(f"[OK] Patched {MODULE_PATH}")
print("\n[DONE] OOS-002.1 installed")
print("\nRun:")
print("py test_oos_002_opportunity_ranking_engine.py")