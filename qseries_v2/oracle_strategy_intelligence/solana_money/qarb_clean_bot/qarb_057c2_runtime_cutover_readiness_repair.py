from __future__ import annotations
import json
from pathlib import Path
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
A=Path("runtime_state/qseries/qarb_clean_bot/qarb_056a_damm_runtime_graph_extension.json")
B=Path("runtime_state/qseries/qarb_clean_bot/qarb_057a2_clmm_directional_tick_array_resolver.json")
C=Path("runtime_state/qseries/qarb_clean_bot/qarb_057b_orca_tick_array_pda_resolver.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_057c2_runtime_cutover_readiness_repair.json")

def load(root,p):
    q=Path(root)/p
    if not q.is_file():raise RuntimeError("MISSING:"+str(p))
    return json.loads(q.read_text(encoding="utf-8"))

def build(root):
    d=load(root,A);cl=load(root,B);oc=load(root,C)
    gates={
      "METEORA_DAMM_V2":bool(d.get("priced_live") and d.get("directed_edges",0)>=6),
      "RAYDIUM_CLMM":bool(cl.get("directional_boundary_ready",0)>=2 and cl.get("both_direction_array_sequences",0)>=2),
      "ORCA_WHIRLPOOL":bool(oc.get("both_direction_sequences_ready",0)>=2)}
    all_ready=all(gates.values())
    payload={"revision":"QARB_057C2","gates":gates,"pavement_complete_for_math":all_ready,
             "runtime_cutover_ready":False,
             "remaining":["CLMM_LOCAL_SWAP_MATH","ORCA_LOCAL_SWAP_MATH","MERGE_NEW_ENDPOINTS_INTO_EXISTING_051D_GRAPH"] if all_ready else ["UNRESOLVED_PAVEMENT_GATE"],
             "next":"QARB_058_LOCAL_SWAP_MATH_AND_RUNTIME_ENDPOINT_CUTOVER" if all_ready else "HOLD_REPAIR_FAILED_GATE",
             "execution_authority":False,"paper_only":True}
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-057C2] RUNTIME CUTOVER READINESS REPAIR")
    print("[GATES] "+json.dumps(p["gates"],sort_keys=True))
    print("[PAVEMENT_COMPLETE_FOR_MATH]",p["pavement_complete_for_math"])
    print("[RUNTIME_CUTOVER_READY]",p["runtime_cutover_ready"])
    print("[REMAINING] "+",".join(p["remaining"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
