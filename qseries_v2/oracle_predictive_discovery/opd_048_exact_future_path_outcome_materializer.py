from qseries_v2.oracle_predictive_discovery.opd_047_bounded_post_t_kalshi_reader import read_post_t
execution_authority=False
def materialize_from_points(state,points):
 t0=float(state["observed_epoch"]);h=int(state["horizon_seconds"]);end=t0+h;p0=float(state["anchor_price"])
 future=[x for x in points if x["ticker"]==state["ticker"] and t0<float(x["event_epoch"])<=end]
 if not future or max(float(x["event_epoch"]) for x in future)<end:return None
 future.sort(key=lambda x:(x["event_epoch"],x.get("sequence_number",0)))
 pend=float(future[-1]["price"]);mx=max(future,key=lambda x:float(x["price"]));mn=min(future,key=lambda x:float(x["price"]))
 mfe=float(mx["price"])-p0;mae=float(mn["price"])-p0
 return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":pend-p0,"mfe":mfe,"mae":mae,"hit_plus_05":mfe>=.05,"hit_minus_05":mae<=-.05,"hit_plus_10":mfe>=.10,"hit_minus_10":mae<=-.10,"future_end_price":pend,"time_to_max_seconds":float(mx["event_epoch"])-t0,"time_to_min_seconds":float(mn["event_epoch"])-t0}
def materialize_live(state,root=None):
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 return materialize_from_points(state,read_post_t(state["ticker"],state["observed_epoch"],end,root))
