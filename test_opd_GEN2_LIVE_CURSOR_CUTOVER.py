import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_live_cursor_cutover as m

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps({"activation_epoch":100.0}))
    rows=[
        {"observed_epoch":90.0,"anchor_id":"old1"},
        {"observed_epoch":99.0,"anchor_id":"old2"},
        {"observed_epoch":101.0,"anchor_id":"new1"},
        {"observed_epoch":102.0,"anchor_id":"new2"},
    ]
    raw="".join(json.dumps(x)+"\n" for x in rows)
    (rt/"opd_061_live_anchor_spool.jsonl").write_text(raw)
    old_end=len((json.dumps(rows[0])+"\n").encode("utf-8"))
    (rt/"opd_065_intake_cursor.json").write_text(json.dumps({"byte_offset":old_end}))
    x=m.cutover(r)
    expected=len(((json.dumps(rows[0])+"\n")+(json.dumps(rows[1])+"\n")).encode("utf-8"))
    assert x["byte_offset"]==expected
    assert x["post_freeze_anchors_present"]==2
    assert x["byte_offset"]>=x["old_byte_offset"]

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps({"activation_epoch":1000.0}))
    (rt/"opd_061_live_anchor_spool.jsonl").write_text(json.dumps({"observed_epoch":10.0})+"\n")
    x=m.cutover(r)
    assert x["byte_offset"]==x["spool_eof"]
    assert x["post_freeze_anchors_present"]==0

assert m.execution_authority is False
print("[PASS] Gen2 cutover skips only pre-freeze backlog and never rewinds worker cursor")
print("[PASS] post-freeze anchors already in spool remain available for worker intake")
print("[EXECUTION_AUTHORITY] FALSE")
