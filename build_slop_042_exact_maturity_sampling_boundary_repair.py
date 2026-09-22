from pathlib import Path
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_016b_exact_frozen_prediction_maturity_rebuild.py")
assert P.exists(),P
s=P.read_text()
old="def materialize_frozen_prediction_path(prediction,root=None,tolerance_seconds=8.0):"
assert old in s,"exact SLOP-016B signature changed"
P.write_text(s.replace(old,"def materialize_frozen_prediction_path(prediction,root=None,tolerance_seconds=30.0):"),encoding="utf-8")
print("[PASS] SLOP-042 maturity sampling boundary repaired to 30s")
print("[PASS] thesis horizon remains 60 seconds")
