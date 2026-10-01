from __future__ import annotations
import json,os,time
from pathlib import Path
from . import core
from . import scanner as prior
from . import crosslisted as cross
from . import hotpath as hot

COIN_API="https://frontend-api-v3.pump.fun/coins-v2"
MIN_NET_BPS=15.0
MAX_TOTAL_SLOT_SPREAD=2

def coin_state(token,http=core.http_json):
    j=http(f"{COIN_API}/{token}")
    if not isinstance(j,dict):
        raise RuntimeError("PUMP_COIN_STATE_NOT_OBJECT")
    return j

def verify_exact_pump_pool(pair,http=core.http_json):
    token=pair["token"];expected=str(pair["pump_pool"])
    c=coin_state(token,http)
    actual=str(c.get("pump_swap_pool") or "")
    if not bool(c.get("complete")):
        raise RuntimeError("PUMP_TOKEN_NOT_GRADUATED")
    if not actual:
        raise RuntimeError("PUMP_CANONICAL_POOL_MISSING")
    if actual!=expected:
        raise RuntimeError(f"PUMP_POOL_MISMATCH discovered={expected} canonical={actual}")
    return {"token":token,"discovered_pool":expected,"canonical_pool":actual,
            "complete":True,"verified":True}

def exact_api_quote(pair,input_mint,output_mint,raw_in,http=core.http_json):
    binding=verify_exact_pump_pool(pair,http)
    body={"inputMint":input_mint,"outputMint":output_mint,"amount":str(int(raw_in)),
          "user":core.WALLET,"feePayer":core.WALLET,"slippagePct":0,
          "frontRunningProtection":False,"tipAmount":0,"encoding":"base64"}
    j=http(core.PUMP_SWAP_API,"POST",body,20)
    if not isinstance(j,dict):
        raise RuntimeError("PUMP_SWAP_RESPONSE_NOT_OBJECT")
    info=j.get("pumpMintInfo")
    if not isinstance(info,dict):
        raise RuntimeError("PUMP_SWAP_NO_MINT_INFO")
    out=info.get("expectedOutAmount")
    if out is None:
        raise RuntimeError("PUMP_SWAP_NO_EXPECTED_OUT")
    raw=int(out)
    if raw<=0:
        raise RuntimeError("PUMP_SWAP_NONPOSITIVE_OUT")
    tx=j.get("transaction")
    return {"raw_in":int(raw_in),"raw_out":raw,"binding":binding,
            "transaction_present":bool(tx),
            "transaction_b64":tx if isinstance(tx,str) else None,
            "pump_mint_info":info}

def _state_window(rpc_url,meta,rpc_fn=core.rpc):
    slot_before=int(rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}]))
    state=prior.pool_state(rpc_url,meta)
    slot_after=int(rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}]))
    return state,slot_before,slot_after

def _dir_meteora_to_pump(rpc_url,state,pair,size,http=core.http_json,rpc_fn=core.rpc):
    meta=pair["meteora"]
    mq=prior.meteora_from_state(state,meta,core.WSOL,float(size))
    if mq["out_mint"]!=pair["token"]:
        raise RuntimeError("METEORA_A_WRONG_OUTPUT")
    if mq.get("partial"):
        raise RuntimeError("METEORA_PARTIAL_QUOTE")
    pq=exact_api_quote(pair,pair["token"],core.WSOL,mq["raw_out"],http)
    slot_end=int(rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}]))
    return {"direction":"METEORA_TO_PUMP","token":pair["token"],"pool":meta["address"],
            "pump_pool":pair["pump_pool"],"start_sol":float(size),
            "end_sol":pq["raw_out"]/1e9,"slot_end":slot_end,
            "pump_binding":pq["binding"],"pump_transaction_present":pq["transaction_present"]}

def _dir_pump_to_meteora(rpc_url,state,pair,size,http=core.http_json,rpc_fn=core.rpc):
    meta=pair["meteora"]
    raw_sol=int(round(float(size)*1e9))
    pq=exact_api_quote(pair,core.WSOL,pair["token"],raw_sol,http)
    tokdec=int(meta["decimals_y"] if meta["token_y"]==pair["token"] else meta["decimals_x"])
    token_ui=pq["raw_out"]/(10**tokdec)
    mq=prior.meteora_from_state(state,meta,pair["token"],token_ui)
    if mq["out_mint"]!=core.WSOL:
        raise RuntimeError("METEORA_B_WRONG_OUTPUT")
    if mq.get("partial"):
        raise RuntimeError("METEORA_PARTIAL_QUOTE")
    slot_end=int(rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}]))
    return {"direction":"PUMP_TO_METEORA","token":pair["token"],"pool":meta["address"],
            "pump_pool":pair["pump_pool"],"start_sol":float(size),
            "end_sol":mq["raw_out"]/1e9,"slot_end":slot_end,
            "pump_binding":pq["binding"],"pump_transaction_present":pq["transaction_present"]}

def _finalize(row,fee,slot_before,slot_after):
    start=float(row["start_sol"]);end=float(row["end_sol"])
    cost=float(fee["estimated_total_fee_sol"])
    net=end-start-cost
    bps=net/start*10000.0 if start else -1e18
    total_spread=max(0,int(row["slot_end"])-int(slot_before))
    x=dict(row)
    x.update({"estimated_fee_sol":cost,"net_sol":net,"net_bps":bps,
              "state_slot_before":int(slot_before),"state_slot_after":int(slot_after),
              "slot_spread":total_spread,
              "fresh":total_spread<=MAX_TOTAL_SLOT_SPREAD,
              "pre_sim_candidate":bool(total_spread<=MAX_TOTAL_SLOT_SPREAD and bps>=MIN_NET_BPS)})
    return x

def _quote_once(root,pair,size,direction,http=core.http_json,rpc_fn=core.rpc):
    rpc_url=os.getenv("SOLANA_RPC_URL",core.DEFAULT_RPC)
    state,s0,s1=_state_window(rpc_url,pair["meteora"],rpc_fn)
    fee=hot.fee_model(root,rpc_url,pair,rpc_fn)
    fn=_dir_pump_to_meteora if direction=="PUMP_TO_METEORA" else _dir_meteora_to_pump
    row=fn(rpc_url,state,pair,float(size),http,rpc_fn)
    return _finalize(row,fee,s0,s1),fee

def _coarse_sizes():
    return (.005,.0075,.01,.014,.02,.03,.05,.08,.12,.20,.35,.50,.75,1.0,1.4)

def optimize_pair(root,pair,http=core.http_json,rpc_fn=core.rpc):
    binding=verify_exact_pump_pool(pair,http)
    raw_rows=[];errors=[]
    # Coarse discovery only. Every quote gets its own fresh state window.
    for size in _coarse_sizes():
        for direction in ("PUMP_TO_METEORA","METEORA_TO_PUMP"):
            try:
                r,_=_quote_once(root,pair,size,direction,http,rpc_fn)
                raw_rows.append(r)
            except Exception as e:
                errors.append({"size":size,"direction":direction,
                               "error":f"{type(e).__name__}: {e}"})
    valid=[x for x in raw_rows if "net_sol" in x]
    if not valid:
        return None,raw_rows,errors,None,binding
    raw_best=max(valid,key=lambda z:z["net_sol"])
    # Mandatory revalidation: throw away prior state/quote and recompute exact winner fresh.
    try:
        best,fee=_quote_once(root,pair,raw_best["start_sol"],raw_best["direction"],http,rpc_fn)
        best["revalidated"]=True
        best["raw_net_sol"]=raw_best["net_sol"]
        best["raw_net_bps"]=raw_best["net_bps"]
    except Exception as e:
        errors.append({"size":raw_best.get("start_sol"),"direction":raw_best.get("direction"),
                       "error":f"REVALIDATION_{type(e).__name__}: {e}"})
        best=dict(raw_best)
        best["pre_sim_candidate"]=False
        best["revalidated"]=False
        best["revalidation_error"]=f"{type(e).__name__}: {e}"
        fee=None
    return best,raw_rows,errors,fee,binding

def run(root,http=core.http_json,rpc_fn=core.rpc):
    _,pairs=cross.crosslisted(root,http,capture_seconds=5,max_intersections=8)
    print("[CROSSLIST] exact_pairs=%d"%len(pairs),flush=True)
    allrows=[];allerr=[];best=None
    for i,pair in enumerate(pairs,1):
        print("[PAIR %d/%d] token=%s pump=%s meteora=%s"%(
          i,len(pairs),pair["token"],pair["pump_pool"],pair["meteora"]["address"]),flush=True)
        try:b,rows,errs,fee,binding=optimize_pair(root,pair,http,rpc_fn)
        except Exception as e:
            print("[PAIR_REJECT] %s: %s"%(type(e).__name__,e),flush=True);continue
        print("[PUMP_BINDING] discovered=%s canonical=%s verified=%s"%(
          binding["discovered_pool"],binding["canonical_pool"],binding["verified"]),flush=True)
        allrows.extend(rows);allerr.extend(errs)
        if errs:
            counts={}
            for e in errs:counts[e["error"]]=counts.get(e["error"],0)+1
            for msg,n in sorted(counts.items(),key=lambda z:-z[1])[:5]:
                print("[QUOTE_ERROR] count=%d %s"%(n,msg),flush=True)
        if b:
            if b.get("raw_net_bps") is not None:
                print("[REVALIDATED] raw_bps=%+.2f fresh_bps=%+.2f total_slot_spread=%d survived=%s"%(
                  b["raw_net_bps"],b["net_bps"],b["slot_spread"],
                  "YES" if b["pre_sim_candidate"] else "NO"),flush=True)
            print("[PAIR_BEST] dir=%s size=%.6f end=%.9f fee=%.9f net=%+.9f bps=%+.2f spread=%d tx_present=%s PRE_SIM_CANDIDATE=%s"%(
              b["direction"],b["start_sol"],b["end_sol"],b["estimated_fee_sol"],
              b["net_sol"],b["net_bps"],b["slot_spread"],b["pump_transaction_present"],
              "YES" if b["pre_sim_candidate"] else "NO"),flush=True)
            if best is None or b["net_sol"]>best["net_sol"]:
                best=b
    out={"revision":"QSB_038K","pairs":pairs,"quotes":allrows,"errors":allerr,"best":best,
         "execution_authority":False,
         "truth":"SAME_WINDOW_EXACT_POOL_PRE_SIM"}
    p=Path(root)/"runtime_state/qseries/qsb038k_same_window/report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
