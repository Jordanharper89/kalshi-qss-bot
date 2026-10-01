from __future__ import annotations
import json
from pathlib import Path
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
D=Path("runtime_state/qseries/qarb_clean_bot/qarb_056a_damm_runtime_graph_extension.json")
C=Path("runtime_state/qseries/qarb_clean_bot/qarb_058a_clmm_local_swap_math.json")
O=Path("runtime_state/qseries/qarb_clean_bot/qarb_058b_orca_local_swap_math.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_058c_runtime_endpoint_cutover_gate.json")
def load(root,p):
    q=Path(root)/p
    if not q.is_file():raise RuntimeError("MISSING:"+str(p))
    return json.loads(q.read_text(encoding="utf-8"))
def build(root):
    d=load(root,D);cl=load(root,C);oc=load(root,O)
    gates={
      "METEORA_DAMM_V2":bool(d.get("priced_live") and d.get("directed_edges",0)>=6),
      "RAYDIUM_CLMM_MATH_BOUND":bool(cl.get("math_bound_pools",0)>=2 and cl.get("probe_complete_pools",0)>=2),
      "ORCA_WHIRLPOOL_MATH_BOUND":bool(oc.get("math_bound_pools",0)>=2 and oc.get("probe_complete_pools",0)>=2)}
    ready=all(gates.values())
    payload={"revision":"QARB_058C","gates":gates,"local_math_bound":ready,
             "runtime_cutover_ready":False,
             "remaining":["REPLAY_VALIDATE_CLMM_ORCA_QUOTES","BIND_LOCAL_PROVIDERS","MERGE_ENDPOINTS_INTO_EXISTING_051D_GRAPH"] if ready else ["REPAIR_FAILED_MATH_GATE"],
             "next":"QARB_059_REPLAY_VALIDATION_AND_EXISTING_RUNTIME_CUTOVER" if ready else "HOLD_REPAIR_FAILED_MATH_GATE",
             "execution_authority":False,"paper_only":True}
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");return payload
def main():
    p=build(Path.cwd())
    print("[QARB-058C] RUNTIME ENDPOINT CUTOVER GATE")
    print("[GATES] "+json.dumps(p["gates"],sort_keys=True))
    print("[LOCAL_MATH_BOUND]",p["local_math_bound"])
    print("[RUNTIME_CUTOVER_READY]",p["runtime_cutover_ready"])
    print("[REMAINING] "+",".join(p["remaining"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
