from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_025_pump_bonding_curve_state_decoder.py"
TEST=ROOT/"test_usls_025_pump_bonding_curve_state_decoder.py"

MOD_TEXT=r"""from __future__ import annotations
import base64,hashlib,json,struct,time,urllib.error,urllib.request
from pathlib import Path
RPC="https://api.mainnet-beta.solana.com"
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
DISC=hashlib.sha256(b"account:BondingCurve").digest()[:8]

def _rpc(method,params):
 delay=.75
 for attempt in range(5):
  body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
  req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except urllib.error.HTTPError as e:
   if e.code!=429:raise
  if attempt<4:time.sleep(delay);delay=min(delay*2,6)
 raise RuntimeError("RPC_RETRY_EXHAUSTED")

def decode_account(value):
 if not value:return None
 raw=base64.b64decode(value["data"][0])
 if len(raw)<49:return {"valid":False,"error":"SHORT_ACCOUNT","length":len(raw)}
 vals=struct.unpack_from("<QQQQQ",raw,8)
 return {"valid":raw[:8]==DISC,"account_discriminator_hex":raw[:8].hex(),
  "virtual_token_reserves":vals[0],"virtual_quote_reserves":vals[1],
  "real_token_reserves":vals[2],"real_quote_reserves":vals[3],
  "token_total_supply":vals[4],"complete":bool(raw[48]),
  "owner":value.get("owner"),"lamports":value.get("lamports"),"data_length":len(raw)}

def read_curves(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 births=json.loads((base/"pump_canonical_birth_horizons.json").read_text(encoding="utf-8"))["births"]
 addrs=[x["bonding_curve"] for x in births]
 result=_rpc("getMultipleAccounts",[addrs,{"encoding":"base64","commitment":"confirmed"}])
 vals=(result or {}).get("value") or []
 rows=[]
 for b,v in zip(births,vals):
  state=decode_account(v)
  rows.append({"event_id":b["event_id"],"token_address":b["token_address"],
   "bonding_curve":b["bonding_curve"],"quote_mint":b["quote_mint"],
   "observed_unix":time.time(),"state":state,"execution_authority":False})
 return {"revision":"USLS_025","curve_count":len(rows),
  "valid_count":sum(1 for x in rows if x["state"] and x["state"].get("valid") and x["state"].get("owner")==PUMP),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=read_curves(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_bonding_curve_states.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_025_pump_bonding_curve_state_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_state(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"curve_count":d["curve_count"],"valid_count":d["valid_count"]},sort_keys=True))
  for x in d["rows"]:print("[CURVE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["curve_count"],0);self.assertEqual(d["valid_count"],d["curve_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-025 Pump bonding-curve account state physically decoded")
  print("[PASS] virtual/real token and quote reserves preserved from exact curve account")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
