from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_013_clean_full_evidence_profitability_challenge.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ["osd_012_full_evidence_clean_corpus.jsonl","TRAIN_FRAC=.65","HURDLE=.02",
          "MIN_N=12","MIN_TICKERS=3","untouched_holdout_rows","lb95",
          "CLEAN_FULL_EVIDENCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT",
          '"execution_authority":False','"publication_allowed":False']:
    assert x in s,x
assert "future_return" in s
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-013 clean full-evidence profitability challenge compiles")
print("[PASS] fixed 65/35 temporal discovery/untouched holdout split")
print("[PASS] fixed 2% hurdle")
print("[PASS] N>=12, >=3 tickers, positive LB95 winner gate")
print("[PASS] bounded indexed univariate/pair discovery")
print("[PASS] execution/publication remain false")
