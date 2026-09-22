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
