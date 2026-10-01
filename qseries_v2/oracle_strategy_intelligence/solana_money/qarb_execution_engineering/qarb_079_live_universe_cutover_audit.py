from __future__ import annotations
import inspect,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_045b_evidence_window_hotset_lifecycle as q45
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_047b_paced_dynamic_hotset_supervisor as q47
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061c_existing_runner_six_dex_valve_cutover as q61
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q72
STATE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_079_live_universe_audit.json")
EXECUTION_AUTHORITY=False;REAL_MONEY_MOVED=False
def audit(root):
 root=Path(root);learned=q70._load(root).get("tokens",{});life=q72.run(root).get("tokens",{})
 active={t for t,x in learned.items() if x.get("status")=="ACTIVE"}
 retired={t for t,x in life.items() if x.get("lifecycle")=="RETIRED"}
 path=root/q45.ACTIVE_BINDINGS
 try:dynamic=list(q47.binding_universe(path));err=None
 except Exception as e:dynamic=[];err=type(e).__name__+":"+str(e)
 dyn={x["token"] for x in dynamic if isinstance(x,dict) and x.get("token")}
 s60=inspect.getsource(q60);s61=inspect.getsource(q61)
 out={"revision":"QARB_079","binding_path":str(path),"binding_file_exists":path.is_file(),
 "startup_cached_prepare":("prepare_once" in s61 and "cached_prepare" in s61),
 "single_hydration_contract":("prepare_once" in s60),
 "dynamic_candidates":len(dynamic),"dynamic_tokens":sorted(dyn),
 "active_count":len(active),"retired_count":len(retired),
 "retired_reentry_candidates":sorted(retired&dyn),"dynamic_error":err,
 "gap_confirmed":("cached_prepare" in s61 and callable(q47.binding_universe)),
 "execution_authority":False,"real_money_moved":False}
 p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
def main():
 x=audit(Path.cwd());print("[QARB-079] LIVE UNIVERSE CUTOVER AUDIT")
 print("[BINDINGS] exists=%s dynamic=%d"%(x["binding_file_exists"],x["dynamic_candidates"]))
 print("[LIFECYCLE] active=%d retired=%d returns=%d"%(x["active_count"],x["retired_count"],len(x["retired_reentry_candidates"])))
 print("[GAP] startup_cached=%s single_hydration=%s gap_confirmed=%s"%(x["startup_cached_prepare"],x["single_hydration_contract"],x["gap_confirmed"]))
 for t in x["retired_reentry_candidates"]:print("[TOKEN_RETURN_CANDIDATE] token=%s"%t)
 if x["dynamic_error"]:print("[DYNAMIC_ERROR] "+x["dynamic_error"])
 print("[MODE] audit_only execution_authority=FALSE real_money_moved=FALSE")
if __name__=="__main__":main()
