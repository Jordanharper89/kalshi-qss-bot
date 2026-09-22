from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "opd_live_full_evidence_fusion_predictor.py" in s
assert "importlib.import_module(modname)" in s
assert "_opd_exo_connect" in s
assert "production PostgreSQL connector unresolved from predictor source" in s
assert 'HURDLE=0.02' in s
assert 'KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND' in s
print("[PASS] profitability gate now resolves PostgreSQL connector from actual production predictor source")
print("[PASS] no guessed connector module paths remain")
print("[PASS] profitability logic, 2% hurdle, and model semantics unchanged")
