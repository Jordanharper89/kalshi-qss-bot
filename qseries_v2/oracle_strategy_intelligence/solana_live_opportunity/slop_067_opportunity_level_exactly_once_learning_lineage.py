import json
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
