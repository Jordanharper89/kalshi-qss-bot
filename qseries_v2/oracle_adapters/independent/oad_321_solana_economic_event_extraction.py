\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaEconomicEvent:
 signature:str; slot:int; event_type:str; program_id:str; mint:str|None; owner:str|None; amount_delta:float|None
 evidence:dict; execution_authority:bool=False
def _amount(x):
 ui=(x.get("uiTokenAmount") or {})
 v=ui.get("uiAmountString")
 try:return float(v)
 except (TypeError,ValueError): return float(ui.get("uiAmount") or 0.0)
def extract_economic_events(envelopes,classifications):
 bysig={}
 for c in classifications:bysig.setdefault(c.signature,[]).append(c)
 out=[]
 for e in envelopes:
  cs=bysig.get(e.signature,[])
  for c in cs:
   typ=(c.parsed_type or "").lower()
   et=None
   if typ in ("transfer","transferchecked"):et="TOKEN_TRANSFER" if "TOKEN" in c.program_class else "NATIVE_TRANSFER"
   elif "mint" in typ:et="TOKEN_MINT"
   elif "burn" in typ:et="TOKEN_BURN"
   elif typ in ("initializeaccount","initializeaccount2","initializeaccount3"):et="TOKEN_ACCOUNT_CREATE"
   if et: out.append(SolanaEconomicEvent(e.signature,e.slot,et,c.program_id,None,None,None,{"instruction_index":c.instruction_index},False))
  pre={(x.get("accountIndex"),x.get("mint"),x.get("owner")):_amount(x) for x in e.pre_token_balances}
  post={(x.get("accountIndex"),x.get("mint"),x.get("owner")):_amount(x) for x in e.post_token_balances}
  for k in set(pre)|set(post):
   d=post.get(k,0.0)-pre.get(k,0.0)
   if abs(d)>0:
    out.append(SolanaEconomicEvent(e.signature,e.slot,"TOKEN_BALANCE_FLOW","BALANCE_DELTA",str(k[1]) if k[1] else None,str(k[2]) if k[2] else None,d,{"account_index":k[0]},False))
  if not cs:
   out.append(SolanaEconomicEvent(e.signature,e.slot,"UNCLASSIFIED_TRANSACTION","UNKNOWN",None,None,None,{"retained":True},False))
 return tuple(out)

