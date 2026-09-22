from __future__ import annotations
import asyncio,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
WS="wss://api.mainnet-beta.solana.com";RPC="https://api.mainnet-beta.solana.com"
DISC=hashlib.sha256(b"global:create_v2").digest()[:8]

def b58decode(s):
 n=0
 for c in s:n=n*58+ALPHABET.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def _keys(tx):
 out=[]
 for k in (((tx.get("transaction") or {}).get("message") or {}).get("accountKeys") or []):
  out.append(k.get("pubkey") if isinstance(k,dict) else k)
 return out

def _pump_ix(tx):
 keys=_keys(tx);msg=((tx.get("transaction") or {}).get("message") or {})
 groups=[(None,x) for x in msg.get("instructions") or []]
 for g in (tx.get("meta") or {}).get("innerInstructions") or []:
  groups += [(g.get("index"),x) for x in g.get("instructions") or []]
 out=[]
 for parent,ix in groups:
  pid=ix.get("programId")
  if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):pid=keys[ix["programIdIndex"]]
  if pid!=PUMP:continue
  raw=b58decode(ix.get("data") or "")
  if raw[:8]!=DISC:continue
  ac=ix.get("accounts") or [];resolved=[keys[a] if isinstance(a,int) and a<len(keys) else a for a in ac]
  out.append({"accounts":resolved,"data":ix.get("data"),"inner_parent_index":parent})
 return out

def _tx(sig):
 delay=.75
 for attempt in range(1,6):
  body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
  req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except urllib.error.HTTPError as e:
   if e.code!=429:raise
  if attempt<5:time.sleep(delay);delay=min(delay*2,6)
 return None

async def capture(seconds=35,max_hits=3):
 import websockets
 req={"jsonrpc":"2.0","id":1,"method":"logsSubscribe","params":[{"mentions":[PUMP]},{"commitment":"confirmed"}]}
 hits=[];seen=set();notes=0
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  await ws.send(json.dumps(req));deadline=time.time()+seconds
  while time.time()<deadline and len(hits)<max_hits:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if m.get("method")!="logsNotification":continue
   notes+=1;res=((m.get("params") or {}).get("result") or {});v=res.get("value") or {}
   sig=v.get("signature");logs=v.get("logs") or []
   if not sig or sig in seen or v.get("err") is not None:continue
   low=" ".join(str(x).lower() for x in logs)
   if "instruction: create" not in low:continue
   seen.add(sig);tx=_tx(sig)
   if not tx:continue
   exact=_pump_ix(tx)
   if exact:hits.append({"signature":sig,"slot":(res.get("context") or {}).get("slot"),
    "observed_unix":time.time(),"block_time":tx.get("blockTime"),"instructions":exact,"raw_transaction":tx})
 return {"revision":"USLS_022","notifications_seen":notes,"exact_create_v2_count":len(hits),
  "create_v2_discriminator_hex":DISC.hex(),"births":hits,"execution_authority":False,"read_only":True}

def write(root):
 d=asyncio.run(capture());p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_live_capture.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
