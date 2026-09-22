from __future__ import annotations
import inspect,json,re
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_333_solana_authoritative_program_identity_registry as reg
from qseries_v2.oracle_adapters.independent import oad_353_solana_final_verified_economic_program_expansion as exp

B58=re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
def readback():
 src1=inspect.getsource(reg);src2=inspect.getsource(exp)
 addrs=sorted(set(B58.findall(src1+"\n"+src2)))
 labels={}
 for a in addrs:
  ctx=(src1+"\n"+src2)
  i=ctx.find(a);window=ctx[max(0,i-220):i+220].lower()
  fam=[]
  for k in ("pump","meteora","raydium","orca","jupiter","token2022","memo"):
   if k in window:fam.append(k)
  labels[a]=fam
 return {"revision":"SULS_014","address_count":len(addrs),"addresses":addrs,
  "context_labels":labels,"execution_authority":False,"read_only":True}
def write(root):
 d=readback();p=root/"runtime_state/solana_opportunities/launch_surveillance/program_registry_exact_readback.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
