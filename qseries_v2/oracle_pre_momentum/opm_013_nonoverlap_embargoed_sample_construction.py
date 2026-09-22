
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
