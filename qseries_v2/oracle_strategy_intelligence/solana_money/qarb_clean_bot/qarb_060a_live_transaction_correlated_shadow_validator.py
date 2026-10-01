from __future__ import annotations
import argparse,base64,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056b_clmm_tick_fee_state as q56b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_056c_orca_tick_fee_state as q56c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058a_clmm_local_swap_math as q58a
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_058b_orca_local_swap_math as q58b

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_ERROR_BPS=10.0
CLMM_STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_056b_clmm_tick_fee_state.json")
CLMM_ARRAYS=Path("runtime_state/qseries/qarb_clean_bot/qarb_057a2_clmm_directional_tick_array_resolver.json")
ORCA_STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_056c_orca_tick_fee_state.json")
ORCA_ARRAYS=Path("runtime_state/qseries/qarb_clean_bot/qarb_057b_orca_tick_array_pda_resolver.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_060a_live_transaction_correlated_shadow_validator.json")

def _load(root,p):
    q=Path(root)/p
    if not q.is_file():raise RuntimeError("MISSING:"+str(p))
    return json.loads(q.read_text(encoding="utf-8"))

def _raw(v):
    if not v:return None
    d=v.get("data")
    if isinstance(d,list) and d:return base64.b64decode(d[0])
    if isinstance(d,str):return base64.b64decode(d)
    return None

def multi(addrs):
    r=c.rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"confirmed"}])
    vals=(r or {}).get("value") or [];slot=((r or {}).get("context") or {}).get("slot")
    return int(slot or 0),{a:_raw(v) for a,v in zip(addrs,vals)}

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
    if i0 not in pre or i0 not in post or i1 not in pre or i1 not in post:return None
    return post[i0]-pre[i0],post[i1]-pre[i1]

def _uniq(xs):
    out=[]
    for x in xs:
        if x and x not in out:out.append(x)
    return out

def prepare(root):
    cs=_load(root,CLMM_STATE);ca=_load(root,CLMM_ARRAYS)
    os=_load(root,ORCA_STATE);oa=_load(root,ORCA_ARRAYS)
    ca_by={r["pool"]:r for r in ca["rows"]};oa_by={r["pool"]:r for r in oa["rows"]}
    pools=[]
    for r in cs["rows"]:
        st=r.get("state") or {};cfg=r.get("config") or {}
        addrs=[r["pool"],st.get("amm_config")]
        for seq in (ca_by.get(r["pool"],{}).get("sequences") or {}).values():
            addrs += [x.get("address") for x in seq if x.get("exists")]
        pools.append({"family":"RAYDIUM_CLMM","pool":r["pool"],"token_a":st.get("token_mint_0"),
                      "token_b":st.get("token_mint_1"),"vault_a":st.get("token_vault_0"),
                      "vault_b":st.get("token_vault_1"),"config":st.get("amm_config"),
                      "addresses":_uniq(addrs)})
    for r in os["rows"]:
        st=r.get("state") or {};addrs=[r["pool"]]
        for seq in (oa_by.get(r["pool"],{}).get("sequences") or {}).values():
            addrs += [x.get("address") for x in seq if x.get("exists")]
        pools.append({"family":"ORCA_WHIRLPOOL","pool":r["pool"],"token_a":st.get("token_mint_a"),
                      "token_b":st.get("token_mint_b"),"vault_a":st.get("token_vault_a"),
                      "vault_b":st.get("token_vault_b"),"addresses":_uniq(addrs)})
    all_addrs=_uniq([a for p in pools for a in p["addresses"]])
    return pools,all_addrs

def local_quote(p,snap,amount,zero):
    pr=snap[p["pool"]]
    if p["family"]=="RAYDIUM_CLMM":
        st=q56b.decode_pool(pr)
        cfg=q56b.decode_config(snap[p["config"]])
        ticks={}
        for a in p["addresses"]:
            if a in (p["pool"],p["config"]):continue
            rr=snap.get(a)
            if rr:
                for x in q58a.decode_ticks(rr):ticks[x["tick"]]=x
        if not ticks:raise RuntimeError("NO_CLMM_TICKS")
        return q58a.quote_steps(st["sqrt_price_x64"],st["liquidity"],cfg["trade_fee_rate"],
                                amount,list(ticks.values()),zero)["amount_out"]
    st=q56c.decode_pool(pr);ticks={}
    for a in p["addresses"]:
        if a==p["pool"]:continue
        rr=snap.get(a)
        if rr and rr[:8]==q58b.tick_disc():
            # start index is encoded immediately after discriminator in fixed TickArray
            start=int.from_bytes(rr[8:12],"little",signed=True)
            for x in q58b.decode_fixed(rr,start,st["tick_spacing"]):ticks[x["tick"]]=x
    if not ticks:raise RuntimeError("NO_ORCA_TICKS")
    return q58b.quote_steps(st["sqrt_price_x64"],st["liquidity"],st["fee_rate"],
                            amount,list(ticks.values()),zero)["amount_out"]

def validate_one(p,pre_snap,t):
    ds=vault_deltas(t,p["vault_a"],p["vault_b"])
    if not ds:return None
    d0,d1=ds
    if d0>0 and d1<0:zero=True;amount_in=d0;actual=-d1
    elif d1>0 and d0<0:zero=False;amount_in=d1;actual=-d0
    else:return None
    if amount_in<=0 or actual<=0:return None
    quoted=local_quote(p,pre_snap,amount_in,zero)
    err=abs(int(quoted)-int(actual))/int(actual)*10000.0
    return {"family":p["family"],"pool":p["pool"],"amount_in":amount_in,"actual_out":actual,
            "local_out":int(quoted),"error_bps":err,"pass":err<=MAX_ERROR_BPS,
            "direction":"A_TO_B" if zero else "B_TO_A"}

def run(root,seconds=30.0,poll=2.0):
    root=Path(root);pools,addrs=prepare(root)
    slot,prev=multi(addrs)
    seen={p["pool"]:{x["signature"] for x in sigs(p["pool"])} for p in pools}
    rows=[];ambiguous=0;errors=[];started=time.monotonic()
    print("[QARB-060A] LIVE TRANSACTION-CORRELATED SHADOW VALIDATOR",flush=True)
    print("[WATCH] pools=%d accounts=%d seconds=%.1f poll=%.1f"%(len(pools),len(addrs),seconds,poll),flush=True)
    print("[RULE] one new pool signature per interval + pre-state snapshot + confirmed tx vault deltas",flush=True)
    while time.monotonic()-started<float(seconds):
        time.sleep(float(poll))
        new_slot,cur=multi(addrs)
        for p in pools:
            try:
                ss=sigs(p["pool"]);news=[x for x in ss if x["signature"] not in seen[p["pool"]]]
                for x in ss:seen[p["pool"]].add(x["signature"])
                eligible=[x for x in news if slot<int(x.get("slot") or 0)<=new_slot]
                if len(eligible)>1:
                    ambiguous+=len(eligible);continue
                if len(eligible)!=1:continue
                x=eligible[0];tr=tx(x["signature"])
                v=validate_one(p,prev,tr)
                if v:
                    v["signature"]=x["signature"];v["slot"]=x.get("slot");rows.append(v)
                    print("[SHADOW] %s pool=%s dir=%s in=%d local=%d actual=%d err=%.4fbps pass=%s"%(
                        v["family"],v["pool"][:12],v["direction"],v["amount_in"],v["local_out"],
                        v["actual_out"],v["error_bps"],v["pass"]),flush=True)
            except Exception as e:errors.append(p["family"]+":"+p["pool"][:12]+":"+type(e).__name__+":"+str(e))
        prev=cur;slot=new_slot
    fams={}
    for fam in ("RAYDIUM_CLMM","ORCA_WHIRLPOOL"):
        rs=[x for x in rows if x["family"]==fam]
        fams[fam]={"samples":len(rs),"passes":sum(1 for x in rs if x["pass"]),
                   "max_error_bps":max([x["error_bps"] for x in rs],default=None),
                   "validated":bool(rs and all(x["pass"] for x in rs))}
    payload={"revision":"QARB_060A","seconds":seconds,"poll_seconds":poll,"samples":rows,
             "families":fams,"ambiguous_intervals":ambiguous,"errors":errors[-20:],
             "shadow_validation_pass":all(x["validated"] for x in fams.values()),
             "next":"QARB_060B_BIND_LOCAL_PROVIDERS" if all(x["validated"] for x in fams.values())
                    else "HOLD_RERUN_UNTIL_BOTH_FAMILIES_HAVE_VALIDATED_SAMPLE",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[FAMILY] "+json.dumps(fams,sort_keys=True),flush=True)
    print("[SHADOW_VALIDATION_PASS]",payload["shadow_validation_pass"],flush=True)
    print("[NEXT]",payload["next"],flush=True);print("[REPORT]",OUT,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return payload

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=30.0);ap.add_argument("--poll",type=float,default=2.0)
    a=ap.parse_args(argv);run(Path.cwd(),a.seconds,a.poll)

if __name__=="__main__":main()
