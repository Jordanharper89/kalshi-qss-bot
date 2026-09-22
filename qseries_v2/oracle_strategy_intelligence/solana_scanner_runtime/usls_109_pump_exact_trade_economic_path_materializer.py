from __future__ import annotations
import json,math
from pathlib import Path

TAPE="runtime_state/solana_opportunities/solana_scanner/raw_birth_trade_tape.jsonl"

def _rows(p):
 out=[]
 if not p.exists():return out
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():
   try:out.append(json.loads(line))
   except Exception:pass
 return out

def _payload(r):
 p=r.get("payload")
 return p if isinstance(p,dict) else r

def _key_index(tx):
 msg=((tx.get("transaction") or {}).get("message") or {})
 out=[]
 for a in msg.get("accountKeys") or []:
  if isinstance(a,str):out.append(a)
  elif isinstance(a,dict):out.append(a.get("pubkey"))
 la=(tx.get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):
  out += la.get("writable") or []
  out += la.get("readonly") or []
 return out

def _token_delta(tx,mint):
 meta=tx.get("meta") or {};pre=meta.get("preTokenBalances") or [];post=meta.get("postTokenBalances") or []
 def amt(x):
  u=(x.get("uiTokenAmount") or {}).get("amount")
  try:return int(u)
  except Exception:return 0
 by={}
 for x in pre:
  if x.get("mint")==mint:by[x.get("accountIndex")]=by.get(x.get("accountIndex"),0)-amt(x)
 for x in post:
  if x.get("mint")==mint:by[x.get("accountIndex")]=by.get(x.get("accountIndex"),0)+amt(x)
 vals=[abs(v) for v in by.values() if v]
 return max(vals) if vals else 0

def _mint_decimals(tx,mint):
 for x in ((tx.get("meta") or {}).get("postTokenBalances") or [])+((tx.get("meta") or {}).get("preTokenBalances") or []):
  if x.get("mint")==mint:
   try:return int((x.get("uiTokenAmount") or {}).get("decimals"))
   except Exception:return None
 return None

def _market_lamport_delta(tx,market):
 keys=_key_index(tx);meta=tx.get("meta") or {}
 try:i=keys.index(market)
 except ValueError:return None
 pre=meta.get("preBalances") or [];post=meta.get("postBalances") or []
 if i>=len(pre) or i>=len(post):return None
 return int(post[i])-int(pre[i])

def run(root):
 rows=_rows(Path(root)/TAPE);out=[]
 for r in rows:
  if r.get("record_type")!="TRADE":continue
  p=_payload(r)
  if p.get("decoder_state")!="EXACT_PUMP_TRADEEVENT_IDENTITY_NORMALIZED":continue
  tx=p.get("raw_transaction") or {}
  mint=p.get("token_address");market=p.get("market_address")
  raw_token=_token_delta(tx,mint);dec=_mint_decimals(tx,mint)
  lam=_market_lamport_delta(tx,market)
  token_qty=(raw_token/(10**dec)) if raw_token and dec is not None else None
  sol_qty=(abs(lam)/1_000_000_000) if lam not in (None,0) else None
  price=(sol_qty/token_qty) if token_qty not in (None,0) and sol_qty is not None else None
  out.append({"family":"PUMP_FUN","token_address":mint,"market_address":market,
   "birth_signature":p.get("birth_signature"),"trade_signature":p.get("trade_signature") or p.get("signature"),
   "trade_slot":p.get("trade_slot") or p.get("slot"),
   "trade_observed_unix":p.get("trade_observed_unix"),
   "side":p.get("side") or "UNKNOWN","base_quantity":token_qty,"quote_quantity":sol_qty,
   "effective_price":price,"price_method":"CURVE_LAMPORT_DELTA_OVER_TOKEN_BALANCE_DELTA",
   "economic_state":"PRICE_AVAILABLE" if price is not None and math.isfinite(price) and price>0 else "PRICE_UNAVAILABLE",
   "source_lineage":p.get("source_lineage"),"execution_authority":False})
 return {"revision":"USLS_109","input_trade_count":len(out),
  "priced_trade_count":sum(x["effective_price"] is not None for x in out),
  "rows":out,"price_semantics":"OBSERVATIONAL_EFFECTIVE_PRICE_PROXY_NOT_EXECUTABLE_PNL",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/pump_exact_trade_economic_path.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
