from __future__ import annotations
import inspect,json
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance import suls_042_native_birth_materialization as m

def audit(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 inbox=json.loads((b/"event_driven_birth_inbox.json").read_text(encoding="utf-8"))
 events=json.loads((b/"confirmed_tradeable_birth_events.json").read_text(encoding="utf-8"))
 births=list(inbox.get("births") or [])
 out_events=list(events.get("events") or [])

 def shape(x):
  if not x:return {}
  env=x.get("envelope") or {}
  raw=env.get("raw_transaction") or {}
  tx=raw.get("transaction") or {}
  msg=tx.get("message") or {}
  meta=raw.get("meta") or {}
  return {
   "top_keys":sorted(x.keys()),
   "envelope_keys":sorted(env.keys()),
   "raw_keys":sorted(raw.keys()),
   "message_keys":sorted(msg.keys()),
   "meta_keys":sorted(meta.keys()),
   "account_keys_type":type(msg.get("accountKeys")).__name__,
   "account_keys_count":len(msg.get("accountKeys") or []),
   "log_count":len(meta.get("logMessages") or []),
   "signature":x.get("signature"),
   "token_address":x.get("token_address"),
   "pair_address":x.get("pair_address"),
  }

 return {
  "revision":"SULS_099",
  "birth_count":len(births),
  "event_count":len(out_events),
  "birth_sample":shape(births[-1] if births else {}),
  "event_sample":shape(out_events[-1] if out_events else {}),
  "materializer_source":inspect.getsource(m._materialize),
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_identity_materialization_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
