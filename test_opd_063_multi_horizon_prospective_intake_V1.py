from pathlib import Path
from tempfile import TemporaryDirectory
import json
from qseries_v2.oracle_predictive_discovery.opd_063_multi_horizon_prospective_intake import HORIZONS,intake_anchor
with TemporaryDirectory() as td:
 root=Path(td);rt=root/"runtime/predictive_data";rt.mkdir(parents=True)
 (rt/"opd_031_prospective_candidate_freeze.json").write_text(json.dumps({"activation_epoch":1.0,"candidates":[]}))
 a={"anchor_id":"a","ticker":"KXBTC-X","asset":"BTC","observed_epoch":100.0,"anchor_price":.5,"kalshi_state":{"trade_price":.5}}
 def asm(anchor,root):return {"coinbase_hf_state":{},"crypto_condition_state":{},"learned_state":None}
 rows=intake_anchor(a,root,Path.cwd(),asm)
 assert len(rows)==len(HORIZONS)==7
 ledger=[json.loads(x) for x in (rt/"opd_032_prospective_state_ledger.jsonl").read_text().splitlines()]
 assert sorted(x["horizon_seconds"] for x in ledger)==list(HORIZONS)
 print("[HORIZONS]",HORIZONS)
 print("[PASS] OPD-063 multi-horizon prospective intake + durable queue certified")
