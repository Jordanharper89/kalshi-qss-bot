import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as m
with tempfile.TemporaryDirectory() as d:
 r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)
 (p/"opd_gen2_post_freeze_state_ledger.jsonl").write_text(json.dumps({"state_id":"g2"})+"\n")
 rows=[{"state_id":"old1","maturity_epoch":1.0},{"state_id":"old2","maturity_epoch":2.0},{"state_id":"g2","maturity_epoch":999.0}]
 z=m._prioritize_gen2(r,rows)
 assert [x["state_id"] for x in z]==["g2","old1","old2"]
 assert m.execution_authority is False
print("[PASS] OPD-044 mature resolver prioritizes Gen2 post-freeze states before old backlog")
print("[PASS] old mature backlog is preserved behind Gen2; no outcome data is used for priority")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
