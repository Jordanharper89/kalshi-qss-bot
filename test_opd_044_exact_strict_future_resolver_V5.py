import tempfile,json
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
r=Path(tempfile.mkdtemp());rt=r/"runtime/predictive_data";rt.mkdir(parents=True)
state={"state_id":"S044","anchor_id":"A044","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.54,"matched_family_ids":["F"],"post_freeze":True}
(rt/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(state)+"\n")
base={"state_id":"S044","future_return":.01,"mfe":.02,"mae":-.01,"hit_plus_05":False,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False}
bad=dict(base,resolution_epoch=104.999)
try:resolve_exact(bad,r);raise AssertionError("non-future outcome admitted")
except ValueError as e:assert str(e)=="NON_FUTURE_RESOLUTION_REJECTED"
row=resolve_exact(dict(base,resolution_epoch=105.0),r);assert row["strictly_future"] is True and row["matched_family_ids"]==["F"]
print("[RESOLUTION_EPOCH]",row["resolution_epoch"]);print("[PASS] OPD-044 exact OPD-033 strictly-future resolver boundary certified")
