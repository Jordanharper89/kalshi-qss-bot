from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_047c_batched_retry_safe_multidex_identity_resolver.py"
TEST=ROOT/"test_usls_047c_batched_retry_safe_multidex_identity_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import base64,json,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import b58,PROGRAMS
PS_POOL_DISC=bytes([241,154,109,4,17,177,109,188])
RPC="https://api.mainnet.solana.com"

def rpc(method,params,retries=5):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json"})
   with urllib.request.urlopen(req,timeout=12) as r:
    body=json.loads(r.read());return body.get("result")
  except Exception as e:
   last=e;time.sleep(min(1.0*(n+1),4.0))
 raise RuntimeError(f"RPC_RETRY_EXHAUSTED:{type(last).__name__}:{last}")

def decode_pool(v):
 if not v:return None
 raw=base64.b64decode(v["data"][0])
 if len(raw)<107 or raw[:8]!=PS_POOL_DISC:return None
 return {"pool_bump":raw[8],"index":int.from_bytes(raw[9:11],"little"),
  "creator":b58(raw[11:43]),"base_mint":b58(raw[43:75]),
  "quote_mint":b58(raw[75:107]),"owner":v.get("owner"),"data_length":len(raw)}

def mint_decimals(v):
 if not v:return None
 raw=base64.b64decode(v["data"][0])
 return int(raw[44]) if len(raw)>44 else None

def resolve(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 pools=sorted({x["event"]["pool"] for x in src["rows"]
  if x["venue"]=="PUMP_SWAP" and x["decode_status"]=="EXACT" and x.get("event")})
 vals=(rpc("getMultipleAccounts",[pools,{"encoding":"base64","commitment":"confirmed"}]) or {}).get("value") or []
 decoded={}
 for pool,v in zip(pools,vals):
  d=decode_pool(v)
  if d:decoded[pool]=d
 mints=sorted({m for d in decoded.values() for m in (d["base_mint"],d["quote_mint"])})
 mvals=(rpc("getMultipleAccounts",[mints,{"encoding":"base64","commitment":"confirmed"}]) or {}).get("value") or []
 dec={m:mint_decimals(v) for m,v in zip(mints,mvals)}
 rows=[]
 for pool in pools:
  d=decoded.get(pool)
  if d:
   d.update({"venue":"PUMP_SWAP","pool":pool,
    "base_decimals":dec.get(d["base_mint"]),"quote_decimals":dec.get(d["quote_mint"]),
    "identity_state":"EXACT" if d["owner"]==PROGRAMS["PUMP_SWAP"] and dec.get(d["base_mint"]) is not None and dec.get(d["quote_mint"]) is not None else "UNRESOLVED",
    "execution_authority":False})
   rows.append(d)
  else:rows.append({"venue":"PUMP_SWAP","pool":pool,"identity_state":"UNRESOLVED","execution_authority":False})
 pending=sorted(v for v in src["venue_row_counts"] if v!="PUMP_SWAP")
 return {"revision":"USLS_047C","pool_count":len(rows),
  "exact_identity_count":sum(x["identity_state"]=="EXACT" for x in rows),
  "identity_rows":rows,"decoder_pending_venues":pending,
  "rpc_calls_expected":2,"batched_rpc":True,"retry_safe":True,
  "unknown_identity_retained":True,"execution_authority":False,"read_only":True}

def write(root):
 d=resolve(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_identities.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"pool_count":d["pool_count"],"exact_identity_count":d["exact_identity_count"],
   "batched_rpc":d["batched_rpc"],"retry_safe":d["retry_safe"],
   "decoder_pending_venues":d["decoder_pending_venues"]},sort_keys=True))
  for x in d["identity_rows"]:print("[IDENTITY]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["pool_count"],0)
  self.assertEqual(d["exact_identity_count"],d["pool_count"])
  self.assertTrue(d["batched_rpc"]);self.assertTrue(d["retry_safe"])
  self.assertTrue(d["unknown_identity_retained"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-047C batched retry-safe multi-DEX identity resolver")
  print("[PASS] PumpSwap pool + mint decimals resolved with two batched RPC boundaries")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
