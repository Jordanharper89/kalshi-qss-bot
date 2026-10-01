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
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060a2_broad_pool_live_shadow_validator.json")

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def _raw(v):
    if not v:return None
    d=v.get("data")
    if isinstance(d,list) and d:return base64.b64decode(d[0])
    if isinstance(d,str):return base64.b64decode(d)
    return None

def account(addr):
    raw,slot=c.account(addr);return raw,int(slot or 0)

def multi(addrs):
    r=c.rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"confirmed"}]) or {}
    vals=r.get("value") or [];slot=((r.get("context") or {}).get("slot") or 0)
    return int(slot),{a:_raw(v) for a,v in zip(addrs,vals)}

def sigs(pool,limit=4):
    return c.rpc("getSignaturesForAddress",[pool,{"limit":limit,"commitment":"confirmed"}]) or []

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

def candidates(root):
    cl=[];oc=[]
    rs=Path(root)/"runtime_state"
    for p in rs.rglob("*.json") if rs.exists() else []:
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        for d in walk(o):
            pool=d.get("pool")
            if not isinstance(pool,str) or len(pool)<30:continue
            fam=str(d.get("venue") or d.get("family") or d.get("venue_name") or "").upper()
            if "RAYDIUM_CLMM" in fam and pool not in cl:cl.append(pool)
            if ("ORCA" in fam or "WHIRLPOOL" in fam) and pool not in oc:oc.append(pool)
    return cl,oc

def build_pool(family,pool):
    raw,slot=account(pool)
    if family=="RAYDIUM_CLMM":
        st=q56b.decode_pool(raw)
        cr,cslot=account(st["amm_config"]);cfg=q56b.decode_config(cr)
        spacing=int(st["tick_spacing"]);tick=int(st["tick_current"]);base=q57a.array_start(tick,spacing);w=60*spacing
        arr=[]
        for s in [base,base-w,base-2*w,base-3*w,base+w,base+2*w,base+3*w]:
            a,_=q57a.tick_array_pda(pool,s)
            try:rr,ss=account(a);arr.append((a,rr,ss))
            except Exception:pass
        return {"family":family,"pool":pool,"slot":slot,"state":st,"config":cfg,
                "token_a":st["token_mint_0"],"token_b":st["token_mint_1"],
                "vault_a":st["token_vault_0"],"vault_b":st["token_vault_1"],
                "addresses":[pool,st["amm_config"]]+[x[0] for x in arr]}
    st=q56c.decode_pool(raw);seq=q57b.resolve(pool,int(st["tick_current"]),int(st["tick_spacing"]))
    adds=[pool]
    for xs in seq.values():
        adds += [x["address"] for x in xs if x.get("exists")]
    return {"family":family,"pool":pool,"slot":slot,"state":st,
            "token_a":st["token_mint_a"],"token_b":st["token_mint_b"],
            "vault_a":st["token_vault_a"],"vault_b":st["token_vault_b"],
            "addresses":list(dict.fromkeys(adds))}

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

def run(root,seconds=60.0,poll=2.0,max_each=12):
    root=Path(root);cl_ids,oc_ids=candidates(root);pools=[];warm_errors=[]
    for fam,ids in (("RAYDIUM_CLMM",cl_ids[:max_each]),("ORCA_WHIRLPOOL",oc_ids[:max_each])):
        for pool in ids:
            try:pools.append(build_pool(fam,pool))
            except Exception as e:warm_errors.append(fam+":"+pool[:12]+":"+type(e).__name__+":"+str(e))
            time.sleep(.08)
    adds=list(dict.fromkeys(a for p in pools for a in p["addresses"]))
    slot,prev=multi(adds)
    seen={p["pool"]:{x["signature"] for x in sigs(p["pool"])} for p in pools}
    rows=[];amb=0;errors=[];start=time.monotonic()
    print("[QARB-060A2] BROAD-POOL LIVE SHADOW VALIDATOR",flush=True)
    print("[DISCOVER] clmm_candidates=%d orca_candidates=%d warmed=%d accounts=%d"%(len(cl_ids),len(oc_ids),len(pools),len(adds)),flush=True)
    print("[WATCH] seconds=%.1f poll=%.1f max_each=%d"%(seconds,poll,max_each),flush=True)
    while time.monotonic()-start<float(seconds):
        time.sleep(float(poll));new_slot,cur=multi(adds)
        for p in pools:
            try:
                ss=sigs(p["pool"]);news=[x for x in ss if x["signature"] not in seen[p["pool"]]]
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
    payload={"revision":"QARB_060A2","candidate_counts":{"RAYDIUM_CLMM":len(cl_ids),"ORCA_WHIRLPOOL":len(oc_ids)},
             "warmed_pools":len(pools),"watched_accounts":len(adds),"samples":rows,"families":fams,
             "ambiguous_intervals":amb,"warm_errors":warm_errors[-30:],"errors":errors[-30:],
             "shadow_validation_pass":ok,
             "next":"QARB_060B_BIND_LOCAL_PROVIDERS" if ok else "HOLD_NO_BOTH_FAMILY_VALIDATION",
             "execution_authority":False,"paper_only":True}
    op=root/OUT;op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[FAMILY] "+json.dumps(fams,sort_keys=True),flush=True)
    print("[SHADOW_VALIDATION_PASS]",ok,flush=True);print("[NEXT]",payload["next"],flush=True)
    print("[REPORT]",OUT,flush=True);print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=60.0)
    ap.add_argument("--poll",type=float,default=2.0);ap.add_argument("--max-each",type=int,default=12)
    a=ap.parse_args(argv);run(Path.cwd(),a.seconds,a.poll,a.max_each)

if __name__=="__main__":main()
