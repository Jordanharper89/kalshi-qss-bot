from pathlib import Path

ROOT = Path.cwd()
MODULE = ROOT / "qseries_v2" / "oracle_intelligence" / "universal_market_adapter_query_replay_validation_engine.py"

bad = 'for flag in ("executed": True, "order_submitted": True, "trade_routed": True, "position_opened": True):'
good = 'for flag in ("executed", "order_submitted", "trade_routed", "position_opened"):'

text = MODULE.read_text(encoding="utf-8")

if bad not in text:
    raise SystemExit("[FAIL] Bad syntax line not found. Module may already be patched or changed.")

text = text.replace(bad, good)

MODULE.write_text(text, encoding="utf-8")

print("========================================")
print(" OI-188 PATCH")
print(" Replay Validation Syntax Fix")
print("========================================")
print(f"[OK] Patched {MODULE}")
print()
print("[DONE] OI-188 syntax fix installed")
print()
print("Run:")
print("py test_oi_188_universal_market_adapter_query_replay_validation_engine.py")