from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact

root=Path.cwd();rt=root/"runtime"/"predictive_data"

def rows(p):
 return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []

states=rows(rt/"opd_032_prospective_state_ledger.jsonl")
done={x["state_id"] for x in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}

candidates=[
 x for x in states
 if int(x.get("horizon_seconds",-1))==5
 and x["state_id"] not in done
 and time.time()>=float(x["observed_epoch"])+5
][-12:]

assert candidates,"NO_MATURE_UNRESOLVED_5S_STATES"

winner=None
for s in reversed(candidates):
 out=materialize_live(s,root)
 print("[TRY]",s["state_id"][:12],s["ticker"],"[RESULT]",out is not None)
 if out is not None:
  winner=(s,out)
  break

assert winner,"NO_PHYSICAL_5S_PATH_FOUND_ACROSS_12_MATURE_STATES"

s,out=winner
resolve_exact(out,root)

resolved={x["state_id"]:x for x in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
r=resolved[s["state_id"]]

assert r["strictly_future"] is True
assert float(r["resolution_epoch"])>=float(s["observed_epoch"])+5
assert int(out["coverage_start_sequence"])>0

print("[STATE_ID]",s["state_id"])
print("[TICKER]",s["ticker"])
print("[COVERAGE_START_SEQUENCE]",out["coverage_start_sequence"])
print("[COVERAGE_HIGHWATER_SEQUENCE]",out["coverage_highwater_sequence"])
print("[RESOLUTION_EPOCH]",r["resolution_epoch"])
print("[STRICTLY_FUTURE]",r["strictly_future"])
print("[PASS] OPD-066 V6 state-time highwater outcome repair physically certified")
