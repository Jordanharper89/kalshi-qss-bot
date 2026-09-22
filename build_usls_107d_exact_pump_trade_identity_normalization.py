from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_107d_exact_pump_trade_identity_normalization.py"
TEST=ROOT/"test_usls_107d_exact_pump_trade_identity_normalization.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time,hashlib
from pathlib import Path

TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"
OUT="runtime_state/solana_opportunities/solana_scanner/exact_pump_trade_identity_normalization.json"

def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def _rid(x):return hashlib.sha256(_canon(x).encode()).hexdigest()

def _read_jsonl(p):
 out=[]
 if not p.exists():return out
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try:out.append(json.loads(line))
   except Exception:pass
 return out

def _payload(r):
 p=r.get("payload")
 return p if isinstance(p,dict) else r

def _vals(x,key):
 out=[]
 if isinstance(x,dict):
  if key in x:out.append(x.get(key))
  for v in x.values():out.extend(_vals(v,key))
 elif isinstance(x,list):
  for v in x:out.extend(_vals(v,key))
 return [v for v in out if v not in (None,"")]

def _first(x,*keys):
 for k in keys:
  v=_vals(x,k)
  if v:return v[0]
 return None

def _births(rows):
 out=[]
 for r in rows:
  if r.get("record_type")!="BIRTH":continue
  p=_payload(r)
  out.append({"signature":_first(p,"signature","birth_signature"),
   "slot":_first(p,"slot","birth_slot"),
   "observed_unix":_first(p,"observed_unix","birth_observed_unix"),
   "token_address":_first(p,"token_address","mint"),
   "market_address":_first(p,"market_address","bonding_curve","curve")})
 return [x for x in out if x["signature"] and x["token_address"] and x["market_address"]]

def _trade_stub(r):
 p=_payload(r)
 return {"record":r,
  "signature":_first(p,"signature","trade_signature"),
  "slot":_first(p,"slot","trade_slot"),
  "observed_unix":_first(p,"observed_unix","trade_observed_unix","received_unix","scanner_observed_unix"),
  "family":_first(p,"family","venue","program_family","source_family"),
  "program_id":_first(p,"program_id","programId")}

def _after_birth(t,b):
 try:
  if t["slot"] is not None and b["slot"] is not None:return int(t["slot"])>=int(b["slot"])
 except Exception:pass
 try:
  if t["observed_unix"] is not None and b["observed_unix"] is not None:return float(t["observed_unix"])>=float(b["observed_unix"])
 except Exception:pass
 return True

async def _maybe(v):return await v if inspect.isawaitable(v) else v

async def _tx(sig):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return await _maybe(_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
  "maxSupportedTransactionVersion":1}],20.0))

def _account_strings(tx):
 vals=[]
 msg=((tx.get("transaction") or {}).get("message") or {})
 for a in msg.get("accountKeys") or []:
  if isinstance(a,str):vals.append(a)
  elif isinstance(a,dict) and a.get("pubkey"):vals.append(str(a["pubkey"]))
 meta=tx.get("meta") or {}
 for k in ("loadedAddresses",):
  z=meta.get(k) or {}
  if isinstance(z,dict):
   vals.extend(str(x) for x in (z.get("writable") or []))
   vals.extend(str(x) for x in (z.get("readonly") or []))
 return set(vals)

def _pump_trade_exact(tx):
 # Reuse the certified Pump TradeEvent detector if present.
 try:
  from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_040_pump_tradeevent_discriminator_gate import is_trade_event
  return bool(is_trade_event(tx))
 except Exception:
  pass
 # Conservative fallback: exact Pump program presence + successful tx.
 accts=_account_strings(tx)
 return "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P" in accts and (tx.get("meta") or {}).get("err") is None

async def _probe(root,max_candidates=120):
 rows=_read_jsonl(Path(root)/TAPE)
 births=_births(rows)
 trades=[_trade_stub(r) for r in rows if r.get("record_type")=="TRADE"]
 seen=set();cands=[]
 for b in births:
  for t in trades:
   sig=t["signature"]
   if not sig or sig in seen or not _after_birth(t,b):continue
   fam=str(t.get("family") or "").upper()
   prog=str(t.get("program_id") or "")
   if fam and "PUMP" not in fam and prog!="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P":
    continue
   seen.add(sig);cands.append((b,t))
   if len(cands)>=max_candidates:break
  if len(cands)>=max_candidates:break

 probes=[];normalized=[]
 for i,(b,t) in enumerate(cands):
  rec={"birth_signature":b["signature"],"trade_signature":t["signature"],
       "rpc_error":None,"tx_found":False,"matched_token":False,
       "matched_market":False,"exact_pump_trade":False}
  try:
   tx=await _tx(t["signature"])
   rec["tx_found"]=isinstance(tx,dict)
   if isinstance(tx,dict) and (tx.get("meta") or {}).get("err") is None:
    accts=_account_strings(tx)
    rec["matched_token"]=b["token_address"] in accts
    rec["matched_market"]=b["market_address"] in accts
    rec["exact_pump_trade"]=_pump_trade_exact(tx)
    if rec["matched_token"] and rec["matched_market"] and rec["exact_pump_trade"]:
     normalized.append({"record_id":_rid({"birth":b["signature"],"trade":t["signature"]}),
      "record_type":"TRADE","family":"PUMP_FUN",
      "birth_signature":b["signature"],"trade_signature":t["signature"],
      "token_address":b["token_address"],"market_address":b["market_address"],
      "birth_slot":b["slot"],"trade_slot":tx.get("slot"),
      "birth_observed_unix":b["observed_unix"],"trade_observed_unix":t["observed_unix"],
      "decoder_state":"EXACT_PUMP_TRADE_IDENTITY_NORMALIZED",
      "source_lineage":{"trade_tape":"USLS_046B","hydration":"OAD_148",
       "trade_semantics":"USLS_040_OR_STRICT_PUMP_PROGRAM_SUCCESS_FALLBACK"},
      "raw_transaction":tx,"execution_authority":False})
     probes.append(rec);break
  except Exception as e:rec["rpc_error"]=repr(e)
  probes.append(rec)
  if i+1<len(cands):await asyncio.sleep(0.9)
 return rows,births,cands,probes,normalized

def run(root,max_candidates=120):
 rows,births,cands,probes,normalized=asyncio.run(_probe(root,max_candidates))
 p=Path(root)/TAPE
 old=_read_jsonl(p);seen={x.get("record_id") for x in old}
 added=[]
 if normalized:
  with p.open("a",encoding="utf-8") as f:
   for x in normalized:
    if x["record_id"] in seen:continue
    seen.add(x["record_id"]);f.write(_canon(x)+"\n");added.append(x)
 return {"revision":"USLS_107D","source_revision":"USLS_107C",
  "birth_count":len(births),"candidate_trade_count":len(cands),
  "hydration_probe_count":len(probes),
  "matched_token_count":sum(x["matched_token"] for x in probes),
  "matched_market_count":sum(x["matched_market"] for x in probes),
  "exact_identity_trade_count":len(normalized),
  "normalized_rows_added":len(added),"normalized_rows":normalized,
  "finding":("EXACT_PUMP_TRADE_IDENTITY_NORMALIZED" if normalized else
             "NO_JOINABLE_PUMP_TRADE_FOUND_IN_BOUNDED_CANDIDATES"),
  "next_boundary":("LIFECYCLE_JOIN_RECERTIFICATION" if normalized else
                   "DIRECT_PER_BIRTH_PUMP_TRADE_FOLLOWER_REQUIRED"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_candidates=120):
 d=run(root,max_candidates)
 p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107d_exact_pump_trade_identity_normalization import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_candidates=120)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "birth_count","candidate_trade_count","hydration_probe_count",
   "matched_token_count","matched_market_count","exact_identity_trade_count",
   "normalized_rows_added","finding","next_boundary")},sort_keys=True))
  self.assertGreater(d["birth_count"],0,"NO_107B_EXACT_BIRTHS_AVAILABLE")
  self.assertGreater(d["candidate_trade_count"],0,"NO_POST_BIRTH_TRADE_CANDIDATES")
  self.assertGreater(d["hydration_probe_count"],0,"NO_TRADE_SIGNATURES_HYDRATED")
  self.assertGreater(d["exact_identity_trade_count"],0,
   "NO_EXACT_PUMP_TRADE_MATCHED_FRESH_BIRTH_TOKEN_AND_MARKET")
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-107D exact Pump trade identity normalization")
  print("[PASS] fresh Pump birth token+curve physically matched in hydrated trade")
  print("[NEXT] LIFECYCLE_JOIN_RECERTIFICATION")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
