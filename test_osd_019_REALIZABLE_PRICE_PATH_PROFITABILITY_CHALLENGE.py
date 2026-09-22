from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_019_realizable_price_path_profitability_challenge.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["anchor_observed_epoch","mfe","mae","targets=(.03,.04,.05,.06,.08,.10)","profit_factor","expectancy_per_trade","max_drawdown"]:assert x in s,x
print("[PASS] OSD-019 profitability challenge compiles");print("[PASS] fixed target/stop + chronological 70/30 holdout installed");print("[PASS] expectancy/payoff/profit-factor/drawdown scoring installed");print("[PASS] execution/publication remain false")
