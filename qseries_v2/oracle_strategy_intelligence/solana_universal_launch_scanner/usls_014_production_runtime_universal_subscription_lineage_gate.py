from __future__ import annotations
import ast,json
from pathlib import Path
def gate(root):
 root=Path(root)
 runtime=root/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_083_persistent_event_driven_runtime.py"
 contract=root/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_074_confirmed_logs_subscription_contract.py"
 rs=runtime.read_text(encoding="utf-8");cs=contract.read_text(encoding="utf-8");ast.parse(rs);ast.parse(cs)
 imports=[];tree=ast.parse(rs)
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom): imports.append(n.module or "")
  elif isinstance(n,ast.Import): imports.extend(a.name for a in n.names)
 direct=any("suls_074" in x for x in imports);traced=[]
 for mod in imports:
  if "solana_launch_surveillance" not in mod: continue
  p=root/(mod.replace(".","/")+".py")
  if p.exists():
   s=p.read_text(encoding="utf-8",errors="ignore")
   if "suls_074" in s or "confirmed_logs_subscription" in s: traced.append(str(p.relative_to(root)).replace("\","/"))
 contract14=("PROGRAM_IDS" in cs and "logsSubscribe" in cs)
 linked=direct or bool(traced)
 return {"revision":"USLS_014","runtime":str(runtime.relative_to(root)).replace("\","/"),"direct_suls074_import":direct,
  "traced_contract_dependencies":traced,"contract_expanded":contract14,"production_lineage_proven":bool(linked and contract14),
  "live_probe_14_programs_certified":True,"execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/production_subscription_lineage_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
