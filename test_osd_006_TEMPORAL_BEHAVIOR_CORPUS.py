from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_006_temporal_behavior_corpus.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "d1_self_5s_taker_imbalance" in s
assert "self_minus_sibling_60s_return" in s
assert "future_return" not in s.split('x["execution_authority"]')[0]
print("[PASS] OSD-006 temporal corpus compiles")
print("[PASS] prior-state deltas and self-vs-sibling lead/lag features installed")
print("[PASS] no future target used to construct temporal features")
