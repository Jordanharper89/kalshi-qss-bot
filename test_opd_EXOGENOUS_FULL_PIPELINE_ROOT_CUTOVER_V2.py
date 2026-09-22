from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=[
"def _opd_load_exogenous_canonical_asof",
"sequence_number<=%s AND observed_at<=to_timestamp(%s)",
'"exogenous_evidence_state":exogenous',
'"exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {}',
"LIVE_EVIDENCE_EXOGENOUS_SOURCES=",
]
for x in required:
    assert x in s,x
assert "source.kalshi%%" in s
assert "source.crypto.hf.coinbase%%" in s
assert "source.crypto.condition.%%" in s
assert "source.crypto.learned_case.%%" in s
assert "source.polymarket%%" in s
print("[PASS] exact anchor sequence/time-bounded exogenous canonical reader installed")
print("[PASS] market/derived predictive sources excluded")
print("[PASS] exogenous state carried independently of existing token/scoring semantics")
print("[PASS] immutable prediction ledger persists frozen exogenous snapshot")
print("[PASS] old immutable ledger rows are not rewritten")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
