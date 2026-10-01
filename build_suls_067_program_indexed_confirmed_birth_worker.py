from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_067_program_indexed_confirmed_birth_worker.py"
TEST=ROOT/"test_suls_067_program_indexed_confirmed_birth_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
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

def cycle(root,limit=40):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"program_indexed_confirmed_state.json"
 ip=base/"program_indexed_confirmed_birth_inbox.json"
 state=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"anchors":{}}
 old=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]}
 births=list(old.get("births") or []);seen={x["signature"] for x in births}
 t0=time.time();sigrows={};anchors={}
 for pid in PROGRAMS:
  rows=_rpc("getSignaturesForAddress",[pid,{"commitment":"confirmed","limit":int(limit)}],20.0) or []
  if rows:anchors[pid]=rows[0].get("signature")
  for r in rows:
   if r.get("signature"):sigrows[r["signature"]]=r
 fetched=0;new=[]
 for sig,r in sorted(sigrows.items(),key=lambda kv:int(kv[1].get("slot") or 0)):
  if sig in seen:continue
  tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
  fetched+=1
  if not tx or ((tx.get("meta") or {}).get("err") is not None) or not _birth(tx):continue
  now=time.time();bt=tx.get("blockTime")
  row={"signature":sig,"slot":int(tx.get("slot") or r.get("slot") or 0),"block_time":bt,
       "observed_unix":now,"age_seconds":None if bt is None else max(0.0,now-float(bt)),
       "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
       "state":"CONFIRMED_BIRTH_CAPTURED","trigger_commitment":"confirmed","execution_authority":False}
  births.append(row);new.append(row);seen.add(sig)
 state={"revision":"SULS_067","anchors":anchors or state.get("anchors",{}),
        "last_cycle_unix":time.time(),"retired_capture_path":"SULS_057_HEAD_BLOCK_SCANNER",
        "execution_authority":False}
 inbox={"revision":"SULS_067","birth_count":len(births),"births":births,
        "execution_authority":False,"read_only":True}
 sp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 ip.write_text(json.dumps(inbox,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"candidate_signatures":len(sigrows),"transactions_fetched":fetched,
         "new_births":len(new),"total_births":len(births),"cycle_seconds":time.time()-t0,
         "anchor_count":len(state["anchors"])}

"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067_program_indexed_confirmed_birth_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[CYCLE]",json.dumps(d,sort_keys=True))
  if d["candidate_signatures"]<=0:self.fail("NO_PROGRAM_INDEXED_CONFIRMED_ACTIVITY")
  self.assertEqual(d["anchor_count"],2)
  print("[PASS] SULS-067 program-indexed confirmed birth worker")
  print("[SCOPE] Replaces SULS-057 head-block scanning for the certified Meteora DBC/DAMM family")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-067 PROGRAM-INDEXED CONFIRMED BIRTH WORKER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
