from __future__ import annotations
import base64,json,struct
from pathlib import Path

DISC=bytes([189,219,127,211,78,230,97,238])
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58(raw):
 n=int.from_bytes(raw,"big");s=""
 while n:n,r=divmod(n,58);s=ALPH[r]+s
 pad=len(raw)-len(raw.lstrip(b"\0"))
 return "1"*pad+(s or ("" if pad else "1"))

def decode(raw):
 if len(raw)<129 or raw[:8]!=DISC:return None
 o=8;mint=b58(raw[o:o+32]);o+=32
 sol,token=struct.unpack_from("<QQ",raw,o);o+=16
 is_buy=bool(raw[o]);o+=1
 user=b58(raw[o:o+32]);o+=32
 ts=struct.unpack_from("<q",raw,o)[0];o+=8
 vs,vt,rs,rt=struct.unpack_from("<QQQQ",raw,o)
 return {"mint":mint,"sol_amount_lamports":sol,"token_amount_raw":token,
  "is_buy":is_buy,"side":"BUY" if is_buy else "SELL","user":user,"timestamp":ts,
  "virtual_sol_reserves":vs,"virtual_token_reserves":vt,
  "real_sol_reserves":rs,"real_token_reserves":rt}

def events(tx):
 out=[]
 for line in ((tx or {}).get("meta") or {}).get("logMessages") or []:
  if not line.startswith("Program data: "):continue
  try:raw=base64.b64decode(line.split("Program data: ",1)[1])
  except Exception:continue
  d=decode(raw)
  if d:out.append(d)
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_trade_raw_transactions.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  ev=events(x.get("raw_transaction"))
  rows.append({"trade_id":x["trade_id"],"signature":x["signature"],
   "expected_side":x["side"],"token_address":x["token_address"],
   "event_count":len(ev),"events":ev,"execution_authority":False})
 return {"revision":"USLS_040","row_count":len(rows),
  "rows_with_trade_event":sum(1 for x in rows if x["event_count"]>0),
  "total_trade_events":sum(x["event_count"] for x in rows),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_events_exact.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
