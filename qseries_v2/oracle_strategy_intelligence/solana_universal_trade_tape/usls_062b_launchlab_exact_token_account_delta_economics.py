from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import roles

def account_keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in (msg.get("accountKeys") or [])]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 for x in (la.get("writable") or [])+(la.get("readonly") or []):
  if x not in ks:ks.append(x)
 return ks

def token_balance_map(tx):
 meta=(tx or {}).get("meta") or {};out={}
 for side,key in (("pre","preTokenBalances"),("post","postTokenBalances")):
  for x in meta.get(key) or []:
   u=x.get("uiTokenAmount") or {};idx=x.get("accountIndex")
   if idx is None or not x.get("mint"):continue
   out[(side,int(idx))]={"mint":x["mint"],"raw":int(u.get("amount") or 0),"decimals":int(u.get("decimals") or 0)}
 return out

def delta_for_account(tx,address,expected_mint):
 ks=account_keys(tx)
 try:idx=ks.index(address)
 except ValueError:return None
 bm=token_balance_map(tx);pre=bm.get(("pre",idx));post=bm.get(("post",idx))
 seen=pre or post
 if not seen or seen["mint"]!=expected_mint:return None
 dec=seen["decimals"];a=pre["raw"] if pre else 0;b=post["raw"] if post else 0
 return (b-a)/(10**dec)

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"launchlab_deep_trade_census.json").read_text(encoding="utf-8"));out=[]
 for x in src["rows"]:
  r=roles(x["accounts"]);base_m=r["base_token_mint"];quote_m=r["quote_token_mint"]
  bd=delta_for_account(x["transaction"],r["user_base_token"],base_m)
  qd=delta_for_account(x["transaction"],r["user_quote_token"],quote_m)
  exact=bd is not None and qd is not None and bd>0 and qd<0
  out.append({"signature":x["signature"],"instruction_name":x["instruction_name"],
   "trader":r["payer"],"pool":r["pool_state"],"base_mint":base_m,"quote_mint":quote_m,
   "user_base_token_account":r["user_base_token"],"user_quote_token_account":r["user_quote_token"],
   "base_vault":r["base_vault"],"quote_vault":r["quote_vault"],
   "base_amount":bd if exact else None,"quote_amount":-qd if exact else None,
   "effective_price":(-qd/bd) if exact and bd else None,"side":"BUY" if exact else "UNKNOWN_TRADE_TYPE",
   "decoder_state":"EXACT_LAUNCHLAB_BUY_ECONOMICS" if exact else "TOKEN_ACCOUNT_DELTA_UNRESOLVED",
   "execution_authority":False})
 return {"revision":"USLS_062B","row_count":len(out),
  "exact_economic_count":sum(x["decoder_state"]=="EXACT_LAUNCHLAB_BUY_ECONOMICS" for x in out),
  "rows":out,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_exact_account_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
