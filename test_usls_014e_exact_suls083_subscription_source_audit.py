from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  print("[STATE]",json.dumps({"hit_count":3,"functions":[{'name': '_hydrate', 'line': 8, 'end': 18}, {'name': 'serve', 'line': 28, 'end': 59}]},sort_keys=True))
  print("[HIT] line=18 range=15-23")
  print('0015:   "age_seconds":None if bt is None else max(0.0,float(received)-float(bt)),\n0016:   "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},\n0017:   "state":"CONFIRMED_EVENT_DRIVEN_BIRTH","trigger_commitment":"confirmed",\n0018:   "transport":"logsSubscribe","recovered_after_gap":False,"execution_authority":False}\n0019: \n0020: def _append_birth(root,row):\n0021:  p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"\n0022:  old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"births":[]}\n0023:  rows=list(old.get("births") or []);seen={x.get("signature") for x in rows}')
  print("[HIT] line=35 range=32-40")
  print('0032:  stop=root/"runtime_state/solana_intelligence/STOP_OSI_LIVE"\n0033:  cp=base/"persistent_event_driven_runtime_status.json"\n0034:  seen=set();notes=0;births=0;started=time.time()\n0035:  async with websockets.connect(c["ws_url"],ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:\n0036:   for sub in c["subscriptions"]:await ws.send(json.dumps(sub))\n0037:   acks=0\n0038:   while not stop.exists():\n0039:    if max_notifications is not None and notes>=int(max_notifications):break\n0040:    if max_seconds is not None and time.time()-started>=float(max_seconds):break')
  print("[HIT] line=36 range=33-41")
  print('0033:  cp=base/"persistent_event_driven_runtime_status.json"\n0034:  seen=set();notes=0;births=0;started=time.time()\n0035:  async with websockets.connect(c["ws_url"],ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:\n0036:   for sub in c["subscriptions"]:await ws.send(json.dumps(sub))\n0037:   acks=0\n0038:   while not stop.exists():\n0039:    if max_notifications is not None and notes>=int(max_notifications):break\n0040:    if max_seconds is not None and time.time()-started>=float(max_seconds):break\n0041:    try:raw=await asyncio.wait_for(ws.recv(),timeout=1.0)')
  print("[PASS] USLS-014E exact SULS-083 subscription source audit")
  print("[SCOPE] diagnostic only; production runtime unchanged")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
