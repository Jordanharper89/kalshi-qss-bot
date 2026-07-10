from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
OOS = BASE / "oracle_intelligence" / "opportunity_operating_system"

MODULE_PATH = OOS / "opportunity_validation_engine.py"

text = MODULE_PATH.read_text(encoding="utf-8")

text = text.replace(
    "from dataclasses import dataclass, field, asdict",
    "from dataclasses import dataclass, field as dc_field, asdict",
)

text = text.replace("field(default_factory=", "dc_field(default_factory=")

MODULE_PATH.write_text(text, encoding="utf-8")

print("=" * 40)
print(" OOS-004.1 INSTALLER")
print(" Opportunity Validation Engine Field Fix")
print("=" * 40)
print(f"[OK] Patched {MODULE_PATH}")
print("\n[DONE] OOS-004.1 installed")
print("\nRun:")
print("py test_oos_004_opportunity_validation_engine.py")