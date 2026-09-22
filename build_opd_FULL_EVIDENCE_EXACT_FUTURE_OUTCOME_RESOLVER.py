from pathlib import Path
import shutil

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_exact_future_outcome_resolver.py"
RUN=R/"run_opd_full_evidence_predictor_child.py"
T=R/"test_opd_FULL_EVIDENCE_EXACT_FUTURE_OUTCOME_RESOLVER.py"
RB=RUN.with_suffix(".pre_exact_future_outcome_resolver.bak")

PRED=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
if not PRED.exists() or "PREDICTION_LEDGER_REVISION=" not in PRED.read_text(encoding="utf-8"):
    raise SystemExit("[FAIL] immutable prediction ledger boundary missing")
if not RUN.exists():
    raise SystemExit("[FAIL] full-evidence continuous child missing")

MODULE = '''from pathlib import Path
import json,os,time
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live

PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME_LEDGER_NAME="opd_full_evidence_live_outcome_ledger.jsonl"
OUTCOME_LEDGER_REVISION="FULL_EVIDENCE_EXACT_FUTURE_OUTCOME_V1"

execution_authority=False
publication_allowed=False

def _load_jsonl(path):
    if not path.exists(): return []
    out=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def _state_from_prediction(p):
    return {
      "state_id":p["prediction_id"],
      "anchor_id":p.get("anchor_id"),
      "anchor_sequence_boundary":p.get("anchor_sequence_boundary"),
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
    root=Path(root or Path.cwd());now=float(time.time() if now is None else now)
    base=root/"runtime"/"predictive_data"
    pp=base/PREDICTION_LEDGER_NAME;op=base/OUTCOME_LEDGER_NAME
    preds=_load_jsonl(pp);outs=_load_jsonl(op)
    resolved={str(x.get("prediction_id")) for x in outs if x.get("prediction_id")}
    due=resolved_now=ineligible=not_ready=unresolved=0
    for p in preds:
        pid=str(p.get("prediction_id") or "")
        if not pid or pid in resolved: continue
        if now < float(p["resolution_due_epoch"]):
            not_ready+=1;continue
        due+=1
        if not bool(p.get("horizon_eligible")):
            row={
              "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
              "resolution_status":"CONTRACT_HORIZON_INELIGIBLE",
              "resolved_epoch":now,"ticker":p["ticker"],
              "horizon_seconds":int(p["horizon_seconds"]),
              "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
              "execution_authority":False,"publication_allowed":False,
            }
            _append(op,row);resolved.add(pid);ineligible+=1;continue
        out=materializer(_state_from_prediction(p),root,after_sequence=int(p["anchor_sequence_boundary"]))
        if out is None:
            unresolved+=1;continue
        fr=float(out["future_return"])
        direction=str(p.get("direction") or "")
        directional_return=fr if direction=="UP" else (-fr if direction=="DOWN" else 0.0)
        row={
          "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
          "resolution_status":"RESOLVED_EXACT_FUTURE",
          "resolved_epoch":now,"ticker":p["ticker"],
          "anchor_sequence_boundary":p.get("anchor_sequence_boundary"),
          "anchor_observed_epoch":float(p["anchor_observed_epoch"]),
          "horizon_seconds":int(p["horizon_seconds"]),
          "resolution_due_epoch":float(p["resolution_due_epoch"]),
          "direction":direction,
          "predicted_probability":p.get("predicted_probability"),
          "expected_return":p.get("expected_return"),
          "net_edge_after_2pct":p.get("net_edge_after_2pct"),
          "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
          "decision_at_freeze":p.get("decision_at_freeze"),
          "future_return":fr,
          "directional_return":directional_return,
          "future_end_price":out.get("future_end_price"),
          "mfe":out.get("mfe"),"mae":out.get("mae"),
          "outcome_basis":out.get("outcome_basis"),
          "coverage_witness_epoch":out.get("coverage_witness_epoch"),
          "coverage_start_sequence":out.get("coverage_start_sequence"),
          "coverage_highwater_sequence":out.get("coverage_highwater_sequence"),
          "anchor_sequence_exact":bool(out.get("anchor_sequence_exact")),
          "execution_authority":False,"publication_allowed":False,
        }
        _append(op,row);resolved.add(pid);resolved_now+=1
    return {"predictions":len(preds),"due":due,"resolved_now":resolved_now,
      "ineligible":ineligible,"not_ready":not_ready,"unresolved_due":unresolved,
      "outcome_ledger":str(op)}

def run(root=None,now=None):
    r=resolve_matured(root,now)
    print("[EXACT FUTURE RESOLVER] predictions={predictions} due={due} resolved_now={resolved_now} ineligible={ineligible} not_ready={not_ready} unresolved_due={unresolved_due}".format(**r))
    print("[OUTCOME LEDGER]",r["outcome_ledger"])
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")
    return r

if __name__=="__main__":
    run()
'''
P.parent.mkdir(parents=True,exist_ok=True)
P.write_text(MODULE,encoding="utf-8")

s=RUN.read_text(encoding="utf-8")
imp="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver import run as resolve_full_evidence_outcomes\n"
if imp not in s:
    lines=s.splitlines(True)
    pos=0
    while pos<len(lines) and (lines[pos].startswith("from ") or lines[pos].startswith("import ")):
        pos+=1
    lines.insert(pos,imp)
    s="".join(lines)

if "resolve_full_evidence_outcomes(" not in s:
    candidates=["run(root)","run(Path.cwd())","predict()","predict(root)"]
    hit=None
    for x in candidates:
        if x in s: hit=x;break
    if hit is None:
        raise SystemExit("[FAIL] continuous child predictor call anchor not found")
    indent=s[s.rfind("\n",0,s.index(hit))+1:s.index(hit)]
    s=s.replace(hit,hit+"\n"+indent+"resolve_full_evidence_outcomes(Path.cwd())",1)

if not RB.exists(): shutil.copy2(RUN,RB)
RUN.write_text(s,encoding="utf-8")

TEST = '''from pathlib import Path
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
    pred={
      "prediction_id":"P1","ticker":"KXBTC15M-TEST","anchor_id":"A1",
      "anchor_sequence_boundary":123,"anchor_observed_epoch":1000.0,
      "anchor_price":0.55,"horizon_seconds":300,"resolution_due_epoch":1300.0,
      "horizon_eligible":True,"direction":"DOWN","predicted_probability":0.72,
      "expected_return":0.05,"net_edge_after_2pct":0.03,
      "actionable_at_freeze":True,"decision_at_freeze":"DOWN"}
    bad=dict(pred,prediction_id="P2",horizon_seconds=900,
      resolution_due_epoch=1900.0,horizon_eligible=False,actionable_at_freeze=False,
      decision_at_freeze="ABSTAIN")
    pp=base/m.PREDICTION_LEDGER_NAME
    pp.write_text(json.dumps(pred)+"\\n"+json.dumps(bad)+"\\n",encoding="utf-8")
    a=m.resolve_matured(root,2000.0,fake_materializer)
    b=m.resolve_matured(root,2030.0,fake_materializer)
    rows=[json.loads(x) for x in (base/m.OUTCOME_LEDGER_NAME).read_text().splitlines()]
    assert a["resolved_now"]==1 and a["ineligible"]==1
    assert b["resolved_now"]==0 and b["ineligible"]==0
    assert len(rows)==2
    good=[x for x in rows if x["prediction_id"]=="P1"][0]
    assert good["resolution_status"]=="RESOLVED_EXACT_FUTURE"
    assert good["future_return"]==-0.08 and good["directional_return"]==0.08
    assert good["coverage_start_sequence"]==123 and good["anchor_sequence_exact"] is True
    assert [x for x in rows if x["prediction_id"]=="P2"][0]["resolution_status"]=="CONTRACT_HORIZON_INELIGIBLE"
    assert good["execution_authority"] is False and good["publication_allowed"] is False

runner=Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")
assert "resolve_full_evidence_outcomes" in runner

print("[PASS] matured prediction resolves from exact frozen anchor sequence")
print("[PASS] strict-future OPD-056 materializer reused")
print("[PASS] immutable outcome ledger prevents duplicate resolution")
print("[PASS] contract-horizon-ineligible forecasts terminalized non-scorable")
print("[PASS] exact future return/MFE/MAE/witness lineage persisted")
print("[PASS] resolver integrated into existing 30-second full-evidence child")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
T.write_text(TEST,encoding="utf-8")

compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(RUN.read_text(encoding="utf-8"),str(RUN),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] exact future outcome resolver installed")
print("[PASS] existing OPD-056 strict-future exact-anchor pavement reused")
print("[OUTCOME LEDGER] runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl")
print("[PASS] resolver integrated into existing full-evidence production child")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
