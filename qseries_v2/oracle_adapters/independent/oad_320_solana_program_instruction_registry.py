\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
PROGRAMS={
"11111111111111111111111111111111":"SYSTEM",
"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":"SPL_TOKEN",
"TokenzQdYhYhQb...":"TOKEN_2022",
"ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL":"ASSOCIATED_TOKEN",
"ComputeBudget111111111111111111111111111111":"COMPUTE_BUDGET",
"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr":"MEMO",
}
@dataclass(frozen=True,slots=True)
class SolanaInstructionClassification:
 signature:str; instruction_index:int; program_id:str; program_class:str; parsed_type:str|None; retained:bool=True; execution_authority:bool=False
def _pid(ix,keys):
 p=ix.get("programId")
 if p:return str(p)
 n=ix.get("programIdIndex")
 return keys[int(n)] if n is not None and int(n)<len(keys) else "UNKNOWN"
def classify_transaction_instructions(envelopes):
 out=[]
 for e in envelopes:
  all_ix=list(e.instructions)
  for group in e.inner_instructions:
   all_ix.extend(tuple(group.get("instructions") or ()))
  for i,ix in enumerate(all_ix):
   if not isinstance(ix,dict): continue
   pid=_pid(ix,e.account_keys); parsed=ix.get("parsed"); typ=parsed.get("type") if isinstance(parsed,dict) else None
   pclass=PROGRAMS.get(pid)
   if pclass is None:
    pl=(str(ix.get("program") or "")+" "+str(typ or "")).lower()
    if "token" in pl:pclass="TOKEN_PROGRAM"
    elif "system" in pl:pclass="SYSTEM"
    else:pclass="UNKNOWN_PROGRAM"
   out.append(SolanaInstructionClassification(e.signature,i,pid,pclass,str(typ) if typ else None,True,False))
 return tuple(out)

