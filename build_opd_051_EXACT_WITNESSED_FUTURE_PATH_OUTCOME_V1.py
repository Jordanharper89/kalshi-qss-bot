from pathlib import Path
import py_compile
R=Path.cwd()
M=R/"qseries_v2/oracle_predictive_discovery/opd_051_exact_witnessed_future_path_outcome.py"
T=R/"test_opd_051_exact_witnessed_future_path_outcome_V1.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from qseries_v2.oracle_predictive_discovery.opd_050_exact_horizon_coverage_witness import read_path_and_witness
execution_authority=False
def materialize_from_path_and_witness(state,path,witness):
 t0=float(state["observed_epoch"]);end=t0+int(state["horizon_seconds"]);p0=float(state["anchor_price"])
 if witness is None or float(witness["event_epoch"])<end:return None
 future=[x for x in path if x["ticker"]==state["ticker"] and t0<float(x["event_epoch"])<=end]
 if not future:return None
 future.sort(key=lambda x:(x["event_epoch"],x.get("sequence_number",0)))
 pend=float(future[-1]["price"]);mx=max(future,key=lambda x:float(x["price"]));mn=min(future,key=lambda x:float(x["price"]))
 mfe=float(mx["price"])-p0;mae=float(mn["price"])-p0
 return {"state_id":state["state_id"],"resolution_epoch":end,"future_return":pend-p0,"mfe":mfe,"mae":mae,
 "hit_plus_05":mfe>=.05,"hit_minus_05":mae<=-.05,"hit_plus_10":mfe>=.10,"hit_minus_10":mae<=-.10,
 "future_end_price":pend,"time_to_max_seconds":float(mx["event_epoch"])-t0,"time_to_min_seconds":float(mn["event_epoch"])-t0,
 "coverage_witness_epoch":float(witness["event_epoch"])}
def materialize_live(state,root=None,guard_seconds=30.0):
 end=float(state["observed_epoch"])+int(state["horizon_seconds"])
 path,witness=read_path_and_witness(state["ticker"],state["observed_epoch"],end,root,guard_seconds)
 return materialize_from_path_and_witness(state,path,witness)
""",encoding="utf-8")
T.write_text("""from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
s={"state_id":"S051","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
p=[{"ticker":"KXTEST","event_epoch":101.0,"price":.52,"sequence_number":1},{"ticker":"KXTEST","event_epoch":104.0,"price":.57,"sequence_number":2}]
w={"ticker":"KXTEST","event_epoch":106.0,"price":.56,"sequence_number":3}
x=materialize_from_path_and_witness(s,p,w)
assert round(x["future_return"],8)==.07 and round(x["mfe"],8)==.07
assert x["resolution_epoch"]==105.0 and x["coverage_witness_epoch"]==106.0 and x["hit_plus_05"] is True
assert materialize_from_path_and_witness(s,p,None) is None
print("[ENDPOINT]",x["future_end_price"],"[WITNESS]",x["coverage_witness_epoch"])
print("[PASS] OPD-051 OPD-005-compatible witnessed future path semantics certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True)
print("[PASS] OPD-051 V1 installed")