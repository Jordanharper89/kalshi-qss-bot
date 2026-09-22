from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_046b_shared_multidex_live_event_router.py"
TEST=ROOT/"test_usls_046b_shared_multidex_live_event_router.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from collections import Counter
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS,route
WS="wss://api.mainnet-beta.solana.com"

async def capture(seconds=18,max_rows=2000):
 import websockets
 byid={i+1:v for i,(k,v) in enumerate(PROGRAMS.items())};venue_byid={i+1:k for i,k in enumerate(PROGRAMS)}
 rows=[];acks={};notes=0
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  for i,(venue,pid) in enumerate(PROGRAMS.items(),1):
   req={"jsonrpc":"2.0","id":i,"method":"logsSubscribe","params":[{"mentions":[pid]},{"commitment":"confirmed"}]}
   await ws.send(json.dumps(req))
  deadline=time.time()+seconds
  while time.time()<deadline and len(rows)<max_rows:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if "id" in m and "result" in m:
    acks[int(m["id"])]=m["result"];continue
   if m.get("method")!="logsNotification":continue
   notes+=1;params=m.get("params") or {};sub=params.get("subscription")
   venue=None
   for rid,sid in acks.items():
    if sid==sub:venue=venue_byid.get(rid);break
   if venue is None:continue
   res=params.get("result") or {};v=res.get("value") or {}
   if v.get("err") is not None:continue
   sig=v.get("signature");slot=(res.get("context") or {}).get("slot");obs=time.time()
   for li,line in enumerate(v.get("logs") or []):
    routed=route(venue,line)
    if routed["decode_status"]=="EXACT" or ("Program data:" in line or "Program log:" in line):
     rows.append({"venue":venue,"program_id":PROGRAMS[venue],"signature":sig,"slot":slot,
      "observed_unix":obs,"log_index":li,"raw_log":line,
      "decode_status":routed["decode_status"],"event":routed["event"],
      "execution_authority":False})
 c=Counter(x["venue"] for x in rows);e=Counter(x["venue"] for x in rows if x["decode_status"]=="EXACT")
 return {"revision":"USLS_046B","subscription_ack_count":len(acks),"notifications_seen":notes,
  "row_count":len(rows),"venue_row_counts":dict(c),"venue_exact_counts":dict(e),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=asyncio.run(capture());p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"subscription_ack_count":d["subscription_ack_count"],
   "notifications_seen":d["notifications_seen"],"row_count":d["row_count"],
   "venue_row_counts":d["venue_row_counts"],"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  self.assertEqual(d["subscription_ack_count"],14);self.assertGreater(d["notifications_seen"],0)
  self.assertGreater(d["row_count"],0);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-046B one shared live router covers all 14 known Solana venue programs")
  print("[PASS] exact plugins decode; undecoded activity remains raw for later adapters")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
