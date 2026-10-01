from __future__ import annotations
import argparse,base64,json,time
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
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060a3_program_driven_active_pool_shadow_validator.json")

def _raw(v):
    if not v:return None
    d=v.get("data")
    if isinstance(d,list) and d:return base64.b64decode(d[0])
    if isinstance(d,str):return base64.b64decode(d)
    return None

def account(addr):
    raw,slot=c.account(addr)
    return raw,int(slot or 0)

def multi(addrs):
    if not addrs:return 0,{}
    r=c.rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"confirmed"}]) or {}
    vals=r.get("value") or [];slot=((r.get("context") or {}).get("slot") or 0)
    return int(slot),{a:_raw(v) for a,v in zip(addrs,vals)}

def sigs(addr,limit=12):
    return c.rpc("getSignaturesForAddress",[addr,{"limit":int(limit),"commitment":"confirmed"}]) or []

def tx(sig):
    return c.rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def keys(t):
    ks=(((t or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
    return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def vault_deltas(t,v0,v1):
    meta=(t or {}).get("meta") or {};ks=keys(t)
    pre={int(x["accountIndex"]):int(((x.get("uiTokenAmount") or {}).get("amount") or 0))
         for x in meta.get("preTokenBalances") or []}
    post={int(x["accountIndex"]):int(((x.get("uiTokenAmount") or {}).get("amount") or 0))
          for x in meta.get("postTokenBalances") or []}
    try:i0=ks.index(v0);i1=ks.index(v1)
    except ValueError:return None
    if i0 not in pre or i1 not in pre or i0 not in post or i1 not in post:return None
    return post[i0]-pre[i0],post[i1]-pre[i1]

def try_pool(family,addr):
    try:
        raw,slot=account(addr)
        if family=="RAYDIUM_CLMM":
            st=q56b.decode_pool(raw)
            if not st.get("token_mint_0") or not st.get("token_mint_1"):return None
            cr,cslot=account(st["amm_config"]);cfg=q56b.decode_config(cr)
            spacing=int(st["tick_spacing"]);tick=int(st["tick_current"]);base=q57a.array_start(tick,spacing);w=60*spacing
            arr=[]
            for s in [base,base-w,base-2*w,base-3*w,base+w,base+2*w,base+3*w]:
                a,_=q57a.tick_array_pda(addr,s)
                try:rr,ss=account(a);arr.append(a)
                except Exception:pass
            if not arr:return None
            return {"family":family,"pool":addr,"state":st,"config":cfg,"vault_a":st["token_vault_0"],
                    "vault_b":st["token_vault_1"],"addresses":[addr,st["amm_config"]]+arr}
        st=q56c.decode_pool(raw)
        seq=q57b.resolve(addr,int(st["tick_current"]),int(st["tick_spacing"]))
        arr=[]
        for xs in seq.values():arr += [x["address"] for x in xs if x.get("exists")]
        arr=list(dict.fromkeys(arr))
        if not arr:return None
        return {"family":family,"pool":addr,"state":st,"vault_a":st["token_vault_a"],
                "vault_b":st["token_vault_b"],"addresses":[addr]+arr}
    except Exception:
        return None

def discover_active(family,program,signature_limit=16,max_pools=8):
    found={};tx_seen=0;account_tests=0
    for s in sigs(program,signature_limit):
        if len(found)>=max_pools:break
        try:t=tx(s["signature"]);tx_seen+=1
        except Exception:continue
        for a in keys(t):
            if not isinstance(a,str) or a in (program,) or a in found:continue
            account_tests+=1
            p=try_pool(family,a)
            if p:
                p["discovery_signature"]=s["signature"];found[a]=p
                if len(found)>=max_pools:break
            if account_tests>=160:break
        if account_tests>=160:break
    return list(found.values()),{"transactions":tx_seen,"account_tests":account_tests}

def local_quote(p,snap,amount,zero):
    if p["family"]=="RAYDIUM_CLMM":
        st=q56b.decode_pool(snap[p["pool"]]);cfg=q56b.decode_config(snap[st["amm_config"]]);ticks={}
        for a in p["addresses"]:
            if a in (p["pool"],st["amm_config"]):continue
            rr=snap.get(a)
            if rr:
                for x in q58a.decode_ticks(rr):ticks[x["tick"]]=x
        if not ticks:raise RuntimeError("NO_CLMM_TICKS")
        return q58a.quote_steps(st["sqrt_price_x64"],st["liquidity"],cfg["trade_fee_rate"],
                                amount,list(ticks.values()),zero)["amount_out"]
    st=q56c.decode_pool(snap[p["pool"]]);ticks={}
    for a in p["addresses"]:
        if a==p["pool"]:continue
        rr=snap.get(a)
        if rr and rr[:8]==q58b.tick_disc():
            start=int.from_bytes(rr[8:12],"little",signed=True)
            for x in q58b.decode_fixed(rr,start,st["tick_spacing"]):ticks[x["tick"]]=x
    if not ticks:raise RuntimeError("NO_ORCA_TICKS")
    return q58b.quote_steps(st["sqrt_price_x64"],st["liquidity"],st["fee_rate"],
                            amount,list(ticks.values()),zero)["amount_out"]

def validate_one(p,pre_snap,t):
    ds=vault_deltas(t,p["vault_a"],p["vault_b"])
    if not ds:return None
    d0,d1=ds
    if d0>0 and d1<0:zero=True;ain=d0;actual=-d1
    elif d1>0 and d0<0:zero=False;ain=d1;actual=-d0
    else:return None
    if ain<=0 or actual<=0:return None
    quoted=int(local_quote(p,pre_snap,ain,zero))
    err=abs(quoted-actual)/actual*10000.0
    return {"family":p["family"],"pool":p["pool"],"amount_in":ain,"actual_out":actual,
            "local_out":quoted,"error_bps":err,"pass":err<=MAX_ERROR_BPS,
            "direction":"A_TO_B" if zero else "B_TO_A"}

def run(root,seconds=60.0,poll=2.0,signature_limit=16,max_pools=8):
    root=Path(root)
    cl,clmeta=discover_active("RAYDIUM_CLMM",CLMM_PROGRAM,signature_limit,max_pools)
    oc,ocmeta=discover_active("ORCA_WHIRLPOOL",ORCA_PROGRAM,signature_limit,max_pools)
    pools=cl+oc
    adds=list(dict.fromkeys(a for p in pools for a in p["addresses"]))
    slot,prev=multi(adds)
    seen={p["pool"]:{x["signature"] for x in sigs(p["pool"],6)} for p in pools}
    rows=[];amb=0;errors=[];start=time.monotonic()
    print("[QARB-060A3] PROGRAM-DRIVEN ACTIVE-POOL SHADOW VALIDATOR",flush=True)
    print("[DISCOVER] clmm_active=%d orca_active=%d watched_accounts=%d"%(len(cl),len(oc),len(adds)),flush=True)
    print("[SCAN] clmm_tx=%d clmm_account_tests=%d orca_tx=%d orca_account_tests=%d"%(
        clmeta["transactions"],clmeta["account_tests"],ocmeta["transactions"],ocmeta["account_tests"]),flush=True)
    print("[WATCH] seconds=%.1f poll=%.1f"%(seconds,poll),flush=True)
    if not pools:
        payload={"revision":"QARB_060A3","active_pools":{"RAYDIUM_CLMM":0,"ORCA_WHIRLPOOL":0},
                 "shadow_validation_pass":False,"next":"HOLD_ACTIVE_POOL_DISCOVERY_EMPTY",
                 "execution_authority":False,"paper_only":True}
        op=root/OUT;op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(payload,indent=2),encoding="utf-8")
        print("[HOLD] no decodable active pools discovered",flush=True);print("[REPORT]",OUT,flush=True);return payload
    while time.monotonic()-start<float(seconds):
        time.sleep(float(poll));new_slot,cur=multi(adds)
        for p in pools:
            try:
                ss=sigs(p["pool"],6);news=[x for x in ss if x["signature"] not in seen[p["pool"]]]
                for x in ss:seen[p["pool"]].add(x["signature"])
                elig=[x for x in news if slot<int(x.get("slot") or 0)<=new_slot]
                if len(elig)>1:amb+=len(elig);continue
                if len(elig)!=1:continue
                tr=tx(elig[0]["signature"]);v=validate_one(p,prev,tr)
                if v:
                    v["signature"]=elig[0]["signature"];v["slot"]=elig[0].get("slot");rows.append(v)
                    print("[SHADOW] %s pool=%s dir=%s err=%.4fbps pass=%s"%(
                        v["family"],v["pool"][:12],v["direction"],v["error_bps"],v["pass"]),flush=True)
            except Exception as e:errors.append(p["family"]+":"+p["pool"][:12]+":"+type(e).__name__+":"+str(e))
        prev=cur;slot=new_slot
    fams={}
    for fam in ("RAYDIUM_CLMM","ORCA_WHIRLPOOL"):
        rs=[x for x in rows if x["family"]==fam]
        fams[fam]={"samples":len(rs),"passes":sum(1 for x in rs if x["pass"]),
                   "max_error_bps":max([x["error_bps"] for x in rs],default=None),
                   "validated":bool(rs and all(x["pass"] for x in rs))}
    ok=all(x["validated"] for x in fams.values())
    payload={"revision":"QARB_060A3",
             "active_pools":{"RAYDIUM_CLMM":len(cl),"ORCA_WHIRLPOOL":len(oc)},
             "discovery":{"RAYDIUM_CLMM":clmeta,"ORCA_WHIRLPOOL":ocmeta},
             "watched_accounts":len(adds),"samples":rows,"families":fams,
             "ambiguous_intervals":amb,"errors":errors[-30:],"shadow_validation_pass":ok,
             "next":"QARB_060B_BIND_LOCAL_PROVIDERS" if ok else "HOLD_NO_BOTH_FAMILY_VALIDATION",
             "execution_authority":False,"paper_only":True}
    op=root/OUT;op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[FAMILY] "+json.dumps(fams,sort_keys=True),flush=True)
    print("[SHADOW_VALIDATION_PASS]",ok,flush=True);print("[NEXT]",payload["next"],flush=True)
    print("[REPORT]",OUT,flush=True);print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=60.0)
    ap.add_argument("--poll",type=float,default=2.0);ap.add_argument("--signature-limit",type=int,default=16)
    ap.add_argument("--max-pools",type=int,default=8)
    a=ap.parse_args(argv);run(Path.cwd(),a.seconds,a.poll,a.signature_limit,a.max_pools)

if __name__=="__main__":main()
