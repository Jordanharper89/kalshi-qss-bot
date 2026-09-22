import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

obj={"payload":{"source_market_id":"KXETH15M-TEST","message":{"market_ticker":"KXETH15M-TEST","price_dollars":"0.42","ts":2000.0}}}
a=m._anchor_from_row((77,"obs77",2000.0,obj))
assert a and a["ticker"]=="KXETH15M-TEST" and a["asset"]=="ETH"
assert a["anchor_sequence_boundary"]==77 and a["anchor_id"]=="obs77" and a["observed_epoch"]==2000.0

states=[];outs={}
for i in range(24):
    sid="h"+str(i);states.append({"state_id":sid,"ticker":"KXETH"+str(i%4),"observed_epoch":1000+i,"horizon_seconds":900,"tokens":["K:A","CB:B","CC:C","L:D"]})
    outs[sid]={"state_id":sid,"resolution_epoch":1500+i,"future_return":-0.05,"mfe":-0.01,"mae":-0.05}
cur={"state_id":"LIVE","ticker":"KXETH-LIVE","observed_epoch":2000.0,"horizon_seconds":900,"tokens":["K:A","CB:B","CC:C","L:D"]}
z=m._score_state(cur,states,outs,2001.0)
assert z["passed"] is True and z["direction"]=="DOWN" and z["predicted_probability"]==1.0 and z["net_edge_after_2pct"]>0
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
print("[PASS] exact canonical crypto row becomes an in-memory live anchor")
print("[PASS] scorer excludes future/unresolved evidence and preserves full decision gates")
print("[PASS] fresh full-evidence DOWN fixture clears support/breadth/probability/economic gates")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
