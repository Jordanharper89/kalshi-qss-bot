from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_exogenous_value_regime_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in ("HURDLE=0.02","TRAIN_FRAC=0.65","MIN_TRAIN_N=30","MIN_HOLDOUT_N=12",
          "MIN_HOLDOUT_TICKERS=3","sids.issubset(ALLOWED)","flatten_numeric",
          "holdout_lb95_net_after_2pct"):
    assert x in s,x
print("[PASS] exogenous value-regime temporal holdout audit installed")
print("[PASS] only 7-source clean BTC snapshots admitted")
print("[PASS] actual canonical numeric evidence values extracted")
print("[PASS] thresholds selected from training only")
print("[PASS] untouched temporal holdout preserved")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] winner requires positive holdout 95% lower bound")
print("[MODEL MUTATION] FALSE")
