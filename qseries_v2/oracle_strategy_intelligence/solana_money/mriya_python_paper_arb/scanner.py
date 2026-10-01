from __future__ import annotations
import json,time
from pathlib import Path
from . import core

MAX_POOLS=12
SIZES_SOL=(0.05,0.10,0.25,0.50,0.75,1.00,1.50)
MIN_NET_BPS=15.0
FRESH_SLOT_SPREAD=4

def _rows(j):
    if isinstance(j,list): return j
    if isinstance(j,dict):
        for k in ("data","pools","items","results"):
            if isinstance(j.get(k),list): return j[k]
    return []

def _mint(o):
    if isinstance(o,str): return o
    if isinstance(o,dict):
        for k in ("address","mint","token_address"):
            if isinstance(o.get(k),str): return o[k]
    return ""

def _dec(o):
    if isinstance(o,dict):
        for k in ("decimals","decimal"):
            try:return int(o[k])
            except Exception:pass
    return None

def _num(x):
    try:return float(x)
    except Exception:return 0.0

def discover_wsol_dlmm_candidates(http=core.http_json,max_pools=MAX_POOLS):
    seen={}
    for page in (1,2,3):
        try:j=http(f"{core.METEORA_API}/pools?page={page}&page_size=100")
        except Exception:
            if page==1: raise
            break
        for x in _rows(j):
            tx=x.get("token_x") or x.get("tokenX") or {}
            ty=x.get("token_y") or x.get("tokenY") or {}
            mx,my=_mint(tx),_mint(ty)
            if core.WSOL not in (mx,my): continue
            token=my if mx==core.WSOL else mx
            if not token or token==core.WSOL: continue
            addr=x.get("address") or x.get("pool_address") or x.get("pubkey")
            if not addr: continue
            dx,dy=_dec(tx),_dec(ty)
            if dx is None or dy is None: continue
            score=max(_num(x.get("tvl")), _num(x.get("liquidity")), _num(x.get("liquidity_usd")))
            row={"address":str(addr),"token_x":mx,"token_y":my,"decimals_x":dx,"decimals_y":dy,
                 "token":token,"score":score}
            old=seen.get((str(addr),token))
            if old is None or row["score"]>old["score"]: seen[(str(addr),token)]=row
    rows=sorted(seen.values(),key=lambda r:r["score"],reverse=True)
    return rows[:int(max_pools)]

def pool_state(rpc_url,meta):
    from meteora_dlmm import PoolState
    lb=core.fetch_account_bytes(rpc_url,meta["address"])
    bins=core.fetch_bin_arrays(rpc_url,meta["address"])
    return PoolState.from_accounts(lb,bins,decimals_x=int(meta["decimals_x"]),
                                   decimals_y=int(meta["decimals_y"]),exhaustive=True)

def meteora_from_state(state,meta,input_mint,input_ui):
    from meteora_dlmm import quote
    if input_mint==meta["token_x"]:
        swap_for_y=True; indec=int(meta["decimals_x"]); outdec=int(meta["decimals_y"]); outmint=meta["token_y"]
    elif input_mint==meta["token_y"]:
        swap_for_y=False; indec=int(meta["decimals_y"]); outdec=int(meta["decimals_x"]); outmint=meta["token_x"]
    else: raise RuntimeError("INPUT_MINT_NOT_IN_POOL")
    raw=int(round(float(input_ui)*(10**indec)))
    q=quote(state,amount_in=raw,swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0)!=0:
        raise RuntimeError("METEORA_PARTIAL_QUOTE")
    rout=int(q.amount_out)
    return {"raw_in":raw,"raw_out":rout,"out_ui":rout/(10**outdec),
            "out_mint":outmint,"out_decimals":outdec}

def pump_any(input_mint,output_mint,raw_in,http=core.http_json):
    body={"inputMint":input_mint,"outputMint":output_mint,"amount":str(int(raw_in)),
          "user":core.WALLET,"slippagePct":0,"frontRunningProtection":False,
          "tipAmount":0,"encoding":"base64"}
    j=http(core.PUMP_SWAP_API,"POST",body,20)
    info=j.get("pumpMintInfo") if isinstance(j,dict) else None
    if not isinstance(info,dict): raise RuntimeError("PUMP_NO_MINT_INFO")
    out=info.get("expectedOutAmount")
    if out is None: raise RuntimeError("PUMP_NO_EXPECTED_OUT")
    raw=int(out)
    if raw<=0: raise RuntimeError("PUMP_NONPOSITIVE_OUT")
    return {"raw_in":int(raw_in),"raw_out":raw,"info":info}

def evaluate(start_sol,final_sol,slot0,slot1,tx_cost_sol=0.0001):
    net=float(final_sol)-float(start_sol)-float(tx_cost_sol)
    bps=net/float(start_sol)*10000.0
    fresh=abs(int(slot1)-int(slot0))<=FRESH_SLOT_SPREAD
    return {"start_sol":float(start_sol),"end_sol":float(final_sol),"tx_cost_sol":float(tx_cost_sol),
            "net_sol":net,"net_bps":bps,"fresh":fresh,
            "paper_trade":bool(fresh and bps>=MIN_NET_BPS)}

def direction_a(rpc_url,state,meta,size,http=core.http_json,rpc_fn=core.rpc):
    slot0=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    mq=meteora_from_state(state,meta,core.WSOL,size)
    if mq["out_mint"]!=meta["token"]: raise RuntimeError("METEORA_A_WRONG_OUTPUT")
    pq=pump_any(meta["token"],core.WSOL,mq["raw_out"],http)
    final_sol=pq["raw_out"]/1e9
    slot1=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    x=evaluate(size,final_sol,slot0,slot1)
    x.update({"direction":"METEORA_TO_PUMP","token":meta["token"],"pool":meta["address"],
              "intermediate_raw":mq["raw_out"]})
    return x

def direction_b(rpc_url,state,meta,size,http=core.http_json,rpc_fn=core.rpc):
    slot0=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    raw_sol=int(round(float(size)*1e9))
    pq=pump_any(core.WSOL,meta["token"],raw_sol,http)
    tokdec=int(meta["decimals_y"] if meta["token_y"]==meta["token"] else meta["decimals_x"])
    token_ui=pq["raw_out"]/(10**tokdec)
    mq=meteora_from_state(state,meta,meta["token"],token_ui)
    if mq["out_mint"]!=core.WSOL: raise RuntimeError("METEORA_B_WRONG_OUTPUT")
    final_sol=mq["raw_out"]/1e9
    slot1=rpc_fn(rpc_url,"getSlot",[{"commitment":"processed"}])
    x=evaluate(size,final_sol,slot0,slot1)
    x.update({"direction":"PUMP_TO_METEORA","token":meta["token"],"pool":meta["address"],
              "intermediate_raw":pq["raw_out"]})
    return x

def scan(root,http=core.http_json,rpc_fn=core.rpc,max_pools=MAX_POOLS):
    rpc_url=core.os.getenv("SOLANA_RPC_URL",core.DEFAULT_RPC)
    candidates=discover_wsol_dlmm_candidates(http,max_pools)
    results=[]; errors=[]
    for idx,meta in enumerate(candidates,1):
        print(f"[POOL {idx}/{len(candidates)}] {meta['address']} token={meta['token']} score={meta['score']}",flush=True)
        try: state=pool_state(rpc_url,meta)
        except Exception as e:
            errors.append({"pool":meta["address"],"stage":"METEORA_STATE","error":f"{type(e).__name__}: {e}"})
            print(f"[SKIP] pool={meta['address']} state_error={type(e).__name__}: {e}",flush=True);continue
        # quick compatibility probe; if Pump cannot quote the token, skip it.
        try: pump_any(meta["token"],core.WSOL,10**int(meta["decimals_y"] if meta["token_y"]==meta["token"] else meta["decimals_x"]),http)
        except Exception as e:
            print(f"[SKIP] token={meta['token']} no_pumpswap_quote={type(e).__name__}: {e}",flush=True);continue
        for size in SIZES_SOL:
            for fn in (direction_a,direction_b):
                try:
                    x=fn(rpc_url,state,meta,size,http,rpc_fn);results.append(x)
                    tag="EDGE" if x["paper_trade"] else "NO_EDGE"
                    print("[%s] dir=%s token=%s size=%.6f end=%.9f net=%+.9f bps=%+.2f fresh=%s"%(
                      tag,x["direction"],x["token"],size,x["end_sol"],x["net_sol"],x["net_bps"],x["fresh"]),flush=True)
                except Exception as e:
                    errors.append({"pool":meta["address"],"token":meta["token"],"size":size,
                                   "direction":fn.__name__,"error":f"{type(e).__name__}: {e}"})
        time.sleep(.10)
    results.sort(key=lambda x:x["net_bps"],reverse=True)
    best=results[0] if results else None
    admitted=[x for x in results if x["paper_trade"]]
    out={"revision":"QSB_038C","candidate_pools":len(candidates),"quotes":len(results),
         "paper_opportunities":len(admitted),"best":best,"opportunities":admitted,
         "errors":errors,"execution_authority":False}
    p=Path(root)/"runtime_state/qseries/qsb038c_live_market_deficiency/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
