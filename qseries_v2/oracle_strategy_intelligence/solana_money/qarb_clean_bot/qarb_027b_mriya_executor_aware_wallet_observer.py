from __future__ import annotations
import json,os,time,urllib.request
from pathlib import Path
TARGET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
EXECUTOR="AN225ykGPAmckE9uMCCM7jQv3L3AYwiPZbHqgMUYEgCR"
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")
def rpc(method,params,attempts=6):
    err=None
    for i in range(attempts):
        try:
            body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
            req=urllib.request.Request(RPC,data=body,headers={"content-type":"application/json"})
            with urllib.request.urlopen(req,timeout=25) as r:j=json.loads(r.read())
            if j.get("error"):raise RuntimeError("RPC "+json.dumps(j["error"],sort_keys=True))
            return j.get("result")
        except Exception as e:
            err=e;time.sleep(min(2.5,.20*(2**i)))
    raise err
def keys(tx):
    msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
    for k in msg.get("accountKeys") or []:
        if isinstance(k,str):out.append(k)
        elif isinstance(k,dict) and k.get("pubkey"):out.append(k["pubkey"])
    la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
    return out+list(la.get("writable") or [])+list(la.get("readonly") or [])
def programs(tx):
    ks=keys(tx);ids=set();msg=((tx or {}).get("transaction") or {}).get("message") or {}
    groups=[msg.get("instructions") or []]+[g.get("instructions") or [] for g in (((tx or {}).get("meta") or {}).get("innerInstructions") or [])]
    for grp in groups:
        for ix in grp:
            if not isinstance(ix,dict):continue
            if ix.get("programId"):ids.add(ix["programId"])
            elif isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):ids.add(ks[ix["programIdIndex"]])
    return sorted(ids)
def token_rows(meta):
    out=[]
    for side,name in ((meta.get("preTokenBalances") or [],"pre"),(meta.get("postTokenBalances") or [],"post")):
        for x in side:
            try:amt=float((x.get("uiTokenAmount") or {}).get("uiAmountString") or 0)
            except Exception:amt=0.0
            out.append({"side":name,"account_index":x.get("accountIndex"),"owner":x.get("owner"),"mint":x.get("mint"),"amount":amt})
    return out
def observe(limit=40):
    sigs=rpc("getSignaturesForAddress",[TARGET,{"limit":int(limit),"commitment":"confirmed"}]) or [];rows=[]
    for n,s in enumerate(sigs,1):
        sig=s.get("signature")
        if not sig:continue
        try:
            tx=rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
            if not tx:raise RuntimeError("EMPTY_TRANSACTION")
            meta=tx.get("meta") or {};ks=keys(tx);bal={}
            for who in (TARGET,EXECUTOR):
                try:i=ks.index(who)
                except ValueError:i=-1
                pre=meta.get("preBalances") or [];post=meta.get("postBalances") or []
                bal[who]=None if i<0 or i>=len(pre) or i>=len(post) else (post[i]-pre[i])/1e9
            rows.append({"signature":sig,"slot":tx.get("slot"),"block_time":tx.get("blockTime"),"err":meta.get("err"),
                         "fee_lamports":meta.get("fee"),"account_keys":ks,"sol_deltas":bal,
                         "token_balance_rows":token_rows(meta),"program_ids":programs(tx)})
        except Exception as e:rows.append({"signature":sig,"error":type(e).__name__+":"+str(e)})
        if n<len(sigs):time.sleep(.12)
    payload={"target":TARGET,"executor":EXECUTOR,"count":len(rows),"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");return payload
def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--limit",type=int,default=40);a=ap.parse_args(argv)
    print("[QARB-027B] MRIYA EXECUTOR-AWARE NATIVE OBSERVER");print("[TARGET]",TARGET);print("[EXECUTOR]",EXECUTOR)
    r=observe(a.limit);ok=[x for x in r["rows"] if not x.get("error")]
    print("[RESULT] transactions=%d decoded=%d errors=%d"%(len(r["rows"]),len(ok),len(r["rows"])-len(ok)))
    for x in ok[:12]:print("[TX] slot=%s target_sol=%s executor_sol=%s token_rows=%d programs=%d sig=%s"%(x.get("slot"),x["sol_deltas"].get(TARGET),x["sol_deltas"].get(EXECUTOR),len(x.get("token_balance_rows") or []),len(x.get("program_ids") or []),x["signature"][:16]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
