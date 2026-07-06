from pathlib import Path

ROOT = Path.cwd()
MODULE = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_query_replay_certification_engine.py"

text = MODULE.read_text(encoding="utf-8")

replacements = {
    'validation_hash = str(data.get("validation_hash") or "")':
        'validation_hash = str(data.get("validation_hash") or data.get("replay_validation_hash") or "")',

    'manifest_hash = str(data.get("manifest_hash") or "")':
        'manifest_hash = str(data.get("manifest_hash") or data.get("target_manifest_hash") or "")',

    'chain_hash = str(data.get("chain_hash") or "")':
        'chain_hash = str(data.get("chain_hash") or data.get("target_chain_hash") or "")',

    'manifest_id = str(data.get("manifest_id") or "")':
        'manifest_id = str(data.get("manifest_id") or data.get("target_manifest_id") or "")',

    'entry_count = int(data.get("entry_count") or 0)':
        'entry_count = int(data.get("entry_count") or data.get("telemetry", {}).get("entry_count") or 0)',
}

changed = 0
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
        changed += 1

if changed == 0:
    raise SystemExit("[FAIL] No contract-alignment replacements were applied. OI-189 shape may differ.")

MODULE.write_text(text, encoding="utf-8")

print("========================================")
print(" OI-189 PATCH")
print(" Replay Certification Contract Alignment")
print("========================================")
print(f"[OK] Patched {MODULE}")
print(f"[OK] Replacements applied: {changed}")
print()
print("[DONE] OI-189 contract alignment installed")
print()
print("Run:")
print("py test_oi_189_universal_market_adapter_query_replay_certification_engine.py")
print("py run_oracle_gate2_1_full_replay_registry_test.py")