
from pathlib import Path
import json
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_013_nonoverlap_embargoed_sample_construction import build_embargoed_samples

MIN_EXAMPLES = 100
MIN_CONTRACTS = 10
MIN_EXAMPLES_PER_SIDE = 20

def evaluate(root=None):
    root = Path(root or Path.cwd())
    rows = build_embargoed_samples(root)["rows"]

    contracts = Counter(r["ticker"] for r in rows)
    up = sum(1 for r in rows if r["btc_return_15s"] > 0)
    down = sum(1 for r in rows if r["btc_return_15s"] < 0)
    flat = len(rows) - up - down

    reasons = []
    if len(rows) < MIN_EXAMPLES:
        reasons.append("INSUFFICIENT_TOTAL_EXAMPLES")
    if len(contracts) < MIN_CONTRACTS:
        reasons.append("INSUFFICIENT_DISTINCT_CONTRACTS")
    if up < MIN_EXAMPLES_PER_SIDE:
        reasons.append("INSUFFICIENT_POSITIVE_BTC_CONDITIONS")
    if down < MIN_EXAMPLES_PER_SIDE:
        reasons.append("INSUFFICIENT_NEGATIVE_BTC_CONDITIONS")

    ready = not reasons

    state = {
        "schema_version": "OPM-015",
        "embargoed_examples": len(rows),
        "distinct_contracts": len(contracts),
        "btc15s_up_examples": up,
        "btc15s_down_examples": down,
        "btc15s_flat_examples": flat,
        "minimum_examples": MIN_EXAMPLES,
        "minimum_contracts": MIN_CONTRACTS,
        "minimum_examples_per_side": MIN_EXAMPLES_PER_SIDE,
        "predictive_experiment_ready": ready,
        "reasons": reasons,
        "predictive_edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    out = root / "runtime" / "pre_momentum"
    out.mkdir(parents=True, exist_ok=True)
    (out / "opm_015_sample_sufficiency.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    return state
