from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q76

STATE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_077_atomic_candidate_composition.json")
EXECUTION_AUTHORITY=False
REAL_MONEY_MOVED=False

def audit(root):
    root=Path(root)
    b=json.loads((root/q76.STATE).read_text(encoding="utf-8"))
    pairs,_=hot.priority_prepare_pairs(root)
    pm={(p.token,p.pump_pool,p.meteora_pool):p for p in pairs}
    _,user=c.sim_identity()
    rows={}
    for t,x in b.get("bindings",{}).items():
        if not x.get("bound"): continue
        pair=pm.get((t,x["pump_pool"],x["meteora_pool"]))
        if pair is None:
            rows[t]={"ok":False,"error":"CURRENT_EXACT_PAIR_NOT_FOUND"}
            continue
        try:
            route=las.compose_bound(user,pair,float(x["size_sol"]))
            cs=list(route.get("candidates",[]))
            labels=[str(v[0]) if isinstance(v,(tuple,list)) and v else
                str(v.get("label","CANDIDATE_%d"%i)) if isinstance(v,dict) else
                "CANDIDATE_%d"%i
                for i,v in enumerate(cs)]
            rows[t]={"ok":bool(cs),"size_sol":x["size_sol"],
                     "pump_pool":x["pump_pool"],"meteora_pool":x["meteora_pool"],
                     "candidate_labels":labels,
                     "pre_sim_bps":route.get("pre_sim_bps")}
        except Exception as e:
            rows[t]={"ok":False,"size_sol":x["size_sol"],
                     "error":type(e).__name__+":"+str(e)}
    out={"revision":"QARB_077","rows":rows,
         "attempted":len(rows),
         "composed":sum(v.get("ok",False) for v in rows.values()),
         "execution_authority":False,"real_money_moved":False}
    p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    return out

def main():
    x=audit(Path.cwd())
    print("[QARB-077] CURRENT-BOUND ACTIVE ATOMIC CANDIDATE COMPOSITION")
    print("[COMPOSE] attempted=%d composed=%d"%(x["attempted"],x["composed"]))
    for t,r in x["rows"].items():
        print("[CANDIDATES] token=%s %s"%(t,r.get("candidate_labels",r.get("error"))))
    print("[MODE] composition_only execution_authority=FALSE real_money_moved=FALSE")

if __name__=="__main__":main()
