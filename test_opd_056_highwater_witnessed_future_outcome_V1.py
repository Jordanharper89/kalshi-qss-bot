from unittest.mock import patch
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m
s={"state_id":"S056","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
p=[{"ticker":"KXTEST","event_epoch":101.0,"price":.52,"sequence_number":10},{"ticker":"KXTEST","event_epoch":104.0,"price":.57,"sequence_number":11}]
w={"ticker":"KXTEST","event_epoch":106.0,"price":.56,"sequence_number":12}
with patch.object(m,"read_until_witness",lambda *a,**k:(p,w,12)):
 x=m.materialize_live(s,".")
 assert round(x["future_return"],8)==.07 and x["coverage_highwater_sequence"]==12
print("[RETURN]",x["future_return"],"[HIGHWATER]",x["coverage_highwater_sequence"])
print("[PASS] OPD-056 highwater witnessed outcome cutover certified")
