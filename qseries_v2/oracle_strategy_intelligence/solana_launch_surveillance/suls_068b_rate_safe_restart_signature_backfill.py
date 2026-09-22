from __future__ import annotations
import json,time
from urllib.error import HTTPError
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067b_rate_safe_program_indexed_confirmed_birth_worker import PROGRAMS

def recover(root,page_limit=100,max_pages=3):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"program_indexed_confirmed_state.json"
 qp=base/"program_indexed_pending_signatures.json"
 state=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"anchors":{}}
 pending_doc=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"pending":[]}
 pending={x["signature"]:x for x in pending_doc.get("pending",[]) if x.get("signature")}
 anchors=dict(state.get("anchors") or {})
 recovered=0;queried=0;rate_limited=False;new_anchors={}

 for pid in PROGRAMS:
  previous=anchors.get(pid)
  before=None
  for _ in range(max(1,int(max_pages))):
   opts={"commitment":"confirmed","limit":int(page_limit)}
   if before:opts["before"]=before
   try:
    rows=_rpc("getSignaturesForAddress",[pid,opts],25.0) or []
   except HTTPError as e:
    if getattr(e,"code",None)==429:
     rate_limited=True;break
    raise
   queried+=len(rows)
   if not rows:break
   if pid not in new_anchors:new_anchors[pid]=rows[0].get("signature")
   stop=False
   for r in rows:
    sig=r.get("signature")
    if not sig:continue
    if previous and sig==previous:
     stop=True;break
    if sig not in pending:
     pending[sig]={"signature":sig,"slot":int(r.get("slot") or 0),"program_seen":pid,
                   "discovered_unix":time.time(),"attempts":0,"recovered_after_gap":True}
     recovered+=1
   if stop or len(rows)<int(page_limit):break
   before=rows[-1].get("signature")
   if not before:break

 if new_anchors:
  anchors.update(new_anchors)
 state.update({"revision":"SULS_068B","anchors":anchors,"last_recovery_unix":time.time(),
               "restart_backfill_ready":True,"rate_limited_last_recovery":rate_limited,
               "pending_signatures":len(pending),"execution_authority":False})
 sp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 qp.write_text(json.dumps({"revision":"SULS_068B","pending":list(pending.values()),
   "execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8")
 return {"queried_signatures":queried,"recovered_signatures":recovered,
         "pending_signatures":len(pending),"restart_backfill_ready":True,
         "anchor_count":len(anchors),"rate_limited":rate_limited}

