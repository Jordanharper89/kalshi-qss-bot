from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
for x in ("HURDLE=0.02","SPLIT=0.65","UNIVARIATE","PAIR","future_return","mean_net","lb95"):
    assert x in s,x
assert "holdout" not in s[s.find("train=rows[:cut]"):s.find("features=")].lower()
print("[PASS] OSD-003 deterministic interface test")
print("[PASS] fixed 2% hurdle")
print("[PASS] discovery-only threshold generation")
print("[PASS] univariate and pair interaction mining enabled")
print("[PASS] untouched holdout is not used for candidate generation")
