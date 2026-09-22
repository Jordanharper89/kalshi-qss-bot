from __future__ import annotations
import ast,json,re
from pathlib import Path
A="qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py"
B="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
TERMS=("asset","mint","token","pool","price","timestamp","observed_at","slot","horizon","return","mfe","mae","path","outcome")
def keys(path):
 text=path.read_text(encoding="utf-8",errors="replace");out=set()
 for m in re.finditer(r'["\']([A-Za-z_][A-Za-z0-9_]*)["\']',text):
  k=m.group(1)
  if any(t in k.lower() for t in TERMS):out.add(k)
 return sorted(out)
def audit(root):
 ka=keys(root/A);kb=keys(root/B);shared=sorted(set(ka)&set(kb))
 return {"revision":"OSI_055","oad312_keys":ka,"oad314_keys":kb,"shared_keys":shared,"shared_key_count":len(shared),"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/oad312_314_shared_contract.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
