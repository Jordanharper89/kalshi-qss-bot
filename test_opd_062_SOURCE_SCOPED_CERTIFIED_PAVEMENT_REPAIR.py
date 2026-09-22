from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble,_source_ids
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
a=json.loads([x for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()][-1])
print("[ANCHOR]",a["asset"],a["ticker"],a["anchor_id"][:12])
print("[CERTIFIED_LOCAL_CONDITION_SOURCES]",len(_source_ids(root,a["asset"])))
t=time.time();r=assemble(a,root);dt=time.time()-t
print("[SECONDS]",round(dt,3))
print("[CB_WINDOWS]",sorted(r["coinbase_hf_state"]))
print("[CONDITION_METRICS]",len(r["crypto_condition_state"]))
print("[LEARNED]",r["learned_state"] is not None)
assert set(r["coinbase_hf_state"])=={"5","15","30","60"},"MISSING_COINBASE_WINDOWS"
assert r["crypto_condition_state"],"NO_CONDITION_STATE"
assert dt<5.0,"SOURCE_SCOPED_ASOF_EXCEEDS_5_SECONDS"
print("[PASS] existing OPD-062 repaired on exact-source + exact-anchor certified pavement")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
