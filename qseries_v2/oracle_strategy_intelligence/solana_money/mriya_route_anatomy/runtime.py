from __future__ import annotations
import argparse,asyncio,time
from pathlib import Path
from .acquire import capture,Blocks
from .anatomy import analyze_target
from .persistence import read_json,write_json

def slots(rows):
    out=[]
    for r in rows:
        try:s=int(r.get("slot") or 0)
        except Exception:continue
        if s>0:out.append(s)
    return sorted(set(out),reverse=True)

def short_mint(x):
    return x if len(x)<=18 else x[:8]+"..."+x[-6:]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--capture-seconds",type=float,default=.7)
    ap.add_argument("--max-slots-per-cycle",type=int,default=2);ap.add_argument("--cycles",type=int,default=0)
    a=ap.parse_args();root=Path(a.root).resolve();blocks=Blocks()
    path=root/"runtime_state/qseries/qsb033_mriya_exact_route_anatomy/routes.json"
    state=read_json(path,{"routes":[]});seen={x["signature"] for x in state["routes"]}
    print("[QSB-033] MRIYA EXACT ROUTE ANATOMY",flush=True)
    print("[TARGET] exact Mriya signatures from full getBlock transactions",flush=True)
    print("[OUTPUT] success/failure + venue sequence + wallet deltas + fee/compute + evidence-grounded legs",flush=True)
    print("[RULE] unresolved DEX leg stays unresolved; no invented input/output",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    c=0
    while True:
        c+=1
        try:ret=asyncio.run(capture(a.capture_seconds,1800)) or {}
        except Exception as e:
            print("[CAPTURE_ERROR]",type(e).__name__,str(e),flush=True);time.sleep(1);continue
        ss=[x for x in slots(list(ret.get("rows") or [])) if x not in blocks.seen][:max(1,a.max_slots_per_cycle)]
        found=0
        for slot in ss:
            b,limited=blocks.fetch(slot)
            if limited:
                print("[RPC429] slot=%d retryable=True"%slot,flush=True);break
            if not isinstance(b,dict):continue
            blocks.seen.add(slot);bt=b.get("blockTime")
            for tx in b.get("transactions") or []:
                arow=analyze_target(tx,slot,bt)
                if not arow or not arow["executor_present"]:continue
                sig=arow["signature"]
                if not sig or sig in seen:continue
                seen.add(sig);state["routes"].append(arow);state["routes"]=state["routes"][-5000:];found+=1
                if arow["failed"]:
                    print("[MRIYA_FAIL] sig=%s slot=%d venues=%s fee=%s cu=%s error=%s"%(
                        sig,slot,arow["venues"],arow["fee_lamports"],arow["compute_units"],arow["error"]),flush=True)
                else:
                    print("[MRIYA_ROUTE] sig=%s slot=%d venues=%s closed=%s legs=%d resolved=%d anchor_delta=%s nonanchor=%s"%(
                        sig,slot,arow["venues"],arow["closed_anchor_cycle"],arow["leg_count"],arow["resolved_legs"],
                        arow["wallet_anchor_deltas"],arow["wallet_nonanchor_deltas"]),flush=True)
                    for i,leg in enumerate(arow["legs"],1):
                        if leg.get("resolved"):
                            print("[LEG %d] %s %g %s -> %g %s rate=%g"%(
                                i,leg["venue"],leg["input_amount"],short_mint(leg["input_asset"]),
                                leg["output_amount"],short_mint(leg["output_asset"]),leg["effective_output_per_input"]),flush=True)
                        else:
                            print("[LEG %d] %s UNRESOLVED transfers=%d reason=%s"%(
                                i,leg["venue"],len(leg["transfers"]),leg["resolution_reason"]),flush=True)
        write_json(path,state)
        print("[CYCLE] n=%d slots=%d new_target_routes=%d total_routes=%d rpc429=%d errors=%d"%(
            c,len(ss),found,len(state["routes"]),blocks.rate_limits,blocks.errors),flush=True)
        if a.cycles and c>=a.cycles:return
if __name__=="__main__":main()
