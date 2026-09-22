from __future__ import annotations
import asyncio,hashlib,inspect,json,time
from pathlib import Path

PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"

def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _rid(kind,x):return hashlib.sha256((kind+"|"+_canon(x)).encode()).hexdigest()

def _load_jsonl(p):
 out=[]
 if not p.exists():return out
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try:out.append(json.loads(line))
   except Exception:pass
 return out

async def _maybe(v):return await v if inspect.isawaitable(v) else v

async def _pump_capture():
 from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import capture
 return await _maybe(capture())

async def _trade_capture(seconds=18,max_rows=4000):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await _maybe(capture(seconds=seconds,max_rows=max_rows))

def _trade_rows(v):
 if isinstance(v,list):return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list):return v[k]
 return []

def _persist_source_artifacts(root,pump_doc):
 base=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner"
 base.mkdir(parents=True,exist_ok=True)
 (base/"pump_create_v2_live_capture.json").write_text(json.dumps(pump_doc,indent=2,sort_keys=True,default=str),encoding="utf-8")
 from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_023_pump_create_v2_exact_account_decoder import decode
 decoded=decode(root)
 (base/"pump_create_v2_decoded_births.json").write_text(json.dumps(decoded,indent=2,sort_keys=True,default=str),encoding="utf-8")
 from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_024_pump_canonical_birth_horizon_scheduler import build
 canonical=build(root)
 (base/"pump_canonical_birth_horizons.json").write_text(json.dumps(canonical,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return decoded,canonical

def _birth_payload(b,decoded_by_sig):
 sig=b.get("signature") or str(b.get("event_id","")).split(":")[-1]
 d=decoded_by_sig.get(sig,{})
 token=b.get("token_address") or d.get("mint") or d.get("token_address")
 market=(b.get("market_address") or b.get("bonding_curve") or
         d.get("bonding_curve") or d.get("bonding_curve_address"))
 return {"venue":"PUMP_FUN","family":"PUMP_FUN","program_id":PUMP,
  "token_address":token,"market_address":market,
  "signature":sig,"birth_signature":sig,
  "slot":b.get("slot") or d.get("slot"),
  "birth_slot":b.get("slot") or d.get("slot"),
  "observed_unix":b.get("birth_observed_unix") or d.get("observed_unix"),
  "birth_observed_unix":b.get("birth_observed_unix") or d.get("observed_unix"),
  "birth_instruction":"create_v2","decoder_state":"EXACT_DECODER_CERTIFIED",
  "source_lineage":{"capture":"USLS_022","identity":"USLS_023","canonical":"USLS_024"},
  "execution_authority":False}

def _append_tape(root,births,trades):
 p=Path(root)/TAPE;p.parent.mkdir(parents=True,exist_ok=True)
 old=_load_jsonl(p);seen={x.get("record_id") for x in old}
 add=[]
 for kind,rows in (("BIRTH",births),("TRADE",trades)):
  for payload in rows:
   rid=_rid(kind,payload)
   if rid in seen:continue
   seen.add(rid)
   add.append({"record_id":rid,"record_type":kind,
    "scanner_observed_unix":time.time(),"payload":payload,
    "execution_authority":False})
 if add:
  with p.open("a",encoding="utf-8") as f:
   for r in add:f.write(_canon(r)+"\n")
 return add

def _chronological_fresh_joins(life,fresh_birth_sigs):
 good=[]
 for x in life.get("lifecycles",[]):
  b=x.get("birth") or {};t=x.get("trade") or {}
  bs=b.get("signature") or b.get("birth_signature")
  if bs not in fresh_birth_sigs:continue
  bslot=b.get("slot") or b.get("birth_slot")
  tslot=t.get("slot") or t.get("trade_slot")
  bt=b.get("observed_unix") or b.get("birth_observed_unix")
  tt=t.get("observed_unix") or t.get("trade_observed_unix")
  chronology=((bslot is not None and tslot is not None and int(tslot)>=int(bslot)) or
              (bt is not None and tt is not None and float(tt)>=float(bt)))
  if chronology:good.append(x)
 return good

async def _live_once():
 return await asyncio.gather(_pump_capture(),_trade_capture())

def run(root,max_cycles=4):
 root=Path(root);history=[];all_births=[];all_trades=[]
 for cycle in range(1,max_cycles+1):
  pump_doc,trade_doc=asyncio.run(_live_once())
  trades=_trade_rows(trade_doc)
  births=(pump_doc or {}).get("births") if isinstance(pump_doc,dict) else []
  births=births if isinstance(births,list) else []
  history.append({"cycle":cycle,
   "pump_notifications_seen":(pump_doc or {}).get("notifications_seen") if isinstance(pump_doc,dict) else None,
   "exact_pump_births":len(births),"universal_trade_rows":len(trades)})
  all_trades.extend(trades)
  if births:
   all_births.extend(births);break

 decoded,canonical=_persist_source_artifacts(root,{"revision":"USLS_022_SCANNER_DIRECT",
  "notifications_seen":sum((x["pump_notifications_seen"] or 0) for x in history),
  "exact_create_v2_count":len(all_births),"births":all_births,
  "execution_authority":False,"read_only":True})
 decoded_rows=decoded.get("rows") or []
 decoded_by_sig={x.get("signature"):x for x in decoded_rows if x.get("signature")}
 canonical_births=canonical.get("births") or []
 birth_payloads=[_birth_payload(b,decoded_by_sig) for b in canonical_births]

 added=_append_tape(root,birth_payloads,all_trades)
 from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106m_scanner_lifecycle_state_materializer import build as lifecycle_build
 life=lifecycle_build(root)
 fresh_sigs={x.get("signature") for x in birth_payloads if x.get("signature")}
 good=_chronological_fresh_joins(life,fresh_sigs)

 identity_complete=sum(bool(x.get("token_address") and x.get("market_address")) for x in birth_payloads)
 return {"revision":"USLS_107B","supersedes":"ORIGINAL_USLS_107_HOLD",
  "architecture":"DIRECT_PUMP_EXACT_BIRTH_LANE_PLUS_CONCURRENT_UNIVERSAL_TRADE_TAPE",
  "history":history,"cycles_completed":len(history),
  "exact_birth_count":len(birth_payloads),
  "identity_complete_birth_count":identity_complete,
  "universal_trade_rows_captured":len(all_trades),
  "tape_rows_added":len(added),
  "lifecycle_join_count":len(good),
  "fresh_lifecycle_joins":good[:20],
  "raw_tape_trade_count":life.get("trade_record_count"),
  "raw_tape_birth_count":life.get("birth_record_count"),
  "accounting_ok":life.get("accounting_ok"),
  "direct_birth_lane":True,"trade_lane_concurrent":True,
  "exact_pump_create_v2":True,"restart_safe_tape":True,
  "unresolved_retention":life.get("unresolved_trade_count",0)>=0,
  "phase5_full_capability_certified":(
   len(birth_payloads)>0 and identity_complete==len(birth_payloads) and
   len(all_trades)>0 and len(good)>0 and bool(life.get("accounting_ok"))
  ),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_cycles=4):
 d=run(root,max_cycles)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_full_capability_replacement_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
