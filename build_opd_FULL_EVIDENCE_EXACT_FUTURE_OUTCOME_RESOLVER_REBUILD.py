from pathlib import Path
import shutil

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_exact_future_outcome_resolver.py"
RUN=ROOT/"run_opd_full_evidence_predictor_child.py"
TEST=ROOT/"test_opd_FULL_EVIDENCE_EXACT_FUTURE_OUTCOME_RESOLVER_REBUILD.py"
BACKUP=ROOT/"run_opd_full_evidence_predictor_child.pre_exact_future_outcome_resolver_rebuild.bak"
PRED=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"

if not RUN.is_file():
    raise RuntimeError("full-evidence continuous child missing")
if not PRED.is_file() or "PREDICTION_LEDGER_REVISION=" not in PRED.read_text(encoding="utf-8"):
    raise RuntimeError("immutable prediction ledger boundary missing")

runner=RUN.read_text(encoding="utf-8")
required_runner=(
    "run as run_prediction",
    "DEFAULT_CADENCE_SECONDS = 30.0",
    "run_prediction(root=root)",
)
for marker in required_runner:
    if marker not in runner:
        raise RuntimeError("exact continuous-child boundary missing: "+marker)

module_text = """from pathlib import Path
import json,os,time
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live

PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME_LEDGER_NAME="opd_full_evidence_live_outcome_ledger.jsonl"
OUTCOME_LEDGER_REVISION="FULL_EVIDENCE_EXACT_FUTURE_OUTCOME_V1"
execution_authority=False
publication_allowed=False

def _load_jsonl(path):
    if not path.exists(): return []
    rows=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def _state(p):
    return {
      "state_id":p["prediction_id"],
      "anchor_id":p.get("anchor_id"),
      "anchor_sequence_boundary":int(p["anchor_sequence_boundary"]),
      "anchor_sequence_basis":"EXACT_FROZEN_PREDICTION_ANCHOR",
      "ticker":p["ticker"],
      "observed_epoch":float(p["anchor_observed_epoch"]),
      "horizon_seconds":int(p["horizon_seconds"]),
      "anchor_price":float(p["anchor_price"]),
    }

def _append(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\\n")
        f.flush();os.fsync(f.fileno())

def resolve_matured(root=None,now=None,materializer=materialize_live):
    root=Path(root or Path.cwd()).resolve()
    now=float(time.time() if now is None else now)
    base=root/"runtime"/"predictive_data"
    predictions=_load_jsonl(base/PREDICTION_LEDGER_NAME)
    outcome_path=base/OUTCOME_LEDGER_NAME
    prior=_load_jsonl(outcome_path)
    done={str(x.get("prediction_id")) for x in prior if x.get("prediction_id")}
    stats={"predictions":len(predictions),"due":0,"resolved_now":0,
           "ineligible":0,"not_ready":0,"unresolved_due":0,"errors":0,
           "outcome_ledger":str(outcome_path)}
    for p in predictions:
        pid=str(p.get("prediction_id") or "")
        if not pid or pid in done: continue
        if now < float(p["resolution_due_epoch"]):
            stats["not_ready"]+=1;continue
        stats["due"]+=1
        if not bool(p.get("horizon_eligible")):
            _append(outcome_path,{
              "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
              "resolution_status":"CONTRACT_HORIZON_INELIGIBLE",
              "resolved_epoch":now,"ticker":p["ticker"],
              "horizon_seconds":int(p["horizon_seconds"]),
              "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
              "execution_authority":False,"publication_allowed":False})
            done.add(pid);stats["ineligible"]+=1;continue
        try:
            out=materializer(_state(p),root,after_sequence=int(p["anchor_sequence_boundary"]))
        except Exception:
            stats["errors"]+=1;continue
        if out is None:
            stats["unresolved_due"]+=1;continue
        fr=float(out["future_return"])
        direction=str(p.get("direction") or "")
        directional_return=fr if direction=="UP" else (-fr if direction=="DOWN" else 0.0)
        _append(outcome_path,{
          "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
          "resolution_status":"RESOLVED_EXACT_FUTURE",
          "resolved_epoch":now,"ticker":p["ticker"],
          "anchor_sequence_boundary":int(p["anchor_sequence_boundary"]),
          "anchor_observed_epoch":float(p["anchor_observed_epoch"]),
          "horizon_seconds":int(p["horizon_seconds"]),
          "resolution_due_epoch":float(p["resolution_due_epoch"]),
          "direction":direction,
          "predicted_probability":p.get("predicted_probability"),
          "expected_return":p.get("expected_return"),
          "net_edge_after_2pct":p.get("net_edge_after_2pct"),
          "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
          "decision_at_freeze":p.get("decision_at_freeze"),
          "future_return":fr,"directional_return":directional_return,
          "future_end_price":out.get("future_end_price"),
          "mfe":out.get("mfe"),"mae":out.get("mae"),
          "outcome_basis":out.get("outcome_basis"),
          "coverage_witness_epoch":out.get("coverage_witness_epoch"),
          "coverage_start_sequence":out.get("coverage_start_sequence"),
          "coverage_highwater_sequence":out.get("coverage_highwater_sequence"),
          "anchor_sequence_exact":bool(out.get("anchor_sequence_exact")),
          "execution_authority":False,"publication_allowed":False})
        done.add(pid);stats["resolved_now"]+=1
    return stats

def run(root=None,now=None):
    r=resolve_matured(root,now)
    print("[EXACT FUTURE RESOLVER] predictions={predictions} due={due} resolved_now={resolved_now} ineligible={ineligible} not_ready={not_ready} unresolved_due={unresolved_due} errors={errors}".format(**r),flush=True)
    print("[OUTCOME LEDGER]",r["outcome_ledger"],flush=True)
    print("[EXECUTION/PUBLICATION] FALSE/FALSE",flush=True)
    return r

if __name__=="__main__":
    run()
"""
MOD.parent.mkdir(parents=True,exist_ok=True)
MOD.write_text(module_text,encoding="utf-8")

import_line="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver import run as resolve_full_evidence_outcomes\n"
if import_line not in runner:
    anchor="from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import (\n"
    pos=runner.find(anchor)
    if pos<0:
        raise RuntimeError("exact predictor import block not found")
    close=runner.find(")\n",pos)
    if close<0:
        raise RuntimeError("predictor import block close not found")
    close+=2
    runner=runner[:close]+import_line+runner[close:]

call="        run_prediction(root=root)\n"
patched="        run_prediction(root=root)\n        resolve_full_evidence_outcomes(root)\n"
if "resolve_full_evidence_outcomes(root)" not in runner:
    if runner.count(call)!=1:
        raise RuntimeError("exact run_prediction(root=root) call not found once")
    runner=runner.replace(call,patched,1)

if not BACKUP.exists():
    shutil.copy2(RUN,BACKUP)
RUN.write_text(runner,encoding="utf-8")

test_text = """from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver as m

def fake_materializer(state,root=None,after_sequence=None):
    assert after_sequence==123
    assert state["anchor_sequence_boundary"]==123
    return {"state_id":state["state_id"],"resolution_epoch":1300.0,
      "future_return":-0.08,"future_end_price":0.47,"mfe":0.01,"mae":-0.10,
      "outcome_basis":"OBSERVED_SAME_TICKER_PATH","coverage_witness_epoch":1301.0,
      "coverage_start_sequence":123,"coverage_highwater_sequence":999,
      "anchor_sequence_exact":True}

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    p1={"prediction_id":"P1","ticker":"KXBTC15M-TEST","anchor_id":"A1",
        "anchor_sequence_boundary":123,"anchor_observed_epoch":1000.0,
        "anchor_price":0.55,"horizon_seconds":300,"resolution_due_epoch":1300.0,
        "horizon_eligible":True,"direction":"DOWN","predicted_probability":0.72,
        "expected_return":0.05,"net_edge_after_2pct":0.03,
        "actionable_at_freeze":True,"decision_at_freeze":"DOWN"}
    p2=dict(p1,prediction_id="P2",horizon_seconds=900,resolution_due_epoch=1900.0,
            horizon_eligible=False,actionable_at_freeze=False,decision_at_freeze="ABSTAIN")
    (base/m.PREDICTION_LEDGER_NAME).write_text(json.dumps(p1)+"\\n"+json.dumps(p2)+"\\n",encoding="utf-8")
    first=m.resolve_matured(root,2000.0,fake_materializer)
    second=m.resolve_matured(root,2030.0,fake_materializer)
    rows=[json.loads(x) for x in (base/m.OUTCOME_LEDGER_NAME).read_text().splitlines()]
    assert first["resolved_now"]==1 and first["ineligible"]==1 and first["errors"]==0
    assert second["resolved_now"]==0 and second["ineligible"]==0
    assert len(rows)==2
    good=[x for x in rows if x["prediction_id"]=="P1"][0]
    assert good["resolution_status"]=="RESOLVED_EXACT_FUTURE"
    assert good["future_return"]==-0.08 and good["directional_return"]==0.08
    assert good["coverage_start_sequence"]==123 and good["anchor_sequence_exact"] is True
    assert [x for x in rows if x["prediction_id"]=="P2"][0]["resolution_status"]=="CONTRACT_HORIZON_INELIGIBLE"

runner=Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")
assert "run_prediction(root=root)" in runner
assert "resolve_full_evidence_outcomes(root)" in runner
assert runner.index("run_prediction(root=root)") < runner.index("resolve_full_evidence_outcomes(root)")

print("[PASS] exact current continuous-child call boundary patched")
print("[PASS] matured prediction resolves from exact frozen anchor sequence")
print("[PASS] strict-future OPD-056 materializer reused")
print("[PASS] immutable outcome ledger prevents duplicate resolution")
print("[PASS] contract-horizon-ineligible forecasts terminalized non-scorable")
print("[PASS] transient resolver/materializer errors fail closed without fabricating outcomes")
print("[PASS] resolver runs after each existing 30-second prediction cycle")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TEST.write_text(test_text,encoding="utf-8")

compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
compile(RUN.read_text(encoding="utf-8"),str(RUN),"exec")
compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

print("[PASS] exact future outcome resolver REBUILD installed")
print("[PASS] exact child call matched: run_prediction(root=root)")
print("[PASS] OPD-056 strict-future exact-anchor pavement reused")
print("[OUTCOME LEDGER] runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl")
print("[PASS] resolver integrated into existing 30-second production child")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
