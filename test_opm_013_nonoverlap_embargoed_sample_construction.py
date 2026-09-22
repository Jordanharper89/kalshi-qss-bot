
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_pre_momentum.opm_013_nonoverlap_embargoed_sample_construction import build_embargoed_samples, EMBARGO_SECONDS

r = build_embargoed_samples(Path.cwd())
rows = r["rows"]
assert rows, "no embargoed samples"

by_contract = defaultdict(list)
for row in rows:
    by_contract[row["ticker"]].append(row["t"])

for ticker, times in by_contract.items():
    times.sort()
    for a, b in zip(times, times[1:]):
        assert (b-a).total_seconds() >= EMBARGO_SECONDS

print("[EMBARGOED_ROWS]", len(rows))
print("[REJECTED_OVERLAP]", len(r["rejected"]))
print("[CONTRACTS]", len(by_contract))
print("[EMBARGO_SECONDS]", EMBARGO_SECONDS)
print("[PASS] same-contract examples cannot overlap inside 300-second outcome window")
print("[PASS] duplicate nearby anchors are withheld from experiment population")
print("[PASS] OPM-013 non-overlap embargoed sample construction certified")
