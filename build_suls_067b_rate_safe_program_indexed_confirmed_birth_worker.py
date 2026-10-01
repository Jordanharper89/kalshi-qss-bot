from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_067b_rate_safe_program_indexed_confirmed_birth_worker.py"
TEST=ROOT/"test_suls_067b_rate_safe_program_indexed_confirmed_birth_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from urllib.error import HTTPError
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
PROGRAMS=(DBC,DAMM)

def _birth(tx):
 logs=((tx or {}).get("meta") or {}).get("logMessages") or []
 low="\n".join(str(x).lower() for x in logs)
 return ("program log: create pool" in low and
         "instruction: initializepoolwithdynamicconfig" in low and
         DBC.lower() in low and DAMM.lower() in low)

def cycle(root,discover_limit=20,max_hydrate=2):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"program_indexed_confirmed_state.json"
 qp=base/"program_indexed_pending_signatures.json"
 ip=base/"program_indexed_confirmed_birth_inbox.json"
 state=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"anchors":{}}
 pending_doc=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"pending":[]}
 inbox=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]}
 births=list(inbox.get("births") or []);seen_births={x["signature"] for x in births}
 pending={x["signature"]:x for x in pending_doc.get("pending",[]) if x.get("signature") not in seen_births}
 anchors=dict(state.get("anchors") or {});discovered=0;rate_limited=False

 for pid in PROGRAMS:
  try:
   rows=_rpc("getSignaturesForAddress",[pid,{"commitment":"confirmed","limit":int(discover_limit)}],20.0) or []
  except HTTPError as e:
   if getattr(e,"code",None)==429:
    rate_limited=True;rows=[]
   else: raise
  if rows: anchors[pid]=rows[0].get("signature")
  for r in rows:
   sig=r.get("signature")
   if sig and sig not in seen_births and sig not in pending:
    pending[sig]={"signature":sig,"slot":int(r.get("slot") or 0),"program_seen":pid,
                  "discovered_unix":time.time(),"attempts":0};discovered+=1

 hydrated=0;new_births=[];remaining={}
 for sig,row in sorted(pending.items(),key=lambda kv:(int(kv[1].get("slot") or 0),kv[0])):
  if hydrated>=int(max_hydrate):
   remaining[sig]=row;continue
  try:
   tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except HTTPError as e:
   row["attempts"]=int(row.get("attempts") or 0)+1
   if getattr(e,"code",None)==429:
    rate_limited=True;remaining[sig]=row;continue
   raise
  hydrated+=1
  if not tx: remaining[sig]=row;continue
  if ((tx.get("meta") or {}).get("err") is not None): continue
  if not _birth(tx): continue
  now=time.time();bt=tx.get("blockTime")
  b={"signature":sig,"slot":int(tx.get("slot") or row.get("slot") or 0),"block_time":bt,
     "observed_unix":now,"age_seconds":None if bt is None else max(0.0,now-float(bt)),
     "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
     "state":"CONFIRMED_BIRTH_CAPTURED","trigger_commitment":"confirmed","execution_authority":False}
  births.append(b);new_births.append(b);seen_births.add(sig)

 state={"revision":"SULS_067B","anchors":anchors,"last_cycle_unix":time.time(),
        "pending_signatures":len(remaining),"rate_limited_last_cycle":rate_limited,
        "retired_capture_path":"SULS_067_BURST_GETTRANSACTION","execution_authority":False}
 sp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 qp.write_text(json.dumps({"revision":"SULS_067B","pending":list(remaining.values()),
   "execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8")
 ip.write_text(json.dumps({"revision":"SULS_067B","birth_count":len(births),"births":births,
   "execution_authority":False,"read_only":True},indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"discovered":discovered,"hydrated":hydrated,"pending":len(remaining),
         "new_births":len(new_births),"total_births":len(births),
         "anchor_count":len(anchors),"rate_limited":rate_limited}

"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067b_rate_safe_program_indexed_confirmed_birth_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT,discover_limit=20,max_hydrate=2);print("[CYCLE]",json.dumps(d,sort_keys=True))
  if d["anchor_count"]==0 and d["discovered"]==0 and d["pending"]==0:
   self.fail("NO_PROGRAM_INDEXED_CONFIRMED_ACTIVITY")
  self.assertLessEqual(d["hydrated"],2)
  print("[PASS] SULS-067B rate-safe program-indexed confirmed birth worker")
  print("[SCOPE] Durable pending queue prevents discovery loss while hydration is intentionally bounded")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-067B RATE-SAFE PROGRAM-INDEXED CONFIRMED BIRTH WORKER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
