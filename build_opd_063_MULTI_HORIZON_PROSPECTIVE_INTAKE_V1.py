from pathlib import Path
MODULE=r'''from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import intake_world_state
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
HORIZONS=(5,15,30,60,300,900,3600)

def intake_anchor(anchor,state_root=None,repo_root=None,assembler=None):
    state_root=Path(state_root or Path.cwd());repo_root=Path(repo_root or Path.cwd())
    extra=(assembler or assemble)(anchor,repo_root)
    out=[]
    for h in HORIZONS:
        s={"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],"observed_epoch":anchor["observed_epoch"],"horizon_seconds":h,"anchor_price":anchor["anchor_price"],"kalshi_state":anchor["kalshi_state"],"coinbase_hf_state":extra["coinbase_hf_state"],"crypto_condition_state":extra["crypto_condition_state"],"learned_state":extra["learned_state"]}
        out.append(intake_world_state(s,state_root,repo_root))
    rebuild_exact(state_root)
    return out
'''
TEST=r'''from pathlib import Path
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
'''
root=Path.cwd();m=root/"qseries_v2/oracle_predictive_discovery/opd_063_multi_horizon_prospective_intake.py"
m.parent.mkdir(parents=True,exist_ok=True);m.write_text(MODULE,encoding="utf-8")
(root/"test_opd_063_multi_horizon_prospective_intake_V1.py").write_text(TEST,encoding="utf-8")
print("[PASS] OPD-063 V1 installed")
