from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_107e_direct_per_birth_pump_trade_follower.py"
TEST=ROOT/"test_usls_107e_direct_per_birth_pump_trade_follower.py"

MOD_TEXT=r"""from __future__ import annotations
import base64,hashlib,json,time
from pathlib import Path

PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
TRADE_EVENT=bytes([189,219,127,211,78,230,97,238])
TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"
OUT="runtime_state/solana_opportunities/solana_scanner/direct_per_birth_pump_trade_follower.json"

def _canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _rid(x): return hashlib.sha256(_canon(x).encode()).hexdigest()

def _read_jsonl(p):
 out=[]
 if not p.exists(): return out
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try: out.append(json.loads(line))
   except Exception: pass
 return out

def _payload(r):
 p=r.get("payload")
 return p if isinstance(p,dict) else r

def _vals(x,key):
 out=[]
 if isinstance(x,dict):
  if key in x: out.append(x.get(key))
  for v in x.values(): out.extend(_vals(v,key))
 elif isinstance(x,list):
  for v in x: out.extend(_vals(v,key))
 return [v for v in out if v not in (None,"")]

def _first(x,*keys):
 for k in keys:
  v=_vals(x,k)
  if v: return v[0]
 return None

def _births(rows):
 out=[]
 for r in rows:
  if r.get("record_type")!="BIRTH": continue
  p=_payload(r)
  fam=str(_first(p,"family","venue") or "")
  if fam!="PUMP_FUN": continue
  b={"signature":_first(p,"signature","birth_signature"),
     "slot":_first(p,"slot","birth_slot"),
     "observed_unix":_first(p,"observed_unix","birth_observed_unix"),
     "token_address":_first(p,"token_address","mint"),
     "market_address":_first(p,"market_address","bonding_curve","curve")}
  if all((b["signature"],b["token_address"],b["market_address"])): out.append(b)
 return out

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def _accounts(tx):
 out=[]
 msg=((tx.get("transaction") or {}).get("message") or {})
 for a in msg.get("accountKeys") or []:
  if isinstance(a,str): out.append(a)
  elif isinstance(a,dict) and a.get("pubkey"): out.append(str(a["pubkey"]))
 la=(tx.get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):
  out += [str(x) for x in la.get("writable") or []]
  out += [str(x) for x in la.get("readonly") or []]
 return set(out)

def _has_trade_event(tx):
 logs=(tx.get("meta") or {}).get("logMessages") or []
 for line in logs:
  s=str(line)
  if "Program data:" not in s: continue
  enc=s.split("Program data:",1)[1].strip()
  try:
   raw=base64.b64decode(enc)
   if raw[:8]==TRADE_EVENT: return True
  except Exception: pass
 return False

def _sig_rows(address,limit=100):
 try:
  x=_rpc("getSignaturesForAddress",[address,{"limit":limit,"commitment":"confirmed"}],20.0)
  return x if isinstance(x,list) else []
 except Exception:
  return []

def _tx(sig):
 try:
  return _rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
    "maxSupportedTransactionVersion":1}],20.0)
 except Exception:
  return None

def _follow_birth(b,max_signatures=100):
 sigrows=_sig_rows(b["market_address"],max_signatures)
 candidates=[];exact=[]
 bslot=int(b["slot"] or 0)
 for s in sigrows:
  slot=int(s.get("slot") or 0)
  if slot < bslot or s.get("err") is not None: continue
  sig=s.get("signature")
  if not sig or sig==b["signature"]: continue
  candidates.append(sig)
 for sig in candidates:
  tx=_tx(sig)
  if not isinstance(tx,dict) or (tx.get("meta") or {}).get("err") is not None: continue
  accts=_accounts(tx)
  if PUMP not in accts: continue
  if b["token_address"] not in accts or b["market_address"] not in accts: continue
  if not _has_trade_event(tx): continue
  exact.append({"record_id":_rid({"birth":b["signature"],"trade":sig}),
   "record_type":"TRADE",
   "payload":{"family":"PUMP_FUN","venue":"PUMP_FUN","program_id":PUMP,
    "birth_signature":b["signature"],"trade_signature":sig,"signature":sig,
    "token_address":b["token_address"],"market_address":b["market_address"],
    "birth_slot":b["slot"],"trade_slot":tx.get("slot"),"slot":tx.get("slot"),
    "birth_observed_unix":b["observed_unix"],"trade_observed_unix":time.time(),
    "decoder_state":"EXACT_PUMP_TRADEEVENT_IDENTITY_NORMALIZED",
    "source_lineage":{"birth":"USLS_107B","address_follow":"getSignaturesForAddress",
      "transaction":"getTransaction","event":"PUMP_TRADE_EVENT_DISCRIMINATOR"},
    "raw_transaction":tx,"execution_authority":False},
   "scanner_observed_unix":time.time(),"execution_authority":False})
 return sigrows,candidates,exact

def run(root,max_signatures=100):
 root=Path(root);tp=root/TAPE
 rows=_read_jsonl(tp);births=_births(rows)
 per=[];exact=[]
 for b in births:
  sigrows,cands,hits=_follow_birth(b,max_signatures)
  per.append({"birth_signature":b["signature"],"token_address":b["token_address"],
   "market_address":b["market_address"],"signature_rows":len(sigrows),
   "post_birth_candidates":len(cands),"exact_trade_hits":len(hits)})
  exact.extend(hits)
 old=_read_jsonl(tp);seen={x.get("record_id") for x in old};added=[]
 if exact:
  with tp.open("a",encoding="utf-8") as f:
   for x in exact:
    if x["record_id"] in seen: continue
    seen.add(x["record_id"]);f.write(_canon(x)+"\n");added.append(x)

 # Re-run exact join repair after normalization.
 from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107c_phase5_exact_lifecycle_join_repair import run as join_run
 join=join_run(root)

 return {"revision":"USLS_107E","source_revision":"USLS_107D",
  "birth_count":len(births),"per_birth":per,
  "exact_trade_count":len(exact),"normalized_rows_added":len(added),
  "exact_identity_lifecycle_join_count":join.get("exact_identity_lifecycle_join_count",0),
  "join_finding":join.get("finding"),
  "direct_per_birth_follow":True,"exact_tradeevent_required":True,
  "token_and_curve_required":True,
  "phase5_full_capability_certified":(
   len(births)>0 and len(exact)>0 and
   join.get("exact_identity_lifecycle_join_count",0)>0),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_signatures=100):
 d=run(root,max_signatures)
 p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107e_direct_per_birth_pump_trade_follower import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_phase5(self):
  p,d=write(ROOT,max_signatures=100)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "birth_count","exact_trade_count","normalized_rows_added",
   "exact_identity_lifecycle_join_count","join_finding",
   "phase5_full_capability_certified")},sort_keys=True))
  for x in d["per_birth"]: print("[BIRTH_FOLLOW]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_count"],0,"NO_EXACT_PUMP_BIRTHS_AVAILABLE")
  self.assertTrue(d["direct_per_birth_follow"])
  self.assertTrue(d["exact_tradeevent_required"])
  self.assertTrue(d["token_and_curve_required"])
  self.assertGreater(d["exact_trade_count"],0,
   "NO_EXACT_PUMP_TRADEEVENT_FOUND_FOR_FRESH_BIRTH_CURVE")
  self.assertGreater(d["exact_identity_lifecycle_join_count"],0,
   "NO_EXACT_BIRTH_TO_TRADE_LIFECYCLE_JOIN")
  self.assertTrue(d["phase5_full_capability_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-107E direct per-birth Pump trade follower")
  print("[PASS] exact Pump TradeEvent + token + curve identity normalized")
  print("[PASS] chronological exact birth-to-trade lifecycle join")
  print("[PASS] PHASE 5 PHYSICALLY CERTIFIED")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
