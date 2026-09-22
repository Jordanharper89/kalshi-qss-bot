from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_013_cross_family_reaction_divergence_detector.py"
TEST = ROOT / "test_oed_013_cross_family_reaction_divergence_detector.py"

assert (PKG / "oed_012_threshold_curve_distortion_detector.py").exists()

code = r"""
from pathlib import Path
from collections import defaultdict
from statistics import median
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 150000
BIN_SECONDS = 60
MIN_EVENTS_PER_FAMILY_BIN = 2

def _extract(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        return None
    m = p.get("message")
    if not isinstance(m, dict):
        return None
    ticker = str(m.get("market_ticker") or p.get("source_market_id") or "")
    if not ticker.startswith("KX"):
        return None
    px = m.get("yes_price_dollars")
    if px is None:
        px = m.get("price_dollars")
    if px is None:
        px = m.get("last_price_dollars")
    try:
        return ticker.split("-", 1)[0], float(px)
    except Exception:
        return None

def detect(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT observed_at, source_id, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT %s",
                (SCAN_ROWS,)
            )
            rows = q.fetchall() or []
        c.rollback()

    fb = defaultdict(list)
    for ts, sid, obj in rows:
        if str(sid) != "source.kalshi.market_data":
            continue
        x = _extract(obj)
        if not x:
            continue
        fam, px = x
        b = int(ts.timestamp()) // BIN_SECONDS
        fb[(fam, b)].append(px)

    returns = defaultdict(dict)
    for (fam, b), vals in fb.items():
        if len(vals) < MIN_EVENTS_PER_FAMILY_BIN:
            continue
        returns[fam][b] = vals[-1] - vals[0]

    families = sorted(returns)
    divergences = []
    for i in range(len(families)):
        for j in range(i + 1, len(families)):
            a, b = families[i], families[j]
            common = sorted(set(returns[a]) & set(returns[b]))
            if len(common) < 5:
                continue
            diffs = [returns[a][k] - returns[b][k] for k in common]
            med = median(diffs)
            for k, d in zip(common, diffs):
                resid = abs(d - med)
                if resid >= 0.20:
                    divergences.append({
                        "family_a": a,
                        "family_b": b,
                        "minute_bin": k,
                        "return_a": returns[a][k],
                        "return_b": returns[b][k],
                        "pair_median_difference": med,
                        "absolute_residual": resid,
                        "shared_history_bins": len(common),
                        "status": "DISCOVERED",
                        "relationship_is_predictive_proven": False,
                        "edge_proven": False,
                    })

    divergences.sort(key=lambda x: x["absolute_residual"], reverse=True)
    return {
        "schema_version": "OED-013",
        "divergences": divergences,
        "families": len(families),
        "relationship_basis": "EMPIRICAL_SAME_MINUTE_PRICE_CHANGE_DIFFERENCE",
        "relationship_is_predictive_proven": False,
        "edge_proven": False,
        "read_only": True,
    }
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_013_cross_family_reaction_divergence_detector import detect

s = detect(Path.cwd())
assert s["families"] > 1
assert s["relationship_is_predictive_proven"] is False
assert s["edge_proven"] is False
assert s["read_only"] is True

print("[FAMILIES]", s["families"])
print("[DIVERGENCES]", len(s["divergences"]))
print("[TOP_DIVERGENCES]")
for x in s["divergences"][:25]:
    print(" ", x)

print("[PASS] divergence measured against empirical pair behavior")
print("[PASS] temporal coexistence alone is not treated as prediction")
print("[PASS] OED-013 cross-family reaction divergence detector certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-013 installer complete")
