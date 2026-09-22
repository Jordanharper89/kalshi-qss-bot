from __future__ import annotations
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

def cycle(root,discover_limit=20,max_live_hydrate=2,max_recovery_hydrate=1):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"program_indexed_confirmed_state.json"
 qp=base/"program_indexed_pending_signatures.json"
 ip=base/"program_indexed_confirmed_birth_inbox.json"
 state=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"anchors":{}}
 pendoc=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"pending":[]}
 inbox=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]}
 births=list(inbox.get("births") or []);seen={x["signature"] for x in births}
 pending={x["signature"]:x for x in pendoc.get("pending",[]) if x.get("signature") not in seen}
 anchors=dict(state.get("anchors") or {});discovered=0;rate_limited=False

 for pid in PROGRAMS:
  try:rows=_rpc("getSignaturesForAddress",[pid,{"commitment":"confirmed","limit":int(discover_limit)}],20.0) or []
  except HTTPError as e:
   if getattr(e,"code",None)==429:rate_limited=True;rows=[]
   else:raise
  if rows:anchors[pid]=rows[0].get("signature")
  for r in rows:
   sig=r.get("signature")
   if sig and sig not in seen and sig not in pending:
    pending[sig]={"signature":sig,"slot":int(r.get("slot") or 0),"program_seen":pid,
      "discovered_unix":time.time(),"attempts":0,"recovered_after_gap":False};discovered+=1

 live=sorted((x for x in pending.values() if not x.get("recovered_after_gap")),
             key=lambda x:(int(x.get("slot") or 0),x["signature"]),reverse=True)
 recovery=sorted((x for x in pending.values() if x.get("recovered_after_gap")),
                 key=lambda x:(int(x.get("slot") or 0),x["signature"]))
 selected=live[:int(max_live_hydrate)]+recovery[:int(max_recovery_hydrate)]
 selected_ids={x["signature"] for x in selected};hydrated=0;new=[]

 for row in selected:
  sig=row["signature"]
  try:
   tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except HTTPError as e:
   row["attempts"]=int(row.get("attempts") or 0)+1
   if getattr(e,"code",None)==429:rate_limited=True;continue
   raise
  hydrated+=1
  if not tx:continue
  pending.pop(sig,None)
  if ((tx.get("meta") or {}).get("err") is not None) or not _birth(tx):continue
  now=time.time();bt=tx.get("blockTime")
  b={"signature":sig,"slot":int(tx.get("slot") or row.get("slot") or 0),"block_time":bt,
     "observed_unix":now,"age_seconds":None if bt is None else max(0.0,now-float(bt)),
     "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
     "state":"CONFIRMED_BIRTH_CAPTURED","trigger_commitment":"confirmed",
     "recovered_after_gap":bool(row.get("recovered_after_gap")),"execution_authority":False}
  births.append(b);new.append(b);seen.add(sig)

 state={"revision":"SULS_067C","anchors":anchors,"last_cycle_unix":time.time(),
  "pending_signatures":len(pending),"live_pending":sum(not x.get("recovered_after_gap") for x in pending.values()),
  "recovery_pending":sum(bool(x.get("recovered_after_gap")) for x in pending.values()),
  "rate_limited_last_cycle":rate_limited,"restart_backfill_ready":bool(state.get("restart_backfill_ready")),
  "capture_policy":"LIVE_NEWEST_FIRST_RECOVERY_BACKGROUND",
  "retired_capture_paths":["SULS_057_HEAD_BLOCK_SCANNER","SULS_067_BURST_GETTRANSACTION","SULS_067B_OLDEST_FIRST"],
  "execution_authority":False}
 sp.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 qp.write_text(json.dumps({"revision":"SULS_067C","pending":list(pending.values()),
  "execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8")
 ip.write_text(json.dumps({"revision":"SULS_067C","birth_count":len(births),"births":births,
  "execution_authority":False,"read_only":True},indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"discovered":discovered,"hydrated":hydrated,"new_births":len(new),"total_births":len(births),
  "pending":len(pending),"live_pending":state["live_pending"],"recovery_pending":state["recovery_pending"],
  "anchor_count":len(anchors),"rate_limited":rate_limited}

