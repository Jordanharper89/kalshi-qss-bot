\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaTransactionEnvelope:
 slot:int; block_time:int|None; blockhash:str; signature:str; version:object; success:bool; fee:int
 account_keys:tuple; instructions:tuple; inner_instructions:tuple; pre_token_balances:tuple; post_token_balances:tuple
 log_messages:tuple; raw_transaction:dict; execution_authority:bool=False
def _keys(msg):
 out=[]
 for x in tuple(msg.get("accountKeys") or ()):
  out.append(str(x.get("pubkey")) if isinstance(x,dict) else str(x))
 return tuple(out)
def canonical_transaction_envelopes(batch):
 out=[]
 for slot,b in batch.blocks:
  for row in tuple(b.get("transactions") or ()):
   tx=dict(row.get("transaction") or {}); meta=dict(row.get("meta") or {}); msg=dict(tx.get("message") or {})
   sigs=tuple(tx.get("signatures") or ())
   if not sigs: continue
   out.append(SolanaTransactionEnvelope(int(slot),b.get("blockTime"),str(b.get("blockhash") or ""),str(sigs[0]),row.get("version","legacy"),meta.get("err") is None,int(meta.get("fee") or 0),_keys(msg),tuple(msg.get("instructions") or ()),tuple(meta.get("innerInstructions") or ()),tuple(meta.get("preTokenBalances") or ()),tuple(meta.get("postTokenBalances") or ()),tuple(meta.get("logMessages") or ()),row,False))
 return tuple(out)

