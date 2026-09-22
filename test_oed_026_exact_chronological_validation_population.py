
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_026_exact_chronological_validation_population import build
s,p=build(Path.cwd())
assert p.exists() and s["condition_count"]>0 and s["random_split_used"] is False
for c in s["conditions"]:
    if c["test_rows"]:
        assert max(x["anchor_epoch"] for x in c["train_rows"])+s["embargo_seconds"] < min(x["anchor_epoch"] for x in c["test_rows"])
        assert set(c["train_days"]).isdisjoint(set(c["test_days"]))
print("[FILE]",p)
print("[CONDITIONS]",s["condition_count"])
print("[READY]",s["ready_count"])
print("[MISSING_ANCHOR_ROWS]",s["missing_anchor_rows"])
print("[POPULATION_HASH]",s["population_hash"])
for c in s["conditions"][:25]:
    print(" ",{k:c[k] for k in ("condition_key","total_rows","train_n","test_n","train_days","test_days","status")})
print("[PASS] chronological train-before-test enforced")
print("[PASS] 900-second embargo enforced")
print("[PASS] unseen UTC-day isolation enforced")
print("[PASS] OED-026 exact chronological validation population certified")
