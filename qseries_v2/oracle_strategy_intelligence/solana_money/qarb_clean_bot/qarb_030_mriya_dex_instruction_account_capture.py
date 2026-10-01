from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_027b_mriya_executor_aware_wallet_observer as obs
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_028b_mriya_executor_flow_decoder as dec

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")
FLOW=Path("runtime_state/qseries/qarb_clean_bot/mriya_route_decode.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")

def _pid(ix,keys):
    if ix.get("programId"): return ix["programId"]
    i=ix.get("programIdIndex")
    return keys[i] if isinstance(i,int) and 0<=i<len(keys) else None

def _accounts(ix,keys):
    out=[]
    for a in ix.get("accounts") or []:
        if isinstance(a,str): out.append(a)
        elif isinstance(a,int) and 0<=a<len(keys): out.append(keys[a])
    return out

def capture():
    if not SRC.is_file(): raise SystemExit("[FAIL] run QARB-027B first")
    if not FLOW.is_file(): raise SystemExit("[FAIL] run QARB-028B first")
    src=json.loads(SRC.read_text(encoding="utf-8"))
    flows={x["signature"]:x for x in json.loads(FLOW.read_text(encoding="utf-8")).get("rows",[])}
    reg=dec.registry();rows=[];errors=[]
    sigs=[x["signature"] for x in src.get("rows",[]) if x.get("signature") and not x.get("error")]
    for n,sig in enumerate(sigs,1):
        try:
            tx=obs.rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
            if not tx: raise RuntimeError("EMPTY_TRANSACTION")
            keys=obs.keys(tx); msg=((tx.get("transaction") or {}).get("message") or {})
            groups=[("TOP",msg.get("instructions") or [])]
            groups += [("INNER:%s"%g.get("index"),g.get("instructions") or []) for g in ((tx.get("meta") or {}).get("innerInstructions") or [])]
            for level,grp in groups:
                for j,ix in enumerate(grp):
                    if not isinstance(ix,dict): continue
                    pid=_pid(ix,keys);name=reg.get(pid)
                    if not name or not any(k in name for k in ("PUMP","METEORA","RAYDIUM","ORCA")): continue
                    f=flows.get(sig,{})
                    rows.append({"signature":sig,"slot":tx.get("slot"),"level":level,"ix_index":j,
                                 "program_id":pid,"program_name":name,"accounts":_accounts(ix,keys),
                                 "mints":sorted(set((f.get("mint_deltas") or {}).keys()))})
        except Exception as e: errors.append({"signature":sig,"error":type(e).__name__+":"+str(e)})
        if n<len(sigs): time.sleep(.10)
    payload={"target":obs.TARGET,"executor":obs.EXECUTOR,"instruction_rows":len(rows),
             "errors":errors,"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-030] MRIYA DEX INSTRUCTION ACCOUNT CAPTURE")
    r=capture()
    from collections import Counter
    c=Counter(x["program_name"] for x in r["rows"])
    print("[PROGRAMS]",json.dumps(dict(c),sort_keys=True))
    print("[RESULT] instruction_rows=%d errors=%d"%(r["instruction_rows"],len(r["errors"])))
    for x in r["rows"][:20]:
        print("[DEX_IX] slot=%s venue=%s accounts=%d mints=%s"%(
            x["slot"],x["program_name"],len(x["accounts"]),[m[:10] for m in x["mints"]]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
