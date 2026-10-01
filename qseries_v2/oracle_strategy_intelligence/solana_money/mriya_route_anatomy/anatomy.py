from __future__ import annotations
from collections import defaultdict
from .registry import BY_PROGRAM,TARGET_WALLET,TARGET_EXECUTOR,TOKEN_PROGRAMS,ANCHORS

def account_keys(tx):
    msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
    for x in msg.get("accountKeys") or []:
        p=x.get("pubkey") if isinstance(x,dict) else x
        if p:out.append(str(p))
    la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
    for k in ("writable","readonly","readOnly"):
        for x in la.get(k) or []:out.append(str(x))
    return out

def _pid(ix,keys):
    if not isinstance(ix,dict):return ""
    if ix.get("programId"):return str(ix["programId"])
    i=ix.get("programIdIndex")
    return keys[i] if isinstance(i,int) and 0<=i<len(keys) else ""

def program_ids(tx):
    keys=account_keys(tx);msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
    for ix in msg.get("instructions") or []:
        p=_pid(ix,keys)
        if p:out.append(p)
    for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
        for ix in g.get("instructions") or []:
            p=_pid(ix,keys)
            if p:out.append(p)
    return tuple(out)

def token_account_map(tx):
    keys=account_keys(tx);m=(tx or {}).get("meta") or {};out={}
    for field in ("preTokenBalances","postTokenBalances"):
        for b in m.get(field) or []:
            i=b.get("accountIndex")
            if not isinstance(i,int) or i<0 or i>=len(keys):continue
            out[keys[i]]={"mint":str(b.get("mint") or ""),"owner":str(b.get("owner") or "")}
    return out

def _ui_amount(info):
    ta=info.get("tokenAmount") if isinstance(info,dict) else None
    if isinstance(ta,dict):
        try:return float(ta.get("uiAmountString") or ta.get("uiAmount") or 0)
        except Exception:return 0.0
    try:return float(info.get("amount") or 0)
    except Exception:return 0.0

def parsed_transfer(ix,amap):
    if not isinstance(ix,dict):return None
    p=ix.get("parsed")
    if not isinstance(p,dict):return None
    typ=str(p.get("type") or "").lower()
    if typ not in ("transfer","transferchecked"):return None
    info=p.get("info") or {}
    src=str(info.get("source") or "");dst=str(info.get("destination") or "")
    if not src or not dst:return None
    amount=_ui_amount(info)
    mint=str(info.get("mint") or (amap.get(src) or {}).get("mint") or (amap.get(dst) or {}).get("mint") or "")
    if amount<=0 or not mint:return None
    return {"source":src,"destination":dst,"mint":mint,"amount":amount,
            "source_owner":str((amap.get(src) or {}).get("owner") or ""),
            "destination_owner":str((amap.get(dst) or {}).get("owner") or "")}

def wallet_token_deltas(tx,wallet=TARGET_WALLET):
    m=(tx or {}).get("meta") or {};pre=defaultdict(float);post=defaultdict(float)
    for field,target in (("preTokenBalances",pre),("postTokenBalances",post)):
        for b in m.get(field) or []:
            if str(b.get("owner") or "")!=wallet:continue
            try:v=float((b.get("uiTokenAmount") or {}).get("uiAmountString") or 0)
            except Exception:v=0.0
            target[str(b.get("mint") or "")]+=v
    return {k:post[k]-pre[k] for k in set(pre)|set(post) if abs(post[k]-pre[k])>1e-12}

def wallet_sol_delta(tx,wallet=TARGET_WALLET):
    keys=account_keys(tx);m=(tx or {}).get("meta") or {}
    try:i=keys.index(wallet)
    except ValueError:return None
    pre=m.get("preBalances") or [];post=m.get("postBalances") or []
    if i>=len(pre) or i>=len(post):return None
    return (post[i]-pre[i])/1e9

def dex_sequence(tx):
    keys=account_keys(tx);seq=[]
    for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
        for ordinal,ix in enumerate(g.get("instructions") or []):
            p=_pid(ix,keys)
            if p in BY_PROGRAM:
                seq.append({"parent_index":g.get("index"),"inner_ordinal":ordinal,"venue":BY_PROGRAM[p],"program_id":p})
    return seq

def reconstruct_legs(tx):
    keys=account_keys(tx);amap=token_account_map(tx);legs=[]
    for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
        current=None
        for ordinal,ix in enumerate(g.get("instructions") or []):
            p=_pid(ix,keys)
            if p in BY_PROGRAM:
                if current:legs.append(current)
                current={"venue":BY_PROGRAM[p],"program_id":p,"parent_index":g.get("index"),
                         "start_inner_ordinal":ordinal,"transfers":[]}
                continue
            if current and p in TOKEN_PROGRAMS:
                tr=parsed_transfer(ix,amap)
                if tr:current["transfers"].append(tr)
        if current:legs.append(current)
    for leg in legs:
        ins=[];outs=[]
        for tr in leg["transfers"]:
            if tr["source_owner"]==TARGET_WALLET:ins.append(tr)
            if tr["destination_owner"]==TARGET_WALLET:outs.append(tr)
        leg["wallet_inputs"]=ins;leg["wallet_outputs"]=outs
        if len(ins)==1 and len(outs)==1:
            leg["resolved"]=True
            leg["input_asset"]=ins[0]["mint"];leg["input_amount"]=ins[0]["amount"]
            leg["output_asset"]=outs[0]["mint"];leg["output_amount"]=outs[0]["amount"]
            leg["effective_output_per_input"]=outs[0]["amount"]/ins[0]["amount"]
        else:
            leg["resolved"]=False
            leg["resolution_reason"]="TARGET_OWNED_TRANSFER_EVIDENCE_NOT_UNIQUE"
    return legs

def analyze_target(tx,slot,block_time):
    keys=account_keys(tx);pids=program_ids(tx);m=(tx or {}).get("meta") or {}
    if TARGET_WALLET not in keys:return None
    sigs=((tx.get("transaction") or {}).get("signatures") or []);sig=str(sigs[0]) if sigs else ""
    failed=m.get("err") is not None
    venues=sorted({BY_PROGRAM[p] for p in pids if p in BY_PROGRAM})
    td=wallet_token_deltas(tx);sd=wallet_sol_delta(tx)
    nonanchor={k:v for k,v in td.items() if k not in ANCHORS and abs(v)>1e-9}
    anchor={ANCHORS[k]:v for k,v in td.items() if k in ANCHORS and abs(v)>1e-9}
    if sd is not None and abs(sd)>1e-12:anchor["SOL_NATIVE"]=sd
    legs=reconstruct_legs(tx)
    resolved=sum(bool(x.get("resolved")) for x in legs)
    return {
      "signature":sig,"slot":int(slot),"block_time":block_time,"failed":failed,"error":m.get("err"),
      "fee_lamports":m.get("fee"),"compute_units":m.get("computeUnitsConsumed"),
      "executor_present":TARGET_EXECUTOR in pids,"venues":venues,"dex_sequence":dex_sequence(tx),
      "wallet_token_deltas":td,"wallet_anchor_deltas":anchor,"wallet_nonanchor_deltas":nonanchor,
      "wallet_sol_delta":sd,"legs":legs,"resolved_legs":resolved,"leg_count":len(legs),
      "closed_anchor_cycle":bool((not failed) and not nonanchor and any(v>0 for v in anchor.values())),
      "execution_authority":False,
    }
