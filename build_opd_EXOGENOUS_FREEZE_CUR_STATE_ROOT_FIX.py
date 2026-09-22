from pathlib import Path

P = Path(
    "qseries_v2/oracle_predictive_discovery/"
    "opd_live_full_evidence_fusion_predictor.py"
)

s = P.read_text(encoding="utf-8")

bad = '"exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state)'
good = '"exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(cur)'

n = s.count(bad)

if n != 1:
    raise SystemExit(f"[FAIL] expected exactly 1 bad insertion, found {n}")

s = s.replace(bad, good, 1)

compile(s, str(P), "exec")
P.write_text(s, encoding="utf-8")

print("[PASS] exogenous freeze now uses current scored state: cur")
print("[ROOT FILE]", P)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")