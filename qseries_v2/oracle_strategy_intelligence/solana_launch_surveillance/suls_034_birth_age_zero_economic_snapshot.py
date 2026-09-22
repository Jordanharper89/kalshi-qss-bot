from __future__ import annotations
import json
from decimal import Decimal
def dec(x):
 try:return Decimal(str(x))
 except Exception:return None
def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));out=[]
 for e in d.get("events",[]):
  ta=dec(e.get("initial_token_amount"));qa=dec(e.get("initial_quote_amount"))
  qpt=(qa/ta) if ta and qa and ta!=0 else None
  out.append({**e,"age_seconds":0,"initial_quote_per_token":None if qpt is None else str(qpt),
   "usd_price":None,"usd_liquidity":None,
   "pricing_scope":"NATIVE_QUOTE_RESERVES_ONLY_NO_EXTERNAL_USD_CONTEXT"})
 return {"revision":"SULS_034","snapshot_count":len(out),"snapshots":out,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_age_zero_economic_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
