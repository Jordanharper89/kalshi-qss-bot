from __future__ import annotations
import json,struct
from pathlib import Path

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PROGRAM="MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG"
EVENT_DISC=bytes([228,69,165,46,81,203,154,29,189,219,127,211,78,230,97,238])

def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def b58e(b):
 n=int.from_bytes(b,"big");s=""
 while n:
  n,r=divmod(n,58);s=ALPH[r]+s
 z=0
 for x in b:
  if x==0:z+=1
  else:break
 return "1"*z+(s or "")

def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])

def mint_decimals(tx,mint):
 ks=keys(tx)
 for n in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(n) or []:
   if x.get("mint")==mint:
    return int((x.get("uiTokenAmount") or {}).get("decimals") or 0)
 return None

def event(raw):
 if len(raw)<153 or raw[:16]!=EVENT_DISC:return None
 o=16
 amount,collateral,dex,helio,allocation=struct.unpack_from("<QQQQQ",raw,o);o+=40
 curve=b58e(raw[o:o+32]);o+=32
 cost=b58e(raw[o:o+32]);o+=32
 sender=b58e(raw[o:o+32]);o+=32
 typ=raw[o];o+=1
 label=""
 if len(raw)>=o+4:
  ln=struct.unpack_from("<I",raw,o)[0];o+=4
  if len(raw)>=o+ln:label=raw[o:o+ln].decode("utf-8","replace")
 return {"amount_raw":amount,"collateral_lamports":collateral,"dex_fee_lamports":dex,
  "helio_fee_lamports":helio,"allocation":allocation,"curve":curve,"cost_token":cost,
  "sender":sender,"event_side":"BUY" if typ==0 else ("SELL" if typ==1 else "UNKNOWN"),
  "label":label}

def events(tx,parent):
 ks=keys(tx);out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=parent:continue
  for ix in g.get("instructions") or []:
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=PROGRAM or not ix.get("data"):continue
   try:e=event(b58d(ix["data"]))
   except Exception:e=None
   if e:out.append(e)
 return out

def parent(level,ordinal):
 return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="MOONIT":continue
  r=x["roles"];es=events(x["transaction"],parent(x["level"],x["instruction_ordinal"]))
  matches=[e for e in es if e["curve"]==r["curve_account"] and e["sender"]==r["sender"] and e["event_side"]==x["side"]]
  e=matches[0] if len(matches)==1 else None
  dec=mint_decimals(x["transaction"],r["mint"])
  if e and dec is not None:
   token=e["amount_raw"]/(10**dec);coll=e["collateral_lamports"]/1_000_000_000
   if x["side"]=="BUY":ia,im,oa,om=coll,"NATIVE_SOL",token,r["mint"]
   else:ia,im,oa,om=token,r["mint"],coll,"NATIVE_SOL"
   state="EXACT_MOONIT_TRADE_EVENT_ECONOMICS"
  else:
   ia=im=oa=om=None;state="MOONIT_EVENT_RECONCILIATION_PENDING"
  rows.append({"signature":x["signature"],"side":x["side"],"market_address":r["curve_account"],"trader":r["sender"],
   "input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
   "dex_fee_sol":e["dex_fee_lamports"]/1_000_000_000 if e else None,
   "helio_fee_sol":e["helio_fee_lamports"]/1_000_000_000 if e else None,
   "event_allocation":e["allocation"] if e else None,"event_label":e["label"] if e else None,
   "event_match_count":len(matches),"decoder_state":state,"execution_authority":False})
 return {"revision":"USLS_095C","row_count":len(rows),
  "exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "economics_source":"MOONIT_PROGRAM_TRADE_EVENT","rows":rows,
  "supersedes":"USLS_095","profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/moonit_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
