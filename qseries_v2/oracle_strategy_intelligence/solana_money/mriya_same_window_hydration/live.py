from __future__ import annotations
import json,os,time,urllib.request
from collections import defaultdict,Counter
from pathlib import Path

RPC_URL=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
TARGET={"RAYDIUM_CLMM","RAYDIUM_CPMM","METEORA_DLMM","METEORA_DAMM_V2","ORCA"}
PER_VENUE=int(os.getenv("QSB_043_PER_VENUE","4"))

def rpc(method,params,timeout=15,retries=4):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(RPC_URL,data=body,headers={"content-type":"application/json","user-agent":"qseries-qsb043/1.0"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                j=json.loads(r.read().decode())
            if j.get("error"): raise RuntimeError("RPC_ERROR:"+json.dumps(j["error"]))
            return j.get("result")
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(0.35*(i+1))
    raise last

def _venue(v):
    v=str(v or "")
    return "METEORA_DAMM_V2" if v=="METEORA_DAMM" else v

def select_signatures(router_rows):
    bysig=defaultdict(set); slot={}
    for x in router_rows:
        if not isinstance(x,dict) or not x.get("signature"): continue
        v=_venue(x.get("venue"))
        if v in TARGET:
            bysig[x["signature"]].add(v)
            try: slot[x["signature"]]=int(x.get("slot"))
            except Exception: pass
    picked=[];counts=Counter()
    # Single-venue signatures only: exact transaction-level signer deltas are unambiguous.
    for sig,vs in sorted(bysig.items(),key=lambda kv:slot.get(kv[0],0),reverse=True):
        if len(vs)!=1: continue
        v=next(iter(vs))
        if counts[v]>=PER_VENUE: continue
        picked.append((sig,v,slot.get(sig)));counts[v]+=1
    return picked

def _signer(tx):
    keys=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
    for k in keys:
        if isinstance(k,dict) and k.get("signer"): return k.get("pubkey")
    return None

def _balmap(rows,owner):
    out={}
    for b in rows or []:
        if not isinstance(b,dict) or b.get("owner")!=owner: continue
        m=b.get("mint"); ui=(b.get("uiTokenAmount") or {})
        try: a=float(ui.get("uiAmountString") if ui.get("uiAmountString") is not None else ui.get("uiAmount"))
        except Exception: continue
        out[m]=out.get(m,0.0)+a
    return out

def economic_from_tx(sig,venue,router_slot,tx):
    if not isinstance(tx,dict) or (tx.get("meta") or {}).get("err") is not None: return None
    owner=_signer(tx)
    if not owner: return None
    meta=tx.get("meta") or {}
    pre=_balmap(meta.get("preTokenBalances"),owner); post=_balmap(meta.get("postTokenBalances"),owner)
    mints=set(pre)|set(post)
    ds={m:post.get(m,0.0)-pre.get(m,0.0) for m in mints}
    ds={m:d for m,d in ds.items() if abs(d)>1e-12}
    neg=[(m,-d) for m,d in ds.items() if d<0]
    pos=[(m,d) for m,d in ds.items() if d>0]
    if len(neg)!=1 or len(pos)!=1: return None
    im,ia=neg[0];om,oa=pos[0]
    slot=tx.get("slot",router_slot)
    try: slot=int(slot)
    except Exception:return None
    return {"venue":venue,"input_mint":im,"output_mint":om,"input_amount":ia,"output_amount":oa,
            "slot":slot,"signature":sig,"pool":None,"decoder_state":"EXACT_SINGLE_VENUE_SIGNER_TOKEN_DELTA",
            "source_module":"qsb_043_same_window_multidex_hydration","execution_authority":False}

def hydrate(router_rows,rpc_fn=rpc):
    rows=[];attempted=Counter();ok=Counter();ambiguous=Counter()
    for sig,v,slot in select_signatures(router_rows):
        attempted[v]+=1
        try:
            tx=rpc_fn("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
            x=economic_from_tx(sig,v,slot,tx)
            if x: rows.append(x);ok[v]+=1
            else: ambiguous[v]+=1
        except Exception:
            ambiguous[v]+=1
    return {"rows":rows,"attempted":dict(attempted),"exact":dict(ok),"rejected":dict(ambiguous)}

def write(root,router_rows,rpc_fn=rpc):
    d=hydrate(router_rows,rpc_fn)
    out={"revision":"QSB_043","execution_authority":False,**d}
    p=Path(root)/"runtime_state/qseries/qsb043_same_window_hydration/report.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
