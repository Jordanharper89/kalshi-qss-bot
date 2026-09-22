from __future__ import annotations
import json,re
from pathlib import Path
NATIVE_MODULES=(
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py")
TOKENS=("runtime_state","runtime/","runtime\\\\",".json",".jsonl","postgres","table","pool","mint","swap","slot","signature")
def _scan(path:Path)->list[dict]:
 if not path.is_file():return []
 out=[]
 for n,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
  low=line.lower()
  if any(t in low for t in TOKENS):out.append({"line":n,"text":line[:600]})
 return out[:300]
def build_registry(root:Path)->dict:
 native=[]
 for rel in NATIVE_MODULES:
  p=root/rel
  if p.is_file():native.append({"module":rel,"lineage":_scan(p)})
 gmgn=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  if "gmgn" in p.name.lower() or "gmgn" in p.read_text(encoding="utf-8",errors="replace").lower():
   gmgn.append({"module":str(p.relative_to(root)),"lineage":_scan(p)})
 cb=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  if "coinbase" in p.name.lower():cb.append(str(p.relative_to(root)))
 return {"revision":"OSI_026","primary":{"native_solana":native,"gmgn":gmgn},
  "context_only":{"coinbase":cb},"policy":{"coinbase_can_create_opportunity":False,
  "native_solana_priority":1,"gmgn_priority":2,"coinbase_priority":3},
  "execution_authority":False,"read_only":True}
def write_registry(root:Path)->Path:
 d=build_registry(root);p=root/"runtime_state/solana_opportunities/source_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
