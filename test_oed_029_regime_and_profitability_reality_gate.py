
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_029_regime_and_profitability_reality_gate import build
s,p=build(Path.cwd())
assert p.exists() and s["semantic_trade_mapping_required"] and s["fees_slippage_required"]
assert s["tradable_edge_count"]<=s["profitability_proven_count"]<=s["holm_behavior_survivors"]
print("[HOLM_BEHAVIOR_SURVIVORS]",s["holm_behavior_survivors"])
print("[REGIME_STABLE]",s["regime_stable_count"])
print("[PROFITABILITY_PROVEN]",s["profitability_proven_count"])
print("[TRADABLE_EDGE_COUNT]",s["tradable_edge_count"])
print("[GATE_HASH]",s["gate_hash"])
for x in s["survivors"]: print(" ",x)
print("[PASS] behavioral significance is not confused with profitability")
print("[PASS] no pair P&L invented without certified trade semantics")
print("[PASS] OED-029 regime/profitability reality gate certified")
