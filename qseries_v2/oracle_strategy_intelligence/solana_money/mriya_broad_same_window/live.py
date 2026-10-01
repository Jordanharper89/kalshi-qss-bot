from __future__ import annotations
import json,os,time,urllib.request
from collections import defaultdict,Counter

RPC_URL=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
WSOL="So11111111111111111111111111111111111111112"
TARGET={"RAYDIUM_CLMM","RAYDIUM_CPMM","METEORA_DLMM","METEORA_DAMM_V2","ORCA"}
PER_VENUE=int(os.getenv("QSB_044B_PER_VENUE","8"))
MAX_SLOTS=int(os.getenv("QSB_044B_MAX_SLOTS","6"))

def _venue(v):
    v=str(v or "")
    return "METEORA_DAMM_V2" if v=="METEORA_DAMM" else v

def select_signatures(rows):
    bysig=defaultdict(set);slots={}
    for x in rows:
        if not isinstance(x,dict) or not x.get("signature"):continue
        v=_venue(x.get("venue"))
        if v not in TARGET:continue
        s=x["signature"];bysig[s].add(v)
        try:slots[s]=int(x.get("slot"))
        except Exception:continue
    out=[];n=Counter()
    for sig,vs in sorted(bysig.items(),key=lambda kv:slots.get(kv[0],0),reverse=True):
        if len(vs)!=1:continue
        v=next(iter(vs))
        if n[v]>=PER_VENUE:continue
        out.append((sig,v,slots[sig]));n[v]+=1
    return out

def _rpc(method,params,timeout=20,retries=6):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(RPC_URL,data=body,headers={"content-type":"application/json","user-agent":"qseries-qsb044b/1.0"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                j=json.loads(r.read().decode())
            if j.get("error"):raise RuntimeError("RPC_ERROR:"+json.dumps(j["error"]))
            return j.get("result")
        except Exception as e:
            last=e
            msg=str(e)
            if "429" in msg and i+1<retries:
                time.sleep(min(3.0,0.75*(i+1)));continue
            if i+1<retries:
                time.sleep(.35*(i+1));continue
    raise last

def _tx_signature(tx):
    try:
        sigs=((tx.get("transaction") or {}).get("signatures") or [])
        return sigs[0] if sigs else None
    except Exception:return None

def hydrate_selected(selected,rpc_fn=_rpc):
    # Fetch a handful of full blocks once, then recover many transactions locally.
    wanted={s:(v,slot) for s,v,slot in selected}
    slots=sorted({slot for _,_,slot in selected},reverse=True)[:MAX_SLOTS]
    found={}
    failures=[]
    for slot in slots:
        try:
            b=rpc_fn("getBlock",[slot,{"encoding":"jsonParsed","transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":0}])
            for tx in (b or {}).get("transactions") or []:
                sig=_tx_signature(tx)
                if sig in wanted:
                    v,_=wanted[sig]
                    # getBlock tx lacks top-level slot; attach exact block slot.
                    x=dict(tx);x["slot"]=slot;found[sig]=(v,slot,x)
            time.sleep(.12)
        except Exception as e:
            failures.append({"slot":slot,"error":f"{type(e).__name__}: {e}"})
    return found,{"slots_requested":slots,"slot_count":len(slots),"block_failures":failures}

def _signer(tx):
    for k in ((((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []):
        if isinstance(k,dict) and k.get("signer"):return k.get("pubkey")
    return None

def _balmap(rows,owner):
    out={}
    for b in rows or []:
        if not isinstance(b,dict) or b.get("owner")!=owner:continue
        m=b.get("mint");u=b.get("uiTokenAmount") or {}
        try:a=float(u.get("uiAmountString") if u.get("uiAmountString") is not None else u.get("uiAmount"))
        except Exception:continue
        out[m]=out.get(m,0.0)+a
    return out

def _native_delta(tx,owner):
    msg=(((tx or {}).get("transaction") or {}).get("message") or {})
    keys=msg.get("accountKeys") or []
    idx=None
    for i,k in enumerate(keys):
        if isinstance(k,dict) and k.get("pubkey")==owner:idx=i;break
    if idx is None:return None
    meta=tx.get("meta") or {};pre=meta.get("preBalances") or [];post=meta.get("postBalances") or []
    if idx>=len(pre) or idx>=len(post):return None
    fee=int(meta.get("fee") or 0)
    return (int(post[idx])-int(pre[idx])+fee)/1e9

def economic_from_tx(sig,venue,router_slot,tx):
    if not isinstance(tx,dict) or (tx.get("meta") or {}).get("err") is not None:return None
    owner=_signer(tx)
    if not owner:return None
    meta=tx.get("meta") or {}
    pre=_balmap(meta.get("preTokenBalances"),owner);post=_balmap(meta.get("postTokenBalances"),owner)
    ds={m:post.get(m,0.0)-pre.get(m,0.0) for m in set(pre)|set(post)}
    ds={m:d for m,d in ds.items() if abs(d)>1e-12}
    neg=[(m,-d) for m,d in ds.items() if d<0];pos=[(m,d) for m,d in ds.items() if d>0]
    try:slot=int(tx.get("slot",router_slot))
    except Exception:return None
    base={"venue":venue,"slot":slot,"signature":sig,"pool":None,"source_module":"qsb_044b_slot_block_hydration","execution_authority":False}
    if len(neg)==1 and len(pos)==1:
        im,ia=neg[0];om,oa=pos[0]
        return {**base,"input_mint":im,"output_mint":om,"input_amount":ia,"output_amount":oa,
                "decoder_state":"EXACT_SINGLE_VENUE_SIGNER_TOKEN_DELTA","discovery_quality":"EXACT_TOKEN_TOKEN"}
    nd=_native_delta(tx,owner)
    if nd is not None and abs(nd)>=0.00001:
        if len(pos)==1 and len(neg)==0 and nd<0:
            om,oa=pos[0]
            return {**base,"input_mint":WSOL,"output_mint":om,"input_amount":abs(nd),"output_amount":oa,
                    "decoder_state":"DISCOVERY_NATIVE_SOL_DELTA","discovery_quality":"REQUOTE_REQUIRED"}
        if len(neg)==1 and len(pos)==0 and nd>0:
            im,ia=neg[0]
            return {**base,"input_mint":im,"output_mint":WSOL,"input_amount":ia,"output_amount":nd,
                    "decoder_state":"DISCOVERY_NATIVE_SOL_DELTA","discovery_quality":"REQUOTE_REQUIRED"}
    return None

def hydrate(router_rows,rpc_fn=_rpc):
    sel=select_signatures(router_rows)
    txs,block_meta=hydrate_selected(sel,rpc_fn)
    attempted=Counter(v for _,v,_ in sel);exact=Counter();native=Counter();rej=Counter();rows=[]
    for sig,v,slot in sel:
        z=txs.get(sig)
        if not z:rej[v]+=1;continue
        x=economic_from_tx(sig,v,slot,z[2])
        if not x:rej[v]+=1;continue
        rows.append(x)
        if x["discovery_quality"]=="EXACT_TOKEN_TOKEN":exact[v]+=1
        else:native[v]+=1
    return {"rows":rows,"attempted":dict(attempted),"exact_token_token":dict(exact),
            "native_sol_discovery":dict(native),"rejected":dict(rej),"block_hydration":block_meta}
