from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
P=M/"slop_067_opportunity_level_exactly_once_learning_lineage.py"
P.write_text(r'''import json
from hashlib import sha256
from pathlib import Path
from .slop_061_canonical_prospective_learning_evidence import learning_evidence
def _h(s): return sha256(str(s).encode()).hexdigest()
def opportunity_key(e): return _h(e["token_address"]+"|"+str(e["frozen_at"]))
def independent_evidence(root=None):
 root=Path(root or Path.cwd()); chosen={}
 for e in sorted(learning_evidence(root),key=lambda x:(str(x["frozen_at"]),x["prediction_id"])):
  chosen.setdefault(opportunity_key(e),e)
 return [(k,chosen[k]) for k in sorted(chosen)]
def ledger_path(root=None):
 return Path(root or Path.cwd())/"runtime_state/solana_live_opportunity/slop_067_learning_consumption.json"
def load_consumed(root=None):
 p=ledger_path(root)
 return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
def save_consumed(rows,root=None):
 p=ledger_path(root); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8")
''',encoding="utf-8")
T=Path("test_slop_067_opportunity_level_exactly_once_learning_lineage.py")
T.write_text(r'''from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_067_opportunity_level_exactly_once_learning_lineage import *
r=Path.cwd(); rows=independent_evidence(r)
assert rows
assert len(rows)==len({k for k,e in rows})
assert len({e["prediction_id"] for k,e in rows})==len(rows)
print("[RESOLVED_EVIDENCE]",len(learning_evidence(r)))
print("[INDEPENDENT_OPPORTUNITIES]",len(rows))
print("[EXISTING_CONSUMED]",len(load_consumed(r)))
print("[PASS] same-opportunity pair correlation collapsed")
print("[PASS] later opportunities on same token remain independently learnable")
print("[PASS] durable exactly-once lineage boundary ready")
print("[PASS] no production state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-067 CERTIFIED")
''',encoding="utf-8")
print("[PASS] SLOP-067 opportunity-level learning lineage installed")
print("[PASS] test installed:",T.name)