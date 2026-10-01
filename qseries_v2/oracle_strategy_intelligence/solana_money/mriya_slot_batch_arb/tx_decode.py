from __future__ import annotations
from collections import defaultdict
from .venue_registry import BY_PROGRAM,TARGET_WALLET,TARGET_EXECUTOR

def keys_and_signers(tx):
    msg=((tx or {}).get("transaction") or {}).get("message") or {};keys=[];signers=set()
    for x in msg.get("accountKeys") or []:
        if isinstance(x,dict):
            p=x.get("pubkey")
            if p:
                p=str(p);keys.append(p)
                if x.get("signer"):signers.add(p)
        elif x is not None:keys.append(str(x))
    la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
    for k in ("writable","readonly","readOnly"):
        for x in la.get(k) or []:keys.append(str(x))
    return keys,signers

def program_ids(tx):
    keys,_=keys_and_signers(tx);msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
    def add(ix):
        if not isinstance(ix,dict):return
        p=ix.get("programId")
        if p:out.append(str(p));return
        i=ix.get("programIdIndex")
        if isinstance(i,int) and 0<=i<len(keys):out.append(keys[i])
    for ix in msg.get("instructions") or []:add(ix)
    for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
        for ix in g.get("instructions") or []:add(ix)
    return tuple(out)

def _amt(b):
    try:return float((b.get("uiTokenAmount") or {}).get("uiAmountString") or 0)
    except Exception:return 0.0

def signer_flows(tx):
    _,signers=keys_and_signers(tx);m=(tx or {}).get("meta") or {}
    pre=defaultdict(lambda:defaultdict(float));post=defaultdict(lambda:defaultdict(float))
    for field,target in (("preTokenBalances",pre),("postTokenBalances",post)):
        for b in m.get(field) or []:
            owner=str(b.get("owner") or "");mint=str(b.get("mint") or "")
            if owner and mint:target[owner][mint]+=_amt(b)
    out={}
    for owner in signers:
        d={mint:post[owner].get(mint,0)-pre[owner].get(mint,0) for mint in set(pre[owner])|set(post[owner])}
        d={k:v for k,v in d.items() if abs(v)>1e-12}
        if d:out[owner]=d
    return out

def decode_edges(tx,slot,block_time,received_unix):
    if not isinstance(tx,dict) or ((tx.get("meta") or {}).get("err") is not None):return [],"TX_ERROR"
    pids=program_ids(tx);venues=sorted({BY_PROGRAM[p] for p in pids if p in BY_PROGRAM})
    sigs=((tx.get("transaction") or {}).get("signatures") or [])
    sig=str(sigs[0]) if sigs else ""
    if not sig:return [],"NO_SIGNATURE"
    if len(venues)!=1:return [],("MULTI_DEX_TX" if len(venues)>1 else "NO_TRACKED_DEX")
    venue=venues[0];out=[]
    for owner,d in signer_flows(tx).items():
        neg=[(m,-v) for m,v in d.items() if v<0];pos=[(m,v) for m,v in d.items() if v>0]
        if len(neg)!=1 or len(pos)!=1:continue
        src,ain=neg[0];dst,aout=pos[0]
        if ain<=0 or aout<=0 or src==dst:continue
        out.append({"src":src,"dst":dst,"rate":aout/ain,"input_amount":ain,"output_amount":aout,
                    "venue":venue,"signature":sig,"slot":int(slot),"block_time":float(block_time or 0),
                    "received_unix":float(received_unix),"owner":owner,
                    "observed_direction":True,"basis":"BLOCK_FULL_TX_SIGNER_DELTA"})
    return out,("OK" if out else "NO_SIMPLE_SIGNER_FLOW")

def classify_target(tx):
    keys,_=keys_and_signers(tx);pids=program_ids(tx);m=(tx or {}).get("meta") or {}
    return {"contains_target":TARGET_WALLET in keys,"executor_present":TARGET_EXECUTOR in pids,
            "failed":m.get("err") is not None,"tracked_venues":sorted({BY_PROGRAM[p] for p in pids if p in BY_PROGRAM})}
