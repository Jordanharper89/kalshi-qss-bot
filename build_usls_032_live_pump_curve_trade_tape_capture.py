from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_032_live_pump_curve_trade_tape_capture.py"
TEST=ROOT/"test_usls_032_live_pump_curve_trade_tape_capture.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import capture as capture_birth
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_023_pump_create_v2_exact_account_decoder import decode
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _tx,_keys
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_031_pump_exact_trade_discriminator_registry import PUMP,classify

WS="wss://api.mainnet-beta.solana.com"

def _pump_instructions(tx):
 keys=_keys(tx);msg=((tx.get("transaction") or {}).get("message") or {})
 groups=[(i,x) for i,x in enumerate(msg.get("instructions") or [])]
 for g in (tx.get("meta") or {}).get("innerInstructions") or []:
  groups += [(g.get("index"),x) for x in g.get("instructions") or []]
 out=[]
 for idx,ix in groups:
  pid=ix.get("programId")
  if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):pid=keys[ix["programIdIndex"]]
  if pid!=PUMP:continue
  c=classify(ix.get("data") or "")
  out.append({"instruction_index":idx,"data":ix.get("data"),**c})
 return out

async def run(root,seconds=30,max_trades=120):
 import websockets
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 cap=await capture_birth(seconds=35,max_hits=1)
 (base/"pump_create_v2_live_capture.json").write_text(json.dumps(cap,indent=2,sort_keys=True),encoding="utf-8")
 dec=decode(root)
 if not dec["rows"]:raise RuntimeError("NO_EXACT_PUMP_BIRTH_DECODED")
 b=dec["rows"][0];curve=b["bonding_curve"];born=b["observed_unix"]
 req={"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[curve]},{"commitment":"confirmed"}]}
 rows=[];seen=set();notes=0
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  await ws.send(json.dumps(req));deadline=time.time()+seconds
  while time.time()<deadline and len(rows)<max_trades:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if m.get("method")!="logsNotification":continue
   notes+=1;res=((m.get("params") or {}).get("result") or {});v=res.get("value") or {}
   sig=v.get("signature")
   if not sig or sig in seen or v.get("err") is not None:continue
   seen.add(sig);tx=_tx(sig)
   if not tx:continue
   for ix in _pump_instructions(tx):
    if ix["side"]=="UNKNOWN_TRADE_TYPE":continue
    rows.append({"signature":sig,"slot":(res.get("context") or {}).get("slot"),
     "block_time":tx.get("blockTime"),"observed_unix":time.time(),
     "birth_observed_unix":born,"token_address":b["mint"],"market_address":curve,
     "quote_mint":b["quote_mint"],**ix})
 return {"revision":"USLS_032","token_address":b["mint"],"market_address":curve,
  "notifications_seen":notes,"trade_instruction_count":len(rows),
  "buy_count":sum(1 for x in rows if x["side"]=="BUY"),
  "sell_count":sum(1 for x in rows if x["side"]=="SELL"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=asyncio.run(run(root));p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_live_curve_trade_capture.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_032_live_pump_curve_trade_tape_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("token_address","market_address","notifications_seen","trade_instruction_count","buy_count","sell_count")},sort_keys=True))
  for x in d["rows"][:50]:print("[TRADE_IX]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["notifications_seen"],0)
  self.assertGreater(d["trade_instruction_count"],0)
  self.assertEqual(d["trade_instruction_count"],d["buy_count"]+d["sell_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-032 prospective live Pump curve-specific trade tape captured")
  print("[PASS] exact BUY/SELL instructions captured after exact newborn-token birth")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
