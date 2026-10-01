from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import PUMP,_tx
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162g_pump_fun_live_direct_decoder import decode
async def capture(root,seconds=75,max_sigs=40):
 import websockets
 req={"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[PUMP]},{"commitment":"confirmed"}]}
 hits=[];seen=set()
 async with websockets.connect("wss://api.mainnet-beta.solana.com",ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  await ws.send(json.dumps(req));deadline=time.time()+seconds
  while time.time()<deadline and len(hits)<max_sigs:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if m.get("method")!="logsNotification":continue
   res=((m.get("params") or {}).get("result") or {});v=res.get("value") or {};sig=v.get("signature")
   if not sig or sig in seen or v.get("err") is not None:continue
   seen.add(sig);hits.append({"signature":sig,"observed_unix":time.time()})
 rows=[];hydrated=0
 for h in hits:
  tx=_tx(h["signature"])
  if not tx:continue
  hydrated+=1;rows+=decode(root,h["signature"],tx,h["observed_unix"])
 return {"revision":"USLS_162H","signature_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_live_economic_row_count":len(rows),"market_count":len({str(x["market_address"]) for x in rows}),
  "rows":rows,"next_boundary":"FREEZE_PUMP_FUN_PROSPECTIVE_COHORT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=asyncio.run(capture(root));p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/pump_fun_strict_live_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
