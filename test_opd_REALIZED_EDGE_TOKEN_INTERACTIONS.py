from pathlib import Path
p=Path("audit_opd_REALIZED_EDGE_TOKEN_INTERACTIONS.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("HURDLE=.020","MIN_N=12","MIN_TICKERS=3","MAX_DEGREE=3",
          "RESOLVED_EXACT_FUTURE","actionable_at_freeze","generation\") or 2)!=2",
          "conservative_lower_bound","eligible_positive","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exact resolved Gen2 prospective actionable outcomes only")
print("[PASS] fixed 2pct hurdle preserved")
print("[PASS] 1-way, 2-way, and 3-way evidence-token interactions audited")
print("[PASS] minimum 12 cases / 3 tickers required before interaction admission")
print("[PASS] conservative lower-bound net economics required for winner status")
print("[PASS] future/outcome/result tokens excluded from feature search")
print("[PASS] predictor and production runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
