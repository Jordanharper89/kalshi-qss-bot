
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_pre_momentum.opm_009_future_kalshi_price_path_labels import build_labeled_examples

def isolate_contracts(root=None):
    root = Path(root or Path.cwd())
    rows = build_labeled_examples(root)["rows"]

    by_contract = defaultdict(list)
    for row in rows:
        by_contract[row["ticker"]].append(row)

    isolated = []
    contract_meta = {}
    violations = []

    for ticker, stream in by_contract.items():
        stream.sort(key=lambda x: x["t"])
        contract_meta[ticker] = {
            "examples": len(stream),
            "first_t": stream[0]["t"].isoformat(),
            "last_t": stream[-1]["t"].isoformat(),
        }

        for row in stream:
            if row["ticker"] != ticker:
                violations.append((ticker, "CROSS_CONTRACT_ROW"))
                continue
            if row["kalshi_base_time"] > row["t"]:
                violations.append((ticker, "BASE_AFTER_T"))
                continue
            for key in ("t5","t15","t30","t60","t120","t300"):
                if row[key] <= row["t"]:
                    violations.append((ticker, key, "LABEL_NOT_FUTURE"))
                    break
            else:
                isolated.append(row)

    return {
        "rows": isolated,
        "contracts": contract_meta,
        "violations": violations,
    }
