from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_044_exact_strict_future_resolver.py";T=R/"test_opd_044_exact_strict_future_resolver_V5.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_033_prospective_future_outcome_resolver import resolve
execution_authority=False
REQ=("state_id","resolution_epoch","future_return","mfe","mae","hit_plus_05","hit_minus_05","hit_plus_10","hit_minus_10")
def resolve_exact(outcome,state_root=None):
 if not isinstance(outcome,dict) or any(k not in outcome for k in REQ):raise ValueError("MISSING_REQUIRED_OUTCOME_FIELD")
 return resolve(outcome,Path(state_root or Path.cwd()))
""",encoding="utf-8")
T.write_text("""import tempfile,json
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
r=Path(tempfile.mkdtemp());rt=r/"runtime/predictive_data";rt.mkdir(parents=True)
state={"state_id":"S044","anchor_id":"A044","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.54,"matched_family_ids":["F"],"post_freeze":True}
(rt/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(state)+"\\n")
base={"state_id":"S044","future_return":.01,"mfe":.02,"mae":-.01,"hit_plus_05":False,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False}
bad=dict(base,resolution_epoch=104.999)
try:resolve_exact(bad,r);raise AssertionError("non-future outcome admitted")
except ValueError as e:assert str(e)=="NON_FUTURE_RESOLUTION_REJECTED"
row=resolve_exact(dict(base,resolution_epoch=105.0),r);assert row["strictly_future"] is True and row["matched_family_ids"]==["F"]
print("[RESOLUTION_EPOCH]",row["resolution_epoch"]);print("[PASS] OPD-044 exact OPD-033 strictly-future resolver boundary certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-044 V5 installed")
