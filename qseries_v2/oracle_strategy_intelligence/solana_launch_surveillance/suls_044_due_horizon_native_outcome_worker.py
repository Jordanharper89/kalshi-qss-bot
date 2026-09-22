from __future__ import annotations
import json,time
from decimal import Decimal
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

def D(x):
 try:return Decimal(str(x))
 except Exception:return None

def bal(a):
 r=_rpc("getTokenAccountBalance",[str(a),{"commitment":"finalized"}],20.0)
 return ((r or {}).get("value") or {}).get("uiAmountString")

def run(root,now=None,max_due=8):
 now=float(time.time() if now is None else now)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 qp=base/"fresh_birth_horizon_queue.json"
 q=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"queue":[]}
 op=base/"native_horizon_outcomes.json"
 old=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"outcomes":[]}
 outcomes=list(old.get("outcomes") or []);done={(x["event_id"],x["horizon_seconds"]) for x in outcomes};processed=0
 for row in q.get("queue",[]):
  k=(row["event_id"],row["horizon_seconds"])
  if k in done:row["state"]="MATURED";continue
  if row.get("state")!="PENDING" or now<float(row["target_unix"]) or processed>=max_due:continue
  ta=D(bal(row["token_vault"]));qa=D(bal(row["quote_vault"]))
  bta=D(row["birth_token_amount"]);bqa=D(row["birth_quote_amount"])
  ratio=(qa/ta) if ta and qa and ta!=0 else None
  br=(bqa/bta) if bta and bqa and bta!=0 else None
  ret=((ratio/br)-1) if ratio is not None and br not in (None,0) else None
  outcomes.append({"event_id":row["event_id"],"horizon_seconds":row["horizon_seconds"],
   "target_unix":row["target_unix"],"observed_unix":now,"token_reserve":None if ta is None else str(ta),
   "quote_reserve":None if qa is None else str(qa),"quote_per_token":None if ratio is None else str(ratio),
   "return_from_birth":None if ret is None else str(ret),"execution_authority":False})
  row["state"]="MATURED";processed+=1;done.add(k)
 qp.write_text(json.dumps(q,indent=2,sort_keys=True),encoding="utf-8")
 out={"revision":"SULS_044","outcome_count":len(outcomes),"new_outcomes":processed,"outcomes":outcomes,
  "execution_authority":False,"read_only":True}
 op.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
