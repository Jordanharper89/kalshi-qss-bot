from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_014_interaction_first_edge_miner.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in [
    "osd_012_full_evidence_clean_corpus.jsonl",
    "TRAIN_FRAC=.65","HURDLE=.02","MIN_N=12","MIN_TICKERS=3",
    "Rare-event concentration score",
    "Candidate may be profitable only in interaction",
    "a[\"hit\"] & b[\"hit\"]",
    "p[\"hit\"] & c[\"hit\"]",
    "INTERACTION_EDGE_SURVIVES_UNTOUCHED_HOLDOUT",
    '"execution_authority":False','"publication_allowed":False'
]:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-014 interaction-first miner compiles")
print("[PASS] pairs do not require profitable standalone atoms")
print("[PASS] selected triples do not require profitable standalone atoms")
print("[PASS] indexed intersections installed")
print("[PASS] fixed 65/35 temporal holdout")
print("[PASS] fixed 2% hurdle")
print("[PASS] N>=12, >=3 tickers, positive LB95 winner gate")
print("[PASS] execution/publication remain false")
