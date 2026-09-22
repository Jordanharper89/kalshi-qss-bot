from __future__ import annotations
import inspect,json,importlib.util

def _load_suls042(root):
 sub=root/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
 hits=sorted(sub.glob("suls_042*.py"))
 if not hits:raise RuntimeError("NO_SULS_042_MODULE_FOUND")
 for p in hits:
  spec=importlib.util.spec_from_file_location("_suls042_dynamic",p)
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  if hasattr(m,"_materialize"):return p,m
 raise RuntimeError("NO_SULS_042_MATERIALIZER_FOUND")

def audit(root):
 p,m=_load_suls042(root)
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 inbox=json.loads((b/"event_driven_birth_inbox.json").read_text(encoding="utf-8"))
 events=json.loads((b/"confirmed_tradeable_birth_events.json").read_text(encoding="utf-8"))
 births=list(inbox.get("births") or []);out=list(events.get("events") or [])
 def shape(x):
  env=x.get("envelope") or {};raw=env.get("raw_transaction") or {}
  tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
  return {"top_keys":sorted(x.keys()),"envelope_keys":sorted(env.keys()),
   "raw_keys":sorted(raw.keys()),"message_keys":sorted(msg.keys()),
   "meta_keys":sorted(meta.keys()),"account_keys_count":len(msg.get("accountKeys") or []),
   "log_count":len(meta.get("logMessages") or []),"signature":x.get("signature"),
   "token_address":x.get("token_address"),"pair_address":x.get("pair_address")}
 return {"revision":"SULS_099B","suls042_path":str(p.relative_to(root)).replace("\\","/"),
  "birth_count":len(births),"event_count":len(out),
  "birth_sample":shape(births[-1] if births else {}),
  "event_sample":shape(out[-1] if out else {}),
  "materializer_source":inspect.getsource(m._materialize),
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_identity_materialization_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
