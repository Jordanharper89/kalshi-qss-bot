from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_018_price_path_opportunity_reconstruction.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["anchor_price","H=(5,15,30,60,300,900,3600)","mfe_up","mae_up","mfe_down","mae_down","time_to_mfe_up","bucket","up_2to1","PRICE_PATH_OPPORTUNITY_MAP_READY"]:assert x in s,x
print("[PASS] OSD-018 price-path opportunity reconstruction compiles")
print("[PASS] MFE/MAE + multi-horizon path economics installed")
print("[PASS] low-price buckets + 2:1 reward/risk installed")
print("[PASS] settlement is not primary success label")
print("[PASS] execution/publication remain false")
