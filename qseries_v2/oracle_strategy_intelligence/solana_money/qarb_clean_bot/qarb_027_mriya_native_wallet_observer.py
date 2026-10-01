from __future__ import annotations
import json, os, time, urllib.request
from pathlib import Path

TARGET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")

def rpc(method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"content-type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        j=json.loads(r.read())
    if j.get("error"): raise RuntimeError("RPC "+json.dumps(j["error"],sort_keys=True))
    return j.get("result")

def _keys(tx):
    msg=((tx or {}).get("transaction") or {}).get("message") or {}
    out=[]
    for k in msg.get("accountKeys") or []:
        if isinstance(k,str): out.append(k)
        elif isinstance(k,dict): out.append(k.get("pubkey"))
    la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
    out += list(la.get("writable") or []) + list(la.get("readonly") or [])
    return [x for x in out if x]

def _program_ids(tx):
    keys=_keys(tx); msg=((tx or {}).get("transaction") or {}).get("message") or {}
    ids=set()
    for ix in msg.get("instructions") or []:
        if isinstance(ix,dict):
            if ix.get("programId"): ids.add(ix["programId"])
            elif isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):
                ids.add(keys[ix["programIdIndex"]])
    for group in (((tx or {}).get("meta") or {}).get("innerInstructions") or []):
        for ix in group.get("instructions") or []:
            if ix.get("programId"): ids.add(ix["programId"])
            elif isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):
                ids.add(keys[ix["programIdIndex"]])
    return sorted(ids)

def _token_map(rows):
    d={}
    for x in rows or []:
        if x.get("owner")!=TARGET: continue
        mint=x.get("mint")
        ui=(x.get("uiTokenAmount") or {}).get("uiAmountString")
        try: amt=float(ui or 0)
        except Exception: amt=0.0
        d[mint]=d.get(mint,0.0)+amt
    return d

def observe(limit=40):
    sigs=rpc("getSignaturesForAddress",[TARGET,{"limit":int(limit),"commitment":"confirmed"}]) or []
    rows=[]
    for s in sigs:
        sig=s.get("signature")
        if not sig: continue
        try:
            tx=rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
        except Exception as exc:
            rows.append({"signature":sig,"error":type(exc).__name__+":"+str(exc)}); continue
        if not tx: continue
        keys=_keys(tx); meta=tx.get("meta") or {}
        try: wi=keys.index(TARGET)
        except ValueError: wi=-1
        pre=(meta.get("preBalances") or []); post=(meta.get("postBalances") or [])
        sol_delta=None
        if wi>=0 and wi<len(pre) and wi<len(post): sol_delta=(post[wi]-pre[wi])/1e9
        a=_token_map(meta.get("preTokenBalances")); b=_token_map(meta.get("postTokenBalances"))
        mints=sorted(set(a)|set(b))
        td={m:round(b.get(m,0)-a.get(m,0),12) for m in mints if abs(b.get(m,0)-a.get(m,0))>0}
        rows.append({"signature":sig,"slot":tx.get("slot"),"block_time":tx.get("blockTime"),
                     "err":meta.get("err"),"fee_lamports":meta.get("fee"),
                     "wallet_sol_delta":sol_delta,"wallet_token_deltas":td,
                     "program_ids":_program_ids(tx)})
        time.sleep(.05)
    payload={"target":TARGET,"count":len(rows),"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--limit",type=int,default=40); a=ap.parse_args(argv)
    print("[QARB-027] MRIYA NATIVE WALLET OBSERVER")
    print("[TARGET]",TARGET)
    print("[RPC] confirmed signatures + confirmed jsonParsed transactions")
    r=observe(a.limit)
    ok=[x for x in r["rows"] if not x.get("error")]
    print("[RESULT] transactions=%d decoded=%d errors=%d"%(len(r["rows"]),len(ok),len(r["rows"])-len(ok)))
    for x in ok[:12]:
        print("[TX] slot=%s sol=%s tokens=%s programs=%d sig=%s"%(
            x.get("slot"),x.get("wallet_sol_delta"),x.get("wallet_token_deltas"),
            len(x.get("program_ids") or []),x["signature"][:16]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
