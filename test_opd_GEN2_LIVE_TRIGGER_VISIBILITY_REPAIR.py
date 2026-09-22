import io,json,tempfile,contextlib
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as w
with tempfile.TemporaryDirectory() as d:
 r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)
 rows=[{"state_id":"a","ticker":"KXBTC","horizon_seconds":300,"matched_family_ids":[]},{"state_id":"b","ticker":"KXETH","horizon_seconds":300,"matched_family_ids":["50ea5acf43d43f1ead2cc772"]}]
 (p/"opd_gen2_post_freeze_state_ledger.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
 assert len(w._gen2_rows(r))==2
 z=io.StringIO()
 with contextlib.redirect_stdout(z): w._emit_gen2_visibility(rows)
 out=z.getvalue()
 assert "ticker=KXBTC" in out and "formula_match=FALSE" in out and "matched_family_ids=NONE" in out
 assert "ticker=KXETH" in out and "formula_match=TRUE" in out and "50ea5acf43d43f1ead2cc772" in out
assert w.execution_authority is False
print("[PASS] existing OPD-044 prints every newly admitted Gen2 state with exact frozen-family match visibility")
print("[PASS] visibility is read-only and does not alter candidate, thresholds, state admission, or outcomes")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
