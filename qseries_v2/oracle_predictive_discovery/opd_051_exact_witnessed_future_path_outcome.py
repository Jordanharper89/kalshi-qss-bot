from qseries_v2.oracle_predictive_discovery.opd_050_exact_horizon_coverage_witness import read_path_and_witness
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def materialize_from_path_and_witness(state,path,witness):
 t0=float(state["observed_epoch"]);end=t0+int(state["horizon_seconds"]);p0=float(state["anchor_price"])
 if witness is None or float(witness["event_epoch"])<end:return None
 future=[x for x in path if x["ticker"]==state["ticker"] and t0<float(x["event_epoch"])<=end]
 if not future:
  return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":0.0,"mfe":0.0,"mae":0.0,
  "hit_plus_05":False,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False,
  "future_end_price":p0,"time_to_max_seconds":0.0,"time_to_min_seconds":0.0,
  "coverage_witness_epoch":float(witness["event_epoch"]),"outcome_basis":"CARRY_FORWARD_NO_SAME_TICKER_EVENT_BEFORE_HORIZON"}
 future.sort(key=lambda x:(x["event_epoch"],x.get("sequence_number",0)))
 pend=float(future[-1]["price"]);mx=max(future,key=lambda x:float(x["price"]));mn=min(future,key=lambda x:float(x["price"]))
 mfe=float(mx["price"])-p0;mae=float(mn["price"])-p0
 return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":pend-p0,"mfe":mfe,"mae":mae,
 "hit_plus_05":mfe>=.05,"hit_minus_05":mae<=-.05,"hit_plus_10":mfe>=.10,"hit_minus_10":mae<=-.10,
 "future_end_price":pend,"time_to_max_seconds":float(mx["event_epoch"])-t0,"time_to_min_seconds":float(mn["event_epoch"])-t0,
 "coverage_witness_epoch":float(witness["event_epoch"]),"outcome_basis":"OBSERVED_SAME_TICKER_PATH"}

def materialize_live(state,root=None,guard_seconds=30.0):
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 path,witness=read_path_and_witness(state["ticker"],state["observed_epoch"],end,root,guard_seconds)
 return materialize_from_path_and_witness(state,path,witness)
