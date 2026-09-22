from collections import defaultdict
from qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import (
    read_and_score_mature_prospective_cases,
)

rows=list(read_and_score_mature_prospective_cases())

print("[SCORED]",len(rows))
assert rows,"no prospective scored cases"

print("[ROW_FIELDS]",tuple(vars(rows[0]).keys()))

def bucket(p):
    lo=int(float(p)*10)/10
    if lo>=1.0:
        lo=.9
    return f"{lo:.1f}-{lo+.1:.1f}"

groups=defaultdict(list)

for r in rows:
    groups[(str(r.asset),bucket(float(r.forecast_probability)))].append(r)

for key,rs in sorted(groups.items()):
    n=len(rs)
    mean_brier=sum(float(x.brier_score) for x in rs)/n
    baseline=sum(float(x.baseline_brier) for x in rs)/n
    hit=sum(
        (float(x.forecast_probability)>=.5)==bool(x.outcome_positive)
        for x in rs
    )/n
    avg_p=sum(float(x.forecast_probability) for x in rs)/n
    actual=sum(bool(x.outcome_positive) for x in rs)/n

    print(
        "[BUCKET]",key,
        "n=",n,
        "avg_p=",round(avg_p,6),
        "actual=",round(actual,6),
        "brier=",round(mean_brier,8),
        "baseline=",round(baseline,8),
        "delta=",round(baseline-mean_brier,8),
        "directional_hit=",round(hit,6),
    )

for asset in sorted({str(x.asset) for x in rows}):
    rs=[x for x in rows if str(x.asset)==asset]
    mean_brier=sum(float(x.brier_score) for x in rs)/len(rs)
    baseline=sum(float(x.baseline_brier) for x in rs)/len(rs)

    print(
        "[ASSET_SCORE]",asset,
        "n=",len(rs),
        "brier=",round(mean_brier,8),
        "baseline=",round(baseline,8),
        "delta=",round(baseline-mean_brier,8),
    )

print("[PASS] OPA-008 predictive forecast anatomy complete")
