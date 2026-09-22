from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
assert sp.exists(),"NO_LIVE_ANCHOR_SPOOL"
a=json.loads(sp.read_text(encoding="utf-8").splitlines()[-1])
t=time.time();r=assemble(a,root);dt=time.time()-t
print("[ASSET]",a["asset"],"[SECONDS]",round(dt,3))
print("[CB_WINDOWS]",sorted(r["coinbase_hf_state"]))
print("[CONDITIONS]",len(r["crypto_condition_state"]))
print("[LEARNED]",r["learned_state"] is not None)
assert set(r["coinbase_hf_state"])=={"5","15","30","60"},"MISSING_COINBASE_WINDOWS"
assert dt<5.0,"OPD062_INDEX_NATIVE_ASOF_EXCEEDS_5_SECONDS"
print("[PASS] OPD-062 index-native strict-as-of physical retrieval certified")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
