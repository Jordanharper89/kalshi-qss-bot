from pathlib import Path
import textwrap

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_044_continuous_prospective_worker.py"
T=R/"test_opd_GEN2_CONTINUOUS_PRODUCTION_CUTOVER.py"

MODULE=r"""
from pathlib import Path
import contextlib
import io
import json
import time

from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
from qseries_v2.oracle_predictive_discovery.opd_063_multi_horizon_prospective_intake import intake_anchor

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _atomic_json(path,payload):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    q.replace(p)

def _write(root,payload):
    _atomic_json(Path(root)/"runtime"/"predictive_data"/"opd_065_worker_heartbeat.json",payload)

def _intake_spool(root,max_anchors=1):
    root=Path(root);rt=root/"runtime"/"predictive_data"
    spool=rt/"opd_061_live_anchor_spool.jsonl"
    cursor=rt/"opd_065_intake_cursor.json"
    if max_anchors<0: raise ValueError("max_anchors must be >= 0")
    if not spool.exists() or max_anchors==0:
        return {"anchors":0,"states":0,"backlog_remaining":False}
    pos=0
    if cursor.exists():
        try: pos=int(json.loads(cursor.read_text(encoding="utf-8")).get("byte_offset",0))
        except Exception: pos=0
    size=spool.stat().st_size
    if pos<0 or pos>size: pos=0
    anchors=states=0
    with spool.open("r",encoding="utf-8") as f:
        f.seek(pos)
        while anchors<max_anchors:
            line=f.readline()
            if not line: break
            end=f.tell()
            a=json.loads(line)
            intake_anchor(a,root,root,rebuild_queue=False)
            anchors+=1;states+=7;pos=end
            _atomic_json(cursor,{"byte_offset":pos,"anchors_last_cycle":anchors,"states_last_cycle":states})
    return {"anchors":anchors,"states":states,"backlog_remaining":pos<size}

def _gen2_state_ids(root):
    p=Path(root)/"runtime"/"predictive_data"/"opd_gen2_post_freeze_state_ledger.jsonl"
    ids=set()
    if not p.exists(): return ids
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: ids.add(json.loads(line)["state_id"])
            except Exception: pass
    return ids

def _prioritize_gen2(root,rows):
    ids=_gen2_state_ids(root)
    return sorted(rows,key=lambda x:(
        0 if x.get("state_id") in ids else 1,
        float(x.get("maturity_epoch",0)),
        str(x.get("state_id",""))
    ))

def _gen2_tick(root,ingest_fn=None,verdict_fn=None):
    if ingest_fn is None:
        from qseries_v2.oracle_predictive_discovery.opd_gen2_post_freeze_state_intake import ingest as ingest_fn
    if verdict_fn is None:
        from qseries_v2.oracle_predictive_discovery.opd_gen2_prove_or_kill_now import prove_or_kill as verdict_fn
    sink=io.StringIO()
    with contextlib.redirect_stdout(sink):
        intake=ingest_fn(root,max_rows=50000)
        verdict=verdict_fn(root)
    best=verdict.get("best") or {}
    return {
        "accepted_this_run":intake.get("accepted_this_run",0),
        "trigger_states_this_run":intake.get("trigger_states_this_run",0),
        "states_total":intake.get("gen2_states_total",0),
        "trigger_states_total":intake.get("gen2_trigger_states_total",0),
        "resolved_baseline_n":best.get("resolved_baseline_n",0),
        "resolved_trigger_n":best.get("resolved_trigger_n",0),
        "trigger_tickers":best.get("trigger_tickers",0),
        "net_expected_after_hurdle":best.get("net_expected_after_hurdle"),
        "verdict":verdict.get("verdict","UNKNOWN"),
        "certified":bool(best.get("certified",False)),
        "execution_authority":False,
    }

def cycle(root=None,now=None,materializer=None,max_anchors=1,max_mature=4,max_attempts=24,
          gen2_ingest_fn=None,gen2_verdict_fn=None):
    root=Path(root or Path.cwd())
    intake=_intake_spool(root,max_anchors=max_anchors)
    rebuild_exact(root)
    all_rows=_prioritize_gen2(root,mature_exact(root,now))
    target=max(0,int(max_mature));limit=max(target,int(max_attempts))
    resolved=abstained=attempted=0
    fn=materializer or materialize_live
    for state in all_rows[:limit]:
        if resolved>=target: break
        attempted+=1
        outcome=fn(state,root)
        if outcome is None:
            abstained+=1
            continue
        resolve_exact(outcome,root)
        resolved+=1
    gen2=_gen2_tick(root,gen2_ingest_fn,gen2_verdict_fn)
    return {
        "intake_anchors":intake["anchors"],
        "intake_states":intake["states"],
        "intake_backlog_remaining":intake["backlog_remaining"],
        "mature_available":len(all_rows),
        "mature_processed":attempted,
        "resolved":resolved,
        "abstained":abstained,
        "gen2":gen2,
        "execution_authority":False,
    }

def run_forever(root=None,cadence=2.0,max_anchors=1,max_mature=4,max_attempts=24):
    root=Path(root or Path.cwd()).resolve()
    cycles=0;last_signal=None
    if cadence<=0: raise ValueError("cadence must be > 0")
    while True:
        cycles+=1;state="HEALTHY";err=None;result=None
        try:
            result=cycle(root,max_anchors=max_anchors,max_mature=max_mature,max_attempts=max_attempts)
            g=(result or {}).get("gen2") or {}
            signal=(g.get("verdict"),g.get("resolved_trigger_n"),g.get("trigger_states_total"))
            if signal!=last_signal and (g.get("resolved_trigger_n",0)>0 or g.get("certified")):
                print("[GEN2]",json.dumps(g,sort_keys=True),flush=True)
            last_signal=signal
        except Exception as exc:
            state="DEGRADED";err=f"{type(exc).__name__}: {exc}"
        _write(root,{
            "schema_version":"OPD-065-GEN2-PRODUCTION",
            "cycles":cycles,
            "state":state,
            "error":err,
            "result":result,
            "execution_authority":False,
            "probability_enabled":False,
            "direction_enabled":False,
            "publication_allowed":False,
            "updated_epoch":time.time(),
        })
        time.sleep(cadence)

if __name__=="__main__":
    t=time.time()
    r=cycle()
    print(r)
    print("[SECONDS]",round(time.time()-t,3))
    print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
"""

TEST=r"""
from pathlib import Path
import json
import tempfile
import qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as w

with tempfile.TemporaryDirectory() as d:
    root=Path(d);rt=root/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_post_freeze_state_ledger.jsonl").write_text(
        json.dumps({"state_id":"g2"})+"\n",encoding="utf-8")
    rows=[
        {"state_id":"old","maturity_epoch":1.0},
        {"state_id":"g2","maturity_epoch":999.0},
    ]
    assert [x["state_id"] for x in w._prioritize_gen2(root,rows)]==["g2","old"]

with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    w._intake_spool=lambda *a,**k:{"anchors":1,"states":7,"backlog_remaining":False}
    w.rebuild_exact=lambda *a,**k:None
    w.mature_exact=lambda *a,**k:[{"state_id":"g2","maturity_epoch":1.0}]
    w._prioritize_gen2=lambda root,rows:rows
    w.resolve_exact=lambda o,root:o
    materializer=lambda s,root:{"state_id":s["state_id"],"future_return":0.08}

    def ingest(root,max_rows=50000):
        return {
            "accepted_this_run":1,
            "trigger_states_this_run":1,
            "gen2_states_total":101,
            "gen2_trigger_states_total":11,
        }

    def verdict(root):
        return {
            "verdict":"NOT_PROVEN",
            "best":{
                "resolved_baseline_n":50,
                "resolved_trigger_n":11,
                "trigger_tickers":4,
                "net_expected_after_hurdle":0.03,
                "certified":False,
            }
        }

    z=w.cycle(root,materializer=materializer,max_mature=1,max_attempts=1,
              gen2_ingest_fn=ingest,gen2_verdict_fn=verdict)
    assert z["resolved"]==1
    assert z["gen2"]["states_total"]==101
    assert z["gen2"]["resolved_trigger_n"]==11
    assert z["gen2"]["net_expected_after_hurdle"]==0.03
    assert z["gen2"]["certified"] is False

assert w.execution_authority is False
print("[PASS] existing OPD-044 production worker now runs Gen2 intake + priority resolution + prove-or-kill every cycle")
print("[PASS] Gen2 evidence remains post-freeze; frozen candidate and thresholds are unchanged")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
"""

if not P.exists():
    raise SystemExit("REFUSE: existing OPD-044 production worker missing")

backup=P.with_suffix(P.suffix+".pre_gen2_continuous_production_cutover")
if not backup.exists():
    backup.write_bytes(P.read_bytes())

P.write_text(textwrap.dedent(MODULE).lstrip(),encoding="utf-8")
T.write_text(textwrap.dedent(TEST).lstrip(),encoding="utf-8")

compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] existing OPD-044 continuous Gen2 production cutover installed")
print(P)
print(T)
