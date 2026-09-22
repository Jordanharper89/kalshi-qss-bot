from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
MODULE = PKG / "opm_014_btc_condition_kalshi_response_descriptive_statistics.py"
TEST = ROOT / "test_opm_014_btc_condition_kalshi_response_descriptive_statistics.py"

module = r"""
from pathlib import Path
from collections import Counter
from statistics import mean, median
from qseries_v2.oracle_pre_momentum.opm_013_nonoverlap_embargoed_sample_construction import build_embargoed_samples

RETURN_FEATURES = ("btc_return_5s","btc_return_15s","btc_return_30s","btc_return_60s")
PATH_FIELDS = ("d5","d15","d30","d60","d120","d300")

def _sign(v, eps=0.0):
    if v > eps:
        return "UP"
    if v < -eps:
        return "DOWN"
    return "FLAT"

def describe(root=None):
    root = Path(root or Path.cwd())
    rows = build_embargoed_samples(root)["rows"]
    if not rows:
        raise RuntimeError("NO_EMBARGOED_ROWS")

    stats = {
        "schema_version": "OPM-014",
        "rows": len(rows),
        "contracts": len(set(r["ticker"] for r in rows)),
        "features": {},
        "responses": {},
        "first_hit_5c": dict(Counter(r["first_hit_5c"] for r in rows)),
        "predictive_edge_proven": False,
    }

    for f in RETURN_FEATURES:
        vals = [float(r[f]) for r in rows]
        stats["features"][f] = {
            "mean": mean(vals),
            "median": median(vals),
            "min": min(vals),
            "max": max(vals),
            "sign_counts": dict(Counter(_sign(v) for v in vals)),
        }

    for p in PATH_FIELDS:
        vals = [float(r[p]) for r in rows]
        stats["responses"][p] = {
            "mean": mean(vals),
            "median": median(vals),
            "min": min(vals),
            "max": max(vals),
            "sign_counts": dict(Counter(_sign(v) for v in vals)),
        }

    stats["mfe_300"] = {
        "mean": mean(float(r["mfe_300"]) for r in rows),
        "median": median(float(r["mfe_300"]) for r in rows),
    }
    stats["mae_300"] = {
        "mean": mean(float(r["mae_300"]) for r in rows),
        "median": median(float(r["mae_300"]) for r in rows),
    }
    return stats
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from pprint import pprint
from qseries_v2.oracle_pre_momentum.opm_014_btc_condition_kalshi_response_descriptive_statistics import describe

s = describe(Path.cwd())
assert s["rows"] > 0
assert s["contracts"] > 0
assert s["predictive_edge_proven"] is False
assert set(s["features"]) == {"btc_return_5s","btc_return_15s","btc_return_30s","btc_return_60s"}
assert set(s["responses"]) == {"d5","d15","d30","d60","d120","d300"}
print("[DESCRIPTIVE_STATISTICS]")
pprint(s)
print("[PASS] BTC condition distributions measured")
print("[PASS] Kalshi future response distributions measured")
print("[PASS] statistics remain descriptive only; no edge claim permitted")
print("[PASS] OPM-014 BTC condition x Kalshi response descriptive statistics certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPM-014 installer complete")
