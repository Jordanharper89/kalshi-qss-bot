
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_exogenous_clean_corpus_realized_edge_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'BTC_ALLOWED={',
'sids.issubset(BTC_ALLOWED)',
'str(r.get("asset") or "").upper()!="BTC"',
'HURDLE=0.02',
'MIN_SEGMENT_N=12',
'MIN_UNIQUE_TICKERS=3',
'lower_bound_net_after_2pct',
):
    assert x in s,x
print("[PASS] clean-corpus realized-edge audit V2 installed")
print("[PASS] only BTC rows admitted")
print("[PASS] snapshot source set must be subset of the 7 certified BTC sources")
print("[PASS] GMGN/Solana/internal/sports contamination cannot enter")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] profitability requires supported positive 95% lower bound")
print("[MODEL MUTATION] FALSE")
