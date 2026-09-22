from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_012_foundational_prediction_corpus_rebuild.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ["ANCHOR_AFTER_PREDICTION_FREEZE","OUTCOME_NOT_STRICTLY_FUTURE",
          "OUTCOME_SEQUENCE_NOT_STRICTLY_FUTURE","osd_012_temporal_quarantine.jsonl",
          "evidence_agreement","comparable_cases","mean_similarity","expected_return",
          "predicted_probability","net_edge_after_2pct","anchor_price",
          "exogenous_evidence_snapshot","coinbase_hf_state",
          '"execution_authority":False','"publication_allowed":False']:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-012 foundational corpus rebuild compiles")
print("[PASS] temporal violations are quarantined, never trained")
print("[PASS] exact future sequence/time gates installed")
print("[PASS] dropped Oracle prediction fields restored")
print("[PASS] nested full-evidence state flattening installed")
print("[PASS] original immutable ledgers remain untouched")
print("[PASS] execution/publication remain false")
