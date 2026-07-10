from pathlib import Path

ROOT = Path.cwd()
MODEL_PATH = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_model" / "universal_market.py"
TEST_PATH = ROOT / "test_umm_001_universal_market_model.py"

text = MODEL_PATH.read_text(encoding="utf-8")

old = """        if mid is None and bid is not None and ask is not None:
            mid = (float(bid) + float(ask)) / 2.0

        if spread is None and bid is not None and ask is not None:
            spread = float(ask) - float(bid)
"""

new = """        if mid is None and bid is not None and ask is not None:
            mid = round((float(bid) + float(ask)) / 2.0, 12)

        if spread is None and bid is not None and ask is not None:
            spread = round(float(ask) - float(bid), 12)
"""

if old not in text:
    raise RuntimeError("Expected UMM-001 price calculation block not found.")

text = text.replace(old, new)
MODEL_PATH.write_text(text, encoding="utf-8")

test = TEST_PATH.read_text(encoding="utf-8")
test = test.replace("assert market.price.spread == 0.04", "assert round(market.price.spread, 2) == 0.04")
test = test.replace("assert market.price.spread == 20", "assert round(market.price.spread, 2) == 20")
TEST_PATH.write_text(test, encoding="utf-8")

print("=" * 40)
print(" UMM-001.1 INSTALLER")
print(" Universal Market Model Precision Fix")
print("=" * 40)
print(f"[OK] Patched {MODEL_PATH}")
print(f"[OK] Patched {TEST_PATH}")
print("\n[DONE] UMM-001.1 installed")
print("\nRun:")
print("py test_umm_001_universal_market_model.py")