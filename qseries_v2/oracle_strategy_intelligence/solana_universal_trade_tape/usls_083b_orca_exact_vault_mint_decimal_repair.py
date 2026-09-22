from __future__ import annotations
import json
from pathlib import Path

def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])

def token_meta(tx):
 ks=keys(tx);out={}
 for name in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(name) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    out[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return out

def scale(raw,acct,tm):
 z=tm.get(acct)
 if raw is None or not z:return None,None
 return raw/(10**z["decimals"]),z["mint"]

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 ix=json.loads((b/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"))
 rr=json.loads((b/"meteora_orca_exact_transfer_reconciliation.json").read_text(encoding="utf-8"))
 bysig={}
 for x in ix["rows"]:
  if x["venue"]=="ORCA":bysig.setdefault(x["signature"],[]).append(x)
 rows=[]
 for r in rr["rows"]:
  if r["venue"]!="ORCA" or not r["economics"]:continue
  ms=bysig.get(r["signature"],[])
  x=ms[0] if len(ms)==1 else None
  if not x:continue
  a=x["accounts"];tm=token_meta(x["transaction"]);direction=r["economics"].get("direction")
  vault_a=a[4] if len(a)>4 else None;vault_b=a[6] if len(a)>6 else None
  if direction=="A_TO_B":
   ia,im=scale(r["economics"]["input_amount"],vault_a,tm)
   oa,om=scale(r["economics"]["output_amount"],vault_b,tm)
  elif direction=="B_TO_A":
   ia,im=scale(r["economics"]["input_amount"],vault_b,tm)
   oa,om=scale(r["economics"]["output_amount"],vault_a,tm)
  else:
   ia=oa=im=om=None
  exact=bool(im and om and ia is not None and oa is not None)
  rows.append({"signature":r["signature"],"pool":r["pool"],"trader":r["trader"],"direction":direction,
   "vault_a":vault_a,"vault_b":vault_b,"input_mint":im,"input_amount":ia,"output_mint":om,"output_amount":oa,
   "decoder_state":"EXACT_ORCA_VAULT_MINT_DECIMAL_ECONOMICS" if exact else "ORCA_VAULT_MINT_DECIMAL_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_083B","row_count":len(rows),
  "exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "rows":rows,"supersedes":"USLS_083","profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/orca_exact_mint_decimal_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
