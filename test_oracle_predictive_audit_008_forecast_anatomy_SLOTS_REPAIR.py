from collections import defaultdict
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases

rows=list(read_and_score_mature_prospective_cases())
print("[SCORED]",len(rows))
assert rows,"no prospective scored cases"

r0=rows[0]
if is_dataclass(r0):
    names=tuple(f.name for f in fields(r0))
elif hasattr(r0,"_fields"):
    names=tuple(r0._fields)
elif hasattr(type(r0),"__slots__"):
    names=tuple(type(r0).__slots__)
else:
    names=tuple(x for x in dir(r0) if not x.startswith("_"))
print("[ROW_FIELDS]",names)

def bucket(p):
    lo=min(.9,int(float(p)*10)/10)
    return f"{lo:.1f}-{lo+.1:.1f}"

groups=defaultdict(list)
for r in rows:
    groups[(str(r.asset),bucket(r.forecast_probability))].append(r)

for key,rs in sorted(groups.items()):
    n=len(rs)
    mb=sum(float(x.brier_score) for x in rs)/n
    bb=sum(float(x.baseline_brier) for x in rs)/n
    avg=sum(float(x.forecast_probability) for x in rs)/n
    actual=sum(bool(x.outcome_positive) for x in rs)/n
    hit=sum((float(x.forecast_probability)>=.5)==bool(x.outcome_positive) for x in rs)/n
    print("[BUCKET]",key,"n=",n,"avg_p=",round(avg,6),
          "actual=",round(actual,6),"brier=",round(mb,8),
          "baseline=",round(bb,8),"delta=",round(bb-mb,8),
          "directional_hit=",round(hit,6))

for asset in sorted({str(x.asset) for x in rows}):
    rs=[x for x in rows if str(x.asset)==asset]
    mb=sum(float(x.brier_score) for x in rs)/len(rs)
    bb=sum(float(x.baseline_brier) for x in rs)/len(rs)
    hit=sum((float(x.forecast_probability)>=.5)==bool(x.outcome_positive) for x in rs)/len(rs)
    print("[ASSET_SCORE]",asset,"n=",len(rs),"brier=",round(mb,8),
          "baseline=",round(bb,8),"delta=",round(bb-mb,8),
          "directional_hit=",round(hit,6))

print("[PASS] OPA-008 forecast anatomy slots repair complete")
