from pathlib import Path

ROOT = Path.cwd()
MODULE = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_query_replay_certification_engine.py"

text = MODULE.read_text(encoding="utf-8")

old = "    self._records.append(record)\n    return record\n"
new = """    if not hasattr(self, "_records"):
        self._records = []
    self._records.append(record)
    return record
"""

if old not in text:
    raise SystemExit("[FAIL] Could not find _records append line to patch.")

text = text.replace(old, new)

MODULE.write_text(text, encoding="utf-8")

print("========================================")
print(" OI-189 PATCH")
print(" Certification Records Fix")
print("========================================")
print(f"[OK] Patched {MODULE}")
print()
print("[DONE] OI-189 records fix installed")
print()
print("Run:")
print("py test_oi_189_universal_market_adapter_query_replay_certification_engine.py")
print("py run_oracle_gate2_1_full_replay_registry_test.py")