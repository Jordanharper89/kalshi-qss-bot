from __future__ import annotations
import json
from collections import Counter,defaultdict
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_027b_mriya_executor_aware_wallet_observer as obs

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_program_owned_pool_candidates.json")

def resolve():
    if not SRC.is_file(): raise SystemExit("[FAIL] run QARB-030 first")
    d=json.loads(SRC.read_text(encoding="utf-8"));rows=d.get("rows") or []
    accounts=sorted({a for r in rows for a in r.get("accounts",[])})
    info={}
    for i in range(0,len(accounts),100):
        chunk=accounts[i:i+100]
        vals=obs.rpc("getMultipleAccounts",[chunk,{"encoding":"base64","commitment":"confirmed"}]) or {}
        for a,v in zip(chunk,vals.get("value") or []):
            info[a]=None if v is None else {"owner":v.get("owner"),"lamports":v.get("lamports"),"space":v.get("space")}
    hit=defaultdict(lambda:{"occurrences":0,"mints":set(),"signatures":set(),"program_name":None,"program_id":None})
    for r in rows:
        pid=r["program_id"]
        for a in r.get("accounts",[]):
            x=info.get(a)
            if not x or x.get("owner")!=pid: continue
            h=hit[a];h["occurrences"]+=1;h["program_name"]=r["program_name"];h["program_id"]=pid
            h["mints"].update(r.get("mints") or []);h["signatures"].add(r["signature"])
    out=[]
    for a,h in hit.items():
        out.append({"address":a,"program_name":h["program_name"],"program_id":h["program_id"],
                    "occurrences":h["occurrences"],"mints":sorted(h["mints"]),
                    "transactions":len(h["signatures"]),"account":info.get(a)})
    out.sort(key=lambda x:(-x["occurrences"],x["program_name"],x["address"]))
    payload={"candidate_accounts":len(out),"rows":out,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-031] MRIYA PROGRAM-OWNED DEX STATE CANDIDATES")
    r=resolve();c=Counter(x["program_name"] for x in r["rows"])
    print("[CANDIDATES]",r["candidate_accounts"],json.dumps(dict(c),sort_keys=True))
    for x in r["rows"][:30]:
        print("[STATE_CANDIDATE] venue=%s hits=%d tx=%d account=%s mints=%s"%(
            x["program_name"],x["occurrences"],x["transactions"],x["address"][:16],[m[:10] for m in x["mints"]]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
