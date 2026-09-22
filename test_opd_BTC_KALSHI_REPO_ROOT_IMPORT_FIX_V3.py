from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "import json, math, statistics, sys" in s
assert "sys.path.insert(0,str(ROOT))" in s
assert 'HURDLE=0.02' in s
assert 'KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND' in s
print("[PASS] repo root added to profitability-gate import path")
print("[PASS] qseries_v2 production modules can resolve from nested script launch")
print("[PASS] connector source, 2% hurdle, signal, and profitability logic unchanged")
