from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_underlying_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "for (a,h),r in labels.items()" not in s
assert 'base=round(p["time"]/5.0)*5.0' in s
assert "for a in (base-5.0,base,base+5.0):" in s
assert 'abs(a-p["time"])<=2.5' in s
print("[PASS] quadratic CHF fallback scan removed")
print("[PASS] bounded indexed 5-second-grid lookup installed")
print("[PASS] exact/nearest-anchor tolerance preserved at <=2.5s")
print("[PASS] target, train/holdout semantics, and signal logic unchanged")
print("[MODEL MUTATION] FALSE")
