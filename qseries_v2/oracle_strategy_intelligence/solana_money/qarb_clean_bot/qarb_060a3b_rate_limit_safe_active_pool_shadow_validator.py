from __future__ import annotations
import argparse,base64,json,time,urllib.error
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056b_clmm_tick_fee_state as q56b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056c_orca_tick_fee_state as q56c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_057a2_clmm_directional_tick_array_resolver as q57a
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_057b_orca_tick_array_pda_resolver as q57b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058a_clmm_local_swap_math as q58a
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058b_orca_local_swap_math as q58b

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_ERROR_BPS=10.0
CLMM_PROGRAM="CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
ORCA_PROGRAM="whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060a3b_rate_limit_safe_active_pool_shadow_validator.json")

def rpc(method,params,tries=5):
    last=None
    for i in range(tries):
        try:return c.rpc(method,params)
        except urllib.error.HTTPError as e:
            last=e
            if e.code!=429:raise
            time.sleep(min(8.0,1.0*(2**i)))
        except Exception as e:
            last=e
            if "429" not in str(e):raise
            time.sleep(min(8.0,1.0*(2**i)))
    raise last

def _raw(v):
    if not v:return None
    d=v.get("data")
    if isinstance(d,list) and d:return base64.b64decode(d[0])
    if isinstance(d,str):return base64.b64decode(d)
    return None

def batch_accounts(addrs,batch=40):
    out={};slot=0
    for i in range(0,len(addrs),batch):
        chunk=addrs[i:i+batch]
        r=rpc("getMultipleAccounts",[chunk,{"encoding":"base64","commitment":"confirmed"}]) or {}
        slot=max(slot,int(((r.get("context") or {}).get("slot") or 0)))
        for a,v in zip(chunk,r.get("value") or []):out[a]=_raw(v)
        time.sleep(.18)
    return slot,out

def sigs(addr,limit=8):
    return rpc("getSignaturesForAddress",[addr,{"limit":int(limit),"commitment":"confirmed"}]) or []

def tx(sig):
    return rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def keys(t):
    ks=(((t or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
    return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def vault_deltas(t,v0,v1):
    meta=(t or {}).get("meta") or {};ks=keys(t)
    pre={int(x["accountIndex"]):int(((x.get("uiTokenAmount") or {}).get("amount") or 0)) for x in meta.get("preTokenBalances") or []}
    post={int(x["accountIndex"]):int(((x.get("uiTokenAmount") or {}).get("amount") or 0)) for x in meta.get("postTokenBalances") or []}
    try:i0=ks.index(v0);i1=ks.index(v1)
    except ValueError:return None
    if i0 not in pre or i1 not in pre or i0 not in post or i1 not in post:return None
    return post[i0]-pre[i0],post[i1]-pre[i1]

def discover_pool_ids(family,program,signature_limit=8,max_pools=6):
    txs=[];all_keys=[]
    for s in sigs(program,signature_limit):
        try:
            t=tx(s["signature"]);txs.append(t)
            all_keys += [a for a in keys(t) if isinstance(a,str) and a!=program]
        except Exception:pass
        time.sleep(.15)
    uniq=list(dict.fromkeys(all_keys))[:240]
    _,raws=batch_accounts(uniq)
    pools=[]
    for a in uniq:
        raw=raws.get(a)
        if not raw:continue
        try:
            st=q56b.decode_pool(raw) if family=="RAYDIUM_CLMM" else q56c.decode_pool(raw)
            if family=="RAYDIUM_CLMM":
                ok=bool(st.get("token_mint_0") and st.get("token_mint_1") and st.get("amm_config"))
            else:
                ok=bool(st.get("token_mint_a") and st.get("token_mint_b") and st.get("token_vault_a") and st.get("token_vault_b"))
            if ok:pools.append(a)
        except Exception:pass
        if len(pools)>=max_pools:break
    return pools,{"transactions":len(txs),"account_keys":len(uniq),"decoded_pools":len(pools)}

def hydrate_pool(family,pool):
    raw,_=batch_accounts([pool])
    pr=raw.get(pool)
    if family=="RAYDIUM_CLMM":
        st=q56b.decode_pool(pr)
        _,cfgraw=batch_accounts([st["amm_config"]]);cfg=q56b.decode_config(cfgraw[st["amm_config"]])
        spacing=int(st["tick_spacing"]);tick=int(st["tick_current"]);base=q57a.array_start(tick,spacing);w=60*spacing
        arr=[]
        for s in [base,base-w,base-2*w,base-3*w,base+w,base+2*w,base+3*w]:
            a,_=q57a.tick_array_pda(pool,s);arr.append(a)
        _,rr=batch_accounts(arr);arr=[a for a in arr if rr.get(a)]
        if not arr:raise RuntimeError("NO_CLMM_ARRAYS")
        return {"family":family,"pool":pool,"vault_a":st["token_vault_0"],"vault_b":st["token_vault_1"],
                "addresses":[pool,st["amm_config"]]+arr}
    st=q56c.decode_pool(pr);seq=q57b.resolve(pool,int(st["tick_current"]),int(st["tick_spacing"]))
    arr=list(dict.fromkeys(x["address"] for xs in seq.values() for x in xs if x.get("exists")))
    if not arr:raise RuntimeError("NO_ORCA_ARRAYS")
    return {"family":family,"pool":pool,"vault_a":st["token_vault_a"],"vault_b":st["token_vault_b"],
            "addresses":[pool]+arr}

def local_quote(p,snap,amount,zero):
    if p["family"]=="RAYDIUM_CLMM":
        st=q56b.decode_pool(snap[p["pool"]]);cfg=q56b.decode_config(snap[st["amm_config"]]);ticks={}
        for a in p["addresses"]:
            if a in (p["pool"],st["amm_config"]):continue
            rr=snap.get(a)
            if rr:
                for x in q58a.decode_ticks(rr):ticks[x["tick"]]=x
        if not ticks:raise RuntimeError("NO_CLMM_TICKS")
        return q58a.quote_steps(st["sqrt_price_x64"],st["liquidity"],cfg["trade_fee_rate"],amount,list(ticks.values()),zero)["amount_out"]
    st=q56c.decode_pool(snap[p["pool"]]);ticks={}
    for a in p["addresses"]:
        if a==p["pool"]:continue
        rr=snap.get(a)
        if rr and rr[:8]==q58b.tick_disc():
            start=int.from_bytes(rr[8:12],"little",signed=True)
            for x in q58b.decode_fixed(rr,start,st["tick_spacing"]):ticks[x["tick"]]=x
    if not ticks:raise RuntimeError("NO_ORCA_TICKS")
    return q58b.quote_steps(st["sqrt_price_x64"],st["liquidity"],st["fee_rate"],amount,list(ticks.values()),zero)["amount_out"]

def validate_one(p,pre,t):
    ds=vault_deltas(t,p["vault_a"],p["vault_b"])
    if not ds:return None
    d0,d1=ds
    if d0>0 and d1<0:zero=True;ain=d0;actual=-d1
    elif d1>0 and d0<0:zero=False;ain=d1;actual=-d0
    else:return None
    if ain<=0 or actual<=0:return None
    quoted=int(local_quote(p,pre,ain,zero));err=abs(quoted-actual)/actual*10000.0
    return {"family":p["family"],"pool":p["pool"],"amount_in":ain,"actual_out":actual,"local_out":quoted,
            "error_bps":err,"pass":err<=MAX_ERROR_BPS,"direction":"A_TO_B" if zero else "B_TO_A"}

def run(root,seconds=60.0,poll=3.0,signature_limit=8,max_pools=6):
    root=Path(root)
    cl_ids,cm=discover_pool_ids("RAYDIUM_CLMM",CLMM_PROGRAM,signature_limit,max_pools)
    time.sleep(1.0)
    oc_ids,om=discover_pool_ids("ORCA_WHIRLPOOL",ORCA_PROGRAM,signature_limit,max_pools)
    pools=[];warm_errors=[]
    for fam,ids in (("RAYDIUM_CLMM",cl_ids),("ORCA_WHIRLPOOL",oc_ids)):
        for pid in ids:
            try:pools.append(hydrate_pool(fam,pid))
            except Exception as e:warm_errors.append(fam+":"+pid[:12]+":"+type(e).__name__+":"+str(e))
            time.sleep(.25)
    addrs=list(dict.fromkeys(a for p in pools for a in p["addresses"]))
    slot,prev=batch_accounts(addrs)
    seen={p["pool"]:{x["signature"] for x in sigs(p["pool"],4)} for p in pools}
    rows=[];errors=[];amb=0;start=time.monotonic()
    print("[QARB-060A3B] RATE-LIMIT-SAFE ACTIVE-POOL SHADOW VALIDATOR",flush=True)
    print("[DISCOVER] clmm_decoded=%d orca_decoded=%d warmed=%d accounts=%d"%(len(cl_ids),len(oc_ids),len(pools),len(addrs)),flush=True)
    print("[SCAN] clmm=%s orca=%s"%(json.dumps(cm,sort_keys=True),json.dumps(om,sort_keys=True)),flush=True)
    print("[RPC] batched getMultipleAccounts + exponential 429 backoff",flush=True)
    if not pools:
        payload={"revision":"QARB_060A3B","shadow_validation_pass":False,"next":"HOLD_ACTIVE_POOL_DISCOVERY_EMPTY",
                 "warm_errors":warm_errors,"execution_authority":False,"paper_only":True}
        op=root/OUT;op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(payload,indent=2),encoding="utf-8")
        print("[HOLD] no hydrated active pools",flush=True);print("[REPORT]",OUT,flush=True);return payload
    while time.monotonic()-start<float(seconds):
        time.sleep(float(poll));new_slot,cur=batch_accounts(addrs)
        for p in pools:
            try:
                ss=sigs(p["pool"],4);news=[x for x in ss if x["signature"] not in seen[p["pool"]]]
                for x in ss:seen[p["pool"]].add(x["signature"])
                elig=[x for x in news if slot<int(x.get("slot") or 0)<=new_slot]
                if len(elig)>1:amb+=len(elig);continue
                if len(elig)!=1:continue
                tr=tx(elig[0]["signature"]);v=validate_one(p,prev,tr)
                if v:
                    v["signature"]=elig[0]["signature"];rows.append(v)
                    print("[SHADOW] %s pool=%s err=%.4fbps pass=%s"%(v["family"],v["pool"][:12],v["error_bps"],v["pass"]),flush=True)
            except Exception as e:errors.append(p["family"]+":"+p["pool"][:12]+":"+type(e).__name__+":"+str(e))
            time.sleep(.08)
        prev=cur;slot=new_slot
    fams={}
    for fam in ("RAYDIUM_CLMM","ORCA_WHIRLPOOL"):
        rs=[x for x in rows if x["family"]==fam]
        fams[fam]={"samples":len(rs),"passes":sum(1 for x in rs if x["pass"]),
                   "max_error_bps":max([x["error_bps"] for x in rs],default=None),
                   "validated":bool(rs and all(x["pass"] for x in rs))}
    ok=all(x["validated"] for x in fams.values())
    payload={"revision":"QARB_060A3B","discovery":{"RAYDIUM_CLMM":cm,"ORCA_WHIRLPOOL":om},
             "warmed_pools":len(pools),"watched_accounts":len(addrs),"samples":rows,"families":fams,
             "ambiguous_intervals":amb,"warm_errors":warm_errors[-20:],"errors":errors[-20:],
             "shadow_validation_pass":ok,
             "next":"QARB_060B_BIND_LOCAL_PROVIDERS" if ok else "HOLD_NO_BOTH_FAMILY_VALIDATION",
             "execution_authority":False,"paper_only":True}
    op=root/OUT;op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[FAMILY] "+json.dumps(fams,sort_keys=True),flush=True)
    print("[SHADOW_VALIDATION_PASS]",ok,flush=True);print("[NEXT]",payload["next"],flush=True)
    print("[REPORT]",OUT,flush=True);print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=60.0);ap.add_argument("--poll",type=float,default=3.0)
    ap.add_argument("--signature-limit",type=int,default=8);ap.add_argument("--max-pools",type=int,default=6)
    a=ap.parse_args(argv);run(Path.cwd(),a.seconds,a.poll,a.signature_limit,a.max_pools)
if __name__=="__main__":main()
