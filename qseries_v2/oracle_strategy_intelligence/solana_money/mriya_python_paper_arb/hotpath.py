from __future__ import annotations
import json,math,os,statistics,time
from pathlib import Path
from . import core
from . import scanner as prior
from . import crosslisted as cross

COARSE=(0.02,0.03,0.05,0.08,0.12,0.20,0.35,0.50,0.75,1.00)
MIN_NET_BPS=15.0
MAX_SLOT_SPREAD=2
DEFAULT_CU_LIMIT=220_000
BASE_FEE_LAMPORTS=5_000

def percentile(vals,p=.75):
    xs=sorted(int(x) for x in vals if x is not None)
    if not xs:return 0
    i=max(0,min(len(xs)-1,int(math.ceil(p*len(xs))-1)))
    return xs[i]

def recent_priority_fee(rpc_url,pump_pool,meteora_pool,rpc_fn=core.rpc):
    rows=rpc_fn(rpc_url,"getRecentPrioritizationFees",[[pump_pool,meteora_pool]]) or []
    vals=[int(x.get("prioritizationFee") or 0) for x in rows if isinstance(x,dict)]
    return {"samples":len(vals),"micro_lamports_per_cu_p75":percentile(vals,.75)}

def observed_route_cu(root):
    p=Path(root)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json"
    try:d=json.loads(p.read_text(encoding="utf-8"))
    except Exception:return DEFAULT_CU_LIMIT
    vals=[]
    for r in d.get("records") or []:
        chain=tuple(r.get("venue_chain") or ())
        if "METEORA_DLMM" in chain and "PUMP_SWAP" in chain and not r.get("failed"):
            for k in ("compute_units","computeUnits","cu","units_consumed"):
                try:
                    v=int(r.get(k) or 0)
                    if v>0:vals.append(v);break
                except Exception:pass
    if not vals:return DEFAULT_CU_LIMIT
    return max(50_000,min(1_400_000,int(statistics.median(vals)*1.10)))

def fee_model(root,rpc_url,pair,rpc_fn=core.rpc):
    pf=recent_priority_fee(rpc_url,pair["pump_pool"],pair["meteora"]["address"],rpc_fn)
    cu=observed_route_cu(root)
    micro=int(pf["micro_lamports_per_cu_p75"])
    priority_lamports=math.ceil(micro*cu/1_000_000)
    total=BASE_FEE_LAMPORTS+priority_lamports
    return {"base_fee_lamports":BASE_FEE_LAMPORTS,"cu_limit_estimate":cu,
            "priority_micro_lamports_per_cu":micro,
            "priority_fee_lamports":priority_lamports,
            "estimated_total_fee_lamports":total,
            "estimated_total_fee_sol":total/1e9,
            "priority_samples":pf["samples"],
            "truth":"PRE_SIMULATION_ESTIMATE"}

def recompute(row,fee):
    if not row or "end_sol" not in row:return row
    start=float(row["start_sol"]);end=float(row["end_sol"])
    cost=float(fee["estimated_total_fee_sol"])
    net=end-start-cost
    bps=(net/start*10000.0) if start else -1e18
    row=dict(row)
    row.update({"estimated_fee_sol":cost,"fee_model":fee,"net_sol":net,"net_bps":bps,
                "fresh":abs(int(row["slot_end"])-int(row["slot_start"]))<=MAX_SLOT_SPREAD})
    row["pre_sim_candidate"]=bool(row["fresh"] and bps>=MIN_NET_BPS)
    row["paper_trade"]=row["pre_sim_candidate"]
    return row

def quote(root,pair,state,size,fee,http=core.http_json,rpc_fn=core.rpc):
    rpc_url=os.getenv("SOLANA_RPC_URL",core.DEFAULT_RPC)
    out=[]
    for fn in (prior.direction_a,prior.direction_b):
        try:
            r=fn(rpc_url,state,pair["meteora"],float(size),http,rpc_fn)
            r["pump_pool"]=pair["pump_pool"];r["pump_activity"]=pair["pump_activity"]
            out.append(recompute(r,fee))
        except Exception as e:
            out.append({"direction":fn.__name__,"token":pair["token"],"start_sol":float(size),
                        "error":f"{type(e).__name__}: {e}","pre_sim_candidate":False})
    return out

def adaptive_sizes(best_size):
    b=float(best_size)
    raw=[b*.55,b*.70,b*.82,b*.90,b*.96,b,b*1.04,b*1.10,b*1.18,b*1.30,b*1.45]
    return sorted({round(max(.005,min(2.0,x)),6) for x in raw})

def optimize(root,pair,http=core.http_json,rpc_fn=core.rpc):
    rpc_url=os.getenv("SOLANA_RPC_URL",core.DEFAULT_RPC)
    state=prior.pool_state(rpc_url,pair["meteora"])
    fee=fee_model(root,rpc_url,pair,rpc_fn)
    rows=[]
    for s in COARSE:rows.extend(quote(root,pair,state,s,fee,http,rpc_fn))
    valid=[x for x in rows if "net_bps" in x]
    if not valid:return None,rows,fee
    coarse_best=max(valid,key=lambda z:z["net_sol"])
    for s in adaptive_sizes(coarse_best["start_sol"]):
        if all(abs(float(x.get("start_sol",-99))-s)>1e-12 for x in rows):
            rows.extend(quote(root,pair,state,s,fee,http,rpc_fn))
    valid=[x for x in rows if "net_bps" in x]
    best=max(valid,key=lambda z:z["net_sol"]) if valid else None
    return best,rows,fee

def load_hot(root,max_age=90):
    p=Path(root)/"runtime_state/qseries/qsb038f_hotpath/crosslist_cache.json"
    try:d=json.loads(p.read_text(encoding="utf-8"))
    except Exception:return []
    if time.time()-float(d.get("saved_unix") or 0)>max_age:return []
    return list(d.get("pairs") or [])

def save_hot(root,pairs):
    p=Path(root)/"runtime_state/qseries/qsb038f_hotpath/crosslist_cache.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({"saved_unix":time.time(),"pairs":pairs},indent=2),encoding="utf-8")

def run_cycle(root,http=core.http_json,rpc_fn=core.rpc):
    pairs=load_hot(root)
    source="HOT_CACHE"
    if not pairs:
        _,pairs=cross.crosslisted(root,http,capture_seconds=5,max_intersections=8)
        save_hot(root,pairs);source="LIVE_INTERSECTION"
    print(f"[CANDIDATES] source={source} crosslisted={len(pairs)}",flush=True)
    all_rows=[];best=None
    for i,pair in enumerate(pairs,1):
        print("[HOTPAIR %d/%d] token=%s pump=%s meteora=%s"%(
          i,len(pairs),pair["token"],pair["pump_pool"],pair["meteora"]["address"]),flush=True)
        try:b,rows,fee=optimize(root,pair,http,rpc_fn)
        except Exception as e:
            print("[HOTPAIR_ERROR] %s: %s"%(type(e).__name__,e),flush=True);continue
        all_rows.extend(rows)
        print("[FEE_EST] cu=%d price=%dµlamports/CU base=%d priority=%d total_sol=%.9f samples=%d"%(
          fee["cu_limit_estimate"],fee["priority_micro_lamports_per_cu"],
          fee["base_fee_lamports"],fee["priority_fee_lamports"],
          fee["estimated_total_fee_sol"],fee["priority_samples"]),flush=True)
        if b:
            print("[HOT_BEST] dir=%s size=%.6f end=%.9f net=%+.9f bps=%+.2f spread=%d PRE_SIM_CANDIDATE=%s"%(
              b["direction"],b["start_sol"],b["end_sol"],b["net_sol"],b["net_bps"],
              abs(int(b["slot_end"])-int(b["slot_start"])),
              "YES" if b["pre_sim_candidate"] else "NO"),flush=True)
            if best is None or b["net_sol"]>best["net_sol"]:best=b
    out={"revision":"QSB_038F","candidate_source":source,"pairs":pairs,"quotes":all_rows,
         "best":best,"execution_authority":False,
         "truth":"FEE_AWARE_PRE_SIMULATION_ONLY"}
    p=Path(root)/"runtime_state/qseries/qsb038f_hotpath/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
