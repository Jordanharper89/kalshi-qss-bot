from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
MODULE = PKG / "opm_013_nonoverlap_embargoed_sample_construction.py"
TEST = ROOT / "test_opm_013_nonoverlap_embargoed_sample_construction.py"

module = r"""
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_pre_momentum.opm_012_contract_boundary_isolation import isolate_contracts

LABEL_HORIZON_SECONDS = 300
EMBARGO_SECONDS = 300

def build_embargoed_samples(root=None):
    root = Path(root or Path.cwd())
    rows = isolate_contracts(root)["rows"]

    by_contract = defaultdict(list)
    for row in rows:
        by_contract[row["ticker"]].append(row)

    admitted = []
    rejected = []

    for ticker, stream in by_contract.items():
        stream.sort(key=lambda x: x["t"])
        last_admitted_t = None

        for row in stream:
            t = row["t"]
            if last_admitted_t is None:
                admitted.append(row)
                last_admitted_t = t
                continue

            gap = (t - last_admitted_t).total_seconds()
            if gap < EMBARGO_SECONDS:
                rejected.append((ticker, row["anchor_epoch"], gap, "EMBARGO_OVERLAP"))
                continue

            admitted.append(row)
            last_admitted_t = t

    admitted.sort(key=lambda x: x["t"])
    return {
        "rows": admitted,
        "rejected": rejected,
        "embargo_seconds": EMBARGO_SECONDS,
        "label_horizon_seconds": LABEL_HORIZON_SECONDS,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPM-013 installer complete")
