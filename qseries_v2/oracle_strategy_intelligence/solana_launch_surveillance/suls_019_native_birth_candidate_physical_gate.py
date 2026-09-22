from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_017_live_native_transaction_program_scan import write as scan_write
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_018_native_pool_birth_candidate_decoder import write as decode_write

def run(root,attempts=5):
 observed=[];total_tx=0
 for i in range(max(1,int(attempts))):
  _,s=scan_write(root);total_tx+=int(s.get("transaction_count",0))
  _,d=decode_write(root)
  for x in d.get("candidates",[]):
   key=(x.get("slot"),x.get("signature"))
   if key not in {(y.get("slot"),y.get("signature")) for y in observed}:observed.append(x)
  if observed:break
  if i+1<attempts:time.sleep(1.0)
 return {"revision":"SULS_019","attempts":i+1,"transactions_examined":total_tx,
  "candidate_count":len(observed),"candidates":observed,
  "physical_candidate_observed":bool(observed),"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_candidate_physical_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
