from __future__ import annotations
import json
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_meteora_birth_detector.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for b in d.get("births",[]):
  sig=b["signature"]
  try:
   tx=_rpc("getTransaction",[sig,{"commitment":"finalized","encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
   finalized=bool(tx)
  except Exception:finalized=False
  rows.append({"signature":sig,"confirmed_observed":True,"finalized_observed":finalized,
   "lineage_state":"FINALIZED_CONFIRMED" if finalized else "AWAITING_FINALIZATION",
   "execution_authority":False})
 return {"revision":"SULS_055","row_count":len(rows),"rows":rows,
  "execution_authority":False,"read_only":True,
  "scope":"Confirmed trigger remains non-final until finalized readback succeeds"}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_to_finalized_lineage.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
