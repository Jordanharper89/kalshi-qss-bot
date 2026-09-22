import qseries_v2.oracle_predictive_discovery.opd_edge_evidence_priority_drain_now as m
hs={300}
a={"state_id":"a","matched_family_ids":["f"],"horizon_seconds":300,"maturity_epoch":9}
b={"state_id":"b","matched_family_ids":[],"horizon_seconds":300,"maturity_epoch":1}
c={"state_id":"c","matched_family_ids":[],"horizon_seconds":5,"maturity_epoch":0}
assert sorted([c,b,a],key=lambda x:m._priority(x,hs))==[a,b,c]
assert m.execution_authority is False
print("[PASS] edge-evidence drain prioritizes frozen-family triggers then candidate-horizon baseline")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
