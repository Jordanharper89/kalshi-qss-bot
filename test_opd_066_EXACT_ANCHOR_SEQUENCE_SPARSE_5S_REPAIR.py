from pathlib import Path
import json,time
from unittest.mock import patch
import qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome as m51
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m56
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact

s={"state_id":"DET","anchor_id":"obs-anchor","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
w={"ticker":"KXTEST","event_epoch":106.0,"price":.50,"sequence_number":12}
z=m51.materialize_from_path_and_witness(s,[],w)
assert z["future_return"]==0.0 and z["mfe"]==0.0 and z["mae"]==0.0
assert z["future_end_price"]==.50 and z["outcome_basis"].startswith("CARRY_FORWARD")
p=[{"ticker":"KXTEST","event_epoch":101.0,"price":.52,"sequence_number":10},{"ticker":"KXTEST","event_epoch":104.0,"price":.57,"sequence_number":11}]
x=m51.materialize_from_path_and_witness(s,p,w)
assert round(x["future_return"],8)==.07 and x["outcome_basis"]=="OBSERVED_SAME_TICKER_PATH"
with patch.object(m56,"exact_anchor_sequence",lambda *a,**k:9),patch.object(m56,"read_until_witness",lambda *a,**k:([],w,12)):
 y=m56.materialize_live(s,".")
 assert y["coverage_start_sequence"]==9 and y["anchor_sequence_exact"] is True and y["future_return"]==0.0
print("[DETERMINISTIC] observed-path preserved; sparse carry-forward certified")

root=Path.cwd();rt=root/"runtime"/"predictive_data"
def rows(p):return [json.loads(v) for v in p.read_text(encoding="utf-8").splitlines() if v.strip()] if p.exists() else []
done={v["state_id"] for v in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
states=[v for v in rows(rt/"opd_032_prospective_state_ledger.jsonl")
 if int(v.get("horizon_seconds",-1))==5 and v["state_id"] not in done and time.time()>=float(v["observed_epoch"])+5]
assert states,"NO_MATURE_UNRESOLVED_LIVE_5S_STATES"
winner=None
for st in reversed(states[-24:]):
 seq=m56.exact_anchor_sequence(st,root)
 if seq is None:
  print("[SKIP_NO_ANCHOR_SEQUENCE]",st["state_id"][:12],st["ticker"]);continue
 out=m56.materialize_live(st,root)
 print("[TRY]",st["state_id"][:12],st["ticker"],"[ANCHOR_SEQ]",seq,"[RESULT]",out is not None)
 if out is not None:
  winner=(st,out);break
assert winner,"NO_WITNESSED_LIVE_5S_STATE_FOUND_IN_24_RECENT_STATES"
st,out=winner
resolve_exact(out,root)
r={v["state_id"]:v for v in rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}[st["state_id"]]
assert r["strictly_future"] is True
assert float(r["resolution_epoch"])>=float(st["observed_epoch"])+5
print("[STATE_ID]",st["state_id"])
print("[TICKER]",st["ticker"])
print("[OUTCOME_BASIS]",out["outcome_basis"])
print("[ANCHOR_SEQUENCE]",out["coverage_start_sequence"])
print("[HIGHWATER_SEQUENCE]",out["coverage_highwater_sequence"])
print("[FUTURE_RETURN]",out["future_return"],"[MFE]",out["mfe"],"[MAE]",out["mae"])
print("[STRICTLY_FUTURE]",r["strictly_future"])
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] exact-anchor-sequence sparse 5-second prospective outcome physically certified")
