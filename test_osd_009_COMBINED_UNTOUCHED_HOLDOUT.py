from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_009_combined_untouched_holdout.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert 's["lb95"]>0' in s and "HURDLE=.02" in s and "MIN_N=12" in s and "MIN_T=3" in s
print("[PASS] OSD-009 combined untouched holdout compiles")
print("[PASS] fixed 2% hurdle and conservative LB95 gate preserved")
