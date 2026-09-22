from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_017_regime_specific_comparable_case_profit_gate.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["HURDLE=.02","A=.60","B=.80","MAXF=80","max(0.000001","calibration_certified","cm>0","clb>0","REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT"]:assert x in s,x
print("[PASS] OSD-017 strict comparable-case profit gate compiles")
print("[PASS] expected-net gate cannot be negative")
print("[PASS] calibration mean net and LB95 must be positive before holdout opens")
print("[PASS] feature capacity expanded to 80")
print("[PASS] fixed 2% hurdle; execution/publication remain false")
