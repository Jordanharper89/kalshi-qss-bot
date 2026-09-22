from __future__ import annotations
import ast,json
from pathlib import Path

PKG="qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance"
RUNTIME="suls_083_persistent_event_driven_runtime"
TARGET="suls_074_confirmed_logs_subscription_contract"

def _module_path(root,name):
 p=root/(name.replace(".","/")+".py")
 return p if p.exists() else None

def _imports(path):
 tree=ast.parse(path.read_text(encoding="utf-8"))
 out=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):
   if n.module:
    out.append(n.module)
  elif isinstance(n,ast.Import):
   out.extend(a.name for a in n.names)
 return out

def _trace(root,start,target,max_depth=6):
 start_name=f"{PKG}.{start}"
 target_name=f"{PKG}.{target}"
 q=[(start_name,0,[start_name])]
 seen=set()
 while q:
  name,depth,pathline=q.pop(0)
  if name in seen: continue
  seen.add(name)
  if name==target_name:
   return pathline
  if depth>=max_depth: continue
  p=_module_path(root,name)
  if not p: continue
  for dep in _imports(p):
   if dep==target_name:
    return pathline+[dep]
   if dep.startswith(PKG+"."):
    q.append((dep,depth+1,pathline+[dep]))
 return []

def gate(root):
 root=Path(root).resolve()
 runtime=_module_path(root,f"{PKG}.{RUNTIME}")
 contract=_module_path(root,f"{PKG}.{TARGET}")
 if not runtime: raise RuntimeError("SULS_083_RUNTIME_NOT_FOUND")
 if not contract: raise RuntimeError("SULS_074_CONTRACT_NOT_FOUND")

 rs=runtime.read_text(encoding="utf-8")
 cs=contract.read_text(encoding="utf-8")
 ast.parse(rs);ast.parse(cs)

 ids=(
 "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
 "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
 "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
 "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
 "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
 "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
 "dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
 "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
 "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
 "MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
 )
 missing=[x for x in ids if x not in cs]
 lineage=_trace(root,RUNTIME,TARGET)

 return {"revision":"USLS_014B",
  "runtime":str(runtime.relative_to(root)).replace("\\\\","/"),
  "contract":str(contract.relative_to(root)).replace("\\\\","/"),
  "subscription_program_count":len(ids),
  "missing_program_ids":missing,
  "contract_expanded":("PROGRAM_IDS" in cs and "logsSubscribe" in cs and not missing),
  "dependency_lineage":lineage,
  "production_lineage_proven":bool(lineage),
  "execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/production_subscription_lineage_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
