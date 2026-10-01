from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_075_physical_confirmed_logs_subscription_probe.py"
TEST=ROOT/"test_suls_075_physical_confirmed_logs_subscription_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time

async def probe(root,max_messages=6,timeout_seconds=12.0):
 import websockets
 c=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json").read_text(encoding="utf-8"))
 ws_url=c["ws_url"];acks=[];notes=[];t0=time.time()
 async with websockets.connect(ws_url,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  for sub in c["subscriptions"]:
   await ws.send(json.dumps(sub))
  deadline=time.monotonic()+float(timeout_seconds)
  while time.monotonic()<deadline and len(notes)<int(max_messages):
   remain=max(0.1,deadline-time.monotonic())
   try:raw=await asyncio.wait_for(ws.recv(),timeout=remain)
   except asyncio.TimeoutError:break
   msg=json.loads(raw)
   if "id" in msg and "result" in msg:
    acks.append({"id":msg["id"],"subscription":msg["result"]});continue
   if msg.get("method")=="logsNotification":
    v=(((msg.get("params") or {}).get("result") or {}).get("value") or {})
    ctx=(((msg.get("params") or {}).get("result") or {}).get("context") or {})
    notes.append({"slot":ctx.get("slot"),"signature":v.get("signature"),"err":v.get("err"),
      "logs":v.get("logs") or [],"received_unix":time.time()})
 return {"revision":"SULS_075","connected":True,"ack_count":len(acks),"notification_count":len(notes),
  "acks":acks,"notifications":notes,"elapsed_seconds":time.time()-t0,
  "execution_authority":False,"read_only":True}

def run(root):
 d=asyncio.run(probe(root))
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_confirmed_logs_subscription_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_075_physical_confirmed_logs_subscription_probe import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=run(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="notifications"},sort_keys=True))
  for n in d["notifications"][:6]:
   print("[NOTIFICATION]",json.dumps({"slot":n["slot"],"signature":n["signature"],"err":n["err"],"log_count":len(n["logs"])},sort_keys=True))
  if not d["connected"] or d["ack_count"]<2:self.fail("CONFIRMED_LOGS_SUBSCRIPTION_NOT_ACKNOWLEDGED")
  if d["notification_count"]<1:self.fail("NO_PHYSICAL_LOGS_NOTIFICATION")
  print("[PASS] SULS-075 physical confirmed logsSubscribe probe")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-075 PHYSICAL CONFIRMED LOGS SUBSCRIPTION PROBE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
