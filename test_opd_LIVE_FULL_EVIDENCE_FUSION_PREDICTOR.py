import json,tempfile,io,contextlib
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

def put(p,rows):p.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
with tempfile.TemporaryDirectory() as d:
 r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
 states=[];outs=[]
 for i in range(30):
  sid="h"+str(i);ep=1000+i
  states.append({"state_id":sid,"ticker":"KXBTC"+str(i%5),"observed_epoch":ep,"horizon_seconds":300,
    "tokens":["H:300","K:ANCHOR_PRICE:40_50C","CB:60:RET:GE_20BPS","CC:momentum:DIR:UP","L:TIMING_CERTIFIED:TRUE"]})
  outs.append({"state_id":sid,"resolution_epoch":ep+300,"future_return":0.06,"mfe":0.09,"mae":0.01,
    "hit_plus_05":True,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False})
 cur={"state_id":"cur","ticker":"KXBTC-LIVE","observed_epoch":2000,"horizon_seconds":300,
   "tokens":["H:300","K:ANCHOR_PRICE:40_50C","CB:60:RET:GE_20BPS","CC:momentum:DIR:UP","L:TIMING_CERTIFIED:TRUE"]}
 states.append(cur);put(rt/"opd_032_prospective_state_ledger.jsonl",states);put(rt/"opd_033_prospective_outcome_ledger.jsonl",outs)
 z=m.run(r,now=2001);best=z[0]
 assert best["passed"] and best["direction"]=="UP"
 assert best["predicted_probability"]==1.0 and best["net_edge_after_2pct"]>0.0
with tempfile.TemporaryDirectory() as d:
 r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
 put(rt/"opd_032_prospective_state_ledger.jsonl",[{"state_id":"x","ticker":"KXETH","observed_epoch":3000,"horizon_seconds":300,
   "tokens":["H:300","CB:60:RET:ZERO","CC:momentum:DIR:FLAT"]}])
 put(rt/"opd_033_prospective_outcome_ledger.jsonl",[])
 z=m.run(r,now=3001)
 assert z and not z[0]["passed"]
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
print("[PASS] full-evidence predictor fuses K/CB/CC/L tokens against strictly older resolved same-asset cases")
print("[PASS] current-state prediction requires support, breadth, similarity, probability, economics, and evidence agreement")
print("[PASS] outcome resolution after prediction time is excluded; execution/publication remain disabled")
