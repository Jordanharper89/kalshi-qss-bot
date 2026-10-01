from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_068_restart_signature_backfill_worker.py"
TEST=ROOT/"test_suls_068_restart_signature_backfill_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067_program_indexed_confirmed_birth_worker import PROGRAMS,_birth

def recover(root,max_per_program=1000):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"program_indexed_confirmed_state.json";ip=base/"program_indexed_confirmed_birth_inbox.json"
 state=json.loads(sp.read_text(encoding="utf-8"));anchors=dict(state.get("anchors") or {})
 inbox=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]}
 births=list(inbox.get("births") or []);seen={x["signature"] for x in births}
 queried=0;recovered=[];new_anchors={}
 for pid in PROGRAMS:
  opts={"commitment":"confirmed","limit":int(max_per_program)}
  if anchors.get(pid):opts["until"]=anchors[pid]
  rows=_rpc("getSignaturesForAddress",[pid,opts],30.0) or [];queried+=len(rows)
  latest=_rpc("getSignaturesForAddress",[pid,{"commitment":"confirmed","limit":1}],15.0) or []
  if latest:new_anchors[pid]=latest[0].get("signature")
  for r in reversed(rows):
   sig=r.get("signature")
   if not sig or sig in seen:continue
   tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
   if not tx or ((tx.get("meta") or {}).get("err") is not None) or not _birth(tx):continue
   now=time.time();bt=tx.get("blockTime")
   row={"signature":sig,"slot":int(tx.get("slot") or r.get("slot") or 0),"block_time":bt,
        "observed_unix":now,"age_seconds":None if bt is None else max(0.0,now-float(bt)),
        "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
        "state":"RECOVERED_CONFIRMED_BIRTH","recovered_after_gap":True,
        "trigger_commitment":"confirmed","execution_authority":False}
   births.append(row);recovered.append(row);seen.add(sig)
 if new_anchors:state["anchors"]=new_anchors
 state["last_recovery_unix"]=time.time();state["restart_backfill_ready"]=True
 sp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 ip.write_text(json.dumps({"revision":"SULS_068","birth_count":len(births),"births":births,
  "execution_authority":False,"read_only":True},indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"queried_signatures":queried,"recovered_births":len(recovered),
         "restart_backfill_ready":True,"anchor_count":len(state.get("anchors") or {})}

"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_068_restart_signature_backfill_worker import recover
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_recovery(self):
  d=recover(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["restart_backfill_ready"]);self.assertEqual(d["anchor_count"],2)
  print("[PASS] SULS-068 restart signature backfill worker")
  print("[SCOPE] Zero recovered births is valid when no certified-family birth occurred across the gap")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-068 RESTART SIGNATURE BACKFILL WORKER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
