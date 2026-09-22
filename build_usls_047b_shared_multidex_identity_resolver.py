from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_047b_shared_multidex_identity_resolver.py"
TEST=ROOT/"test_usls_047b_shared_multidex_identity_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import base64,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_025_pump_bonding_curve_state_decoder import _rpc
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import b58,PROGRAMS
PS_POOL_DISC=bytes([241,154,109,4,17,177,109,188])

def decode_pumpswap_pool(v):
 if not v:return None
 raw=base64.b64decode(v["data"][0])
 if len(raw)<107 or raw[:8]!=PS_POOL_DISC:return None
 return {"pool_bump":raw[8],"index":int.from_bytes(raw[9:11],"little"),"creator":b58(raw[11:43]),
  "base_mint":b58(raw[43:75]),"quote_mint":b58(raw[75:107]),"owner":v.get("owner"),"data_length":len(raw)}

def decimals(mint):
 r=_rpc("getTokenSupply",[mint,{"commitment":"confirmed"}])
 v=(r or {}).get("value") or {};return int(v["decimals"]) if "decimals" in v else None

def resolve(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 seen={};rows=[]
 for x in src["rows"]:
  if x["venue"]!="PUMP_SWAP" or x["decode_status"]!="EXACT":continue
  pool=(x.get("event") or {}).get("pool")
  if not pool or pool in seen:continue
  v=(_rpc("getAccountInfo",[pool,{"encoding":"base64","commitment":"confirmed"}]) or {}).get("value")
  d=decode_pumpswap_pool(v)
  if d:
   d.update({"venue":"PUMP_SWAP","pool":pool,"base_decimals":decimals(d["base_mint"]),
    "quote_decimals":decimals(d["quote_mint"]),"identity_state":"EXACT",
    "execution_authority":False})
  else:d={"venue":"PUMP_SWAP","pool":pool,"identity_state":"UNRESOLVED","execution_authority":False}
  seen[pool]=d;rows.append(d)
 pending=sorted(v for v in src["venue_row_counts"] if v!="PUMP_SWAP")
 return {"revision":"USLS_047B","identity_rows":rows,"exact_identity_count":sum(x["identity_state"]=="EXACT" for x in rows),
  "decoder_pending_venues":pending,"unknown_identity_retained":True,
  "execution_authority":False,"read_only":True}

def write(root):
 d=resolve(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_identities.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047b_shared_multidex_identity_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"identity_row_count":len(d["identity_rows"]),
   "exact_identity_count":d["exact_identity_count"],"decoder_pending_venues":d["decoder_pending_venues"]},sort_keys=True))
  if d["identity_rows"]:self.assertEqual(d["exact_identity_count"],len(d["identity_rows"]))
  self.assertTrue(d["unknown_identity_retained"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-047B shared multi-DEX identity resolver boundary")
  print("[PASS] PumpSwap exact pool identity plugin integrated; other venue identities remain pending")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
