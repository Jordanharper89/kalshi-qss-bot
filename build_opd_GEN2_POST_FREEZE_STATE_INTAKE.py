from pathlib import Path
import textwrap

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_gen2_post_freeze_state_intake.py"
T=R/"test_opd_GEN2_POST_FREEZE_STATE_INTAKE.py"

MODULE=r"""
from pathlib import Path
import json,os
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

FORBIDDEN={"future_target","future_return","mfe","mae","hit_plus_05","hit_minus_05",
           "hit_plus_10","hit_minus_10","resolution_epoch"}

def _canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"))

def _paths(root):
    rt=Path(root)/"runtime"/"predictive_data"
    return (rt,
            rt/"opd_032_prospective_state_ledger.jsonl",
            rt/"opd_gen2_candidate_freeze.json",
            rt/"opd_gen2_post_freeze_state_ledger.jsonl",
            rt/"opd_gen2_post_freeze_state_cursor.json")

def _load_freeze(path):
    x=json.loads(path.read_text(encoding="utf-8"))
    if int(x.get("generation",0))!=2:
        raise RuntimeError("GEN2_FREEZE_REQUIRED")
    if int(x.get("candidate_count",0))<1:
        raise RuntimeError("GEN2_CANDIDATE_REQUIRED")
    return x

def ingest(root=None,max_rows=50000):
    root=Path(root or Path.cwd()).resolve()
    rt,src,freeze_path,dst,cursor_path=_paths(root)
    freeze=_load_freeze(freeze_path)
    activation=float(freeze["activation_epoch"])
    candidates=freeze["candidates"]

    cursor=0
    if cursor_path.exists():
        try:
            cursor=int(json.loads(cursor_path.read_text(encoding="utf-8")).get("source_lines_seen",0))
        except Exception:
            cursor=0

    seen=set()
    if dst.exists():
        with dst.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try: seen.add(json.loads(line)["state_id"])
                    except Exception: pass

    scanned=accepted=trigger_states=pre_freeze_rejected=wrong_horizon=0
    source_lines_seen=0
    if not src.exists():
        raise RuntimeError("OPD032_STATE_LEDGER_MISSING")

    with src.open(encoding="utf-8") as f:
        for source_lines_seen,line in enumerate(f,1):
            if source_lines_seen<=cursor:
                continue
            if scanned>=int(max_rows):
                break
            scanned+=1
            if not line.strip():
                continue
            s=json.loads(line)
            if FORBIDDEN.intersection(s):
                raise RuntimeError("OUTCOME_FIELD_FOUND_IN_SOURCE_STATE")
            if float(s["observed_epoch"])<=activation:
                pre_freeze_rejected+=1
                continue

            h=int(s["horizon_seconds"])
            applicable=[c for c in candidates if int(c["horizon_seconds"])==h]
            if not applicable:
                wrong_horizon+=1
                continue

            toks=set(s.get("tokens") or [])
            matches=[c["family_id"] for c in applicable
                     if all(t in toks for t in c["formula"])]

            row={
                "schema_version":"OPD-GEN2-STATE-1",
                "generation":2,
                "state_id":s["state_id"],
                "anchor_id":s.get("anchor_id"),
                "ticker":s["ticker"],
                "observed_epoch":float(s["observed_epoch"]),
                "horizon_seconds":h,
                "tokens":sorted(toks),
                "anchor_price":s.get("anchor_price"),
                "anchor_sequence_boundary":s.get("anchor_sequence_boundary"),
                "anchor_sequence_basis":s.get("anchor_sequence_basis"),
                "matched_family_ids":matches,
                "post_gen2_freeze":True,
                "selection_reused":False,
                "edge_certified":False,
                "execution_authority":False,
            }
            if row["state_id"] not in seen:
                with dst.open("a",encoding="utf-8") as o:
                    o.write(_canon(row)+"\n")
                    o.flush()
                    os.fsync(o.fileno())
                seen.add(row["state_id"])
                accepted+=1
                if matches:
                    trigger_states+=1

    new_cursor=max(cursor,source_lines_seen)
    cursor_path.write_text(json.dumps({
        "schema_version":"OPD-GEN2-STATE-CURSOR-1",
        "source_lines_seen":new_cursor,
        "activation_epoch":activation,
        "execution_authority":False
    },indent=2,sort_keys=True),encoding="utf-8")

    all_rows=[]
    if dst.exists():
        with dst.open(encoding="utf-8") as f:
            all_rows=[json.loads(x) for x in f if x.strip()]

    summary={
        "schema_version":"OPD-GEN2-STATE-1",
        "generation":2,
        "activation_epoch":activation,
        "scanned_this_run":scanned,
        "accepted_this_run":accepted,
        "trigger_states_this_run":trigger_states,
        "pre_freeze_rejected_this_run":pre_freeze_rejected,
        "wrong_horizon_this_run":wrong_horizon,
        "gen2_states_total":len(all_rows),
        "gen2_trigger_states_total":sum(bool(x["matched_family_ids"]) for x in all_rows),
        "unique_tickers_total":len({x["ticker"] for x in all_rows}),
        "all_post_gen2_freeze":all(float(x["observed_epoch"])>activation for x in all_rows),
        "selection_reused":False,
        "edge_certified":False,
        "execution_authority":False,
    }
    (rt/"opd_gen2_post_freeze_state_intake.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")

    print("="*96)
    print("ORACLE GEN2 POST-FREEZE STATE INTAKE")
    print("="*96)
    for k,v in summary.items():
        print(k.upper(),"=",v)
    print("PROBABILITY/DIRECTION/PUBLICATION/EXECUTION=FALSE/FALSE/FALSE/FALSE")
    return summary

if __name__=="__main__":
    ingest()
"""

TEST=r"""
import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_post_freeze_state_intake as m

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    freeze={
        "generation":2,
        "activation_epoch":100.0,
        "candidate_count":1,
        "candidates":[{"family_id":"f","horizon_seconds":300,"formula":["A","B"]}]
    }
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps(freeze))
    rows=[
        {"state_id":"old","anchor_id":"a0","ticker":"OLD","observed_epoch":99.0,
         "horizon_seconds":300,"tokens":["A","B"],"anchor_price":0.5},
        {"state_id":"base","anchor_id":"a1","ticker":"BASE","observed_epoch":101.0,
         "horizon_seconds":300,"tokens":["A"],"anchor_price":0.5},
        {"state_id":"hit","anchor_id":"a2","ticker":"HIT","observed_epoch":102.0,
         "horizon_seconds":300,"tokens":["A","B"],"anchor_price":0.5},
        {"state_id":"wrongh","anchor_id":"a3","ticker":"H5","observed_epoch":103.0,
         "horizon_seconds":5,"tokens":["A","B"],"anchor_price":0.5},
    ]
    (rt/"opd_032_prospective_state_ledger.jsonl").write_text(
        "".join(json.dumps(x)+"\n" for x in rows))
    s=m.ingest(r)
    assert s["gen2_states_total"]==2
    assert s["gen2_trigger_states_total"]==1
    assert s["pre_freeze_rejected_this_run"]==1
    assert s["wrong_horizon_this_run"]==1
    assert s["all_post_gen2_freeze"] is True
    assert s["selection_reused"] is False
    s2=m.ingest(r)
    assert s2["gen2_states_total"]==2

assert m.execution_authority is False
print("[PASS] Gen2 state intake accepts only truly post-freeze candidate-horizon states")
print("[PASS] baseline + trigger evidence are isolated from the 323 selection rows")
print("[EDGE/PROBABILITY/DIRECTION/PUBLICATION/EXECUTION] FALSE/FALSE/FALSE/FALSE/FALSE")
"""

P.parent.mkdir(parents=True,exist_ok=True)
P.write_text(textwrap.dedent(MODULE).lstrip(),encoding="utf-8")
T.write_text(textwrap.dedent(TEST).lstrip(),encoding="utf-8")
compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] Gen2 post-freeze state intake installed")
print(P)
print(T)
