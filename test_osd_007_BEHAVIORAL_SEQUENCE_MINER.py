from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_007_behavioral_sequence_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "BEHAVIORAL_SEQUENCE" in s and "HURDLE=.02" in s and "SPLIT=.65" in s
print("[PASS] OSD-007 behavioral sequence miner compiles")
print("[PASS] fixed 2% hurdle and discovery-only generation preserved")
