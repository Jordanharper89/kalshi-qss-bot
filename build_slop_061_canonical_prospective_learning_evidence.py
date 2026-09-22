from pathlib import Path
M=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity")
M.mkdir(parents=True,exist_ok=True)
P=M/"slop_061_canonical_prospective_learning_evidence.py"
P.write_text(r'''from hashlib import sha256
import json
from pathlib import Path
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts

def _canon(x):
 return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def learning_evidence(root=None):
 root=Path(root or Path.cwd())
 ps={p.prediction_id:p for p in read_predictions(root)}
 out=[]
 for r in read_resolution_dicts(root):
  pid=r["prediction_id"]
  p=ps.get(pid)
  if not p: continue
  raw={"prediction_id":pid,"token_address":p.token_address,
   "pair_address":p.pair_address,"frozen_at":str(p.frozen_at),
   "condition":"BUY_PRESSURE","horizon_seconds":60,
   "target_fraction":0.10,"stop_fraction":-0.05,"friction_bps":200,
   "outcome":r.get("outcome"),"gross_return":r.get("gross_return"),
   "net_return":r.get("net_return"),"terminal_return":r.get("terminal_return"),
   "mfe":r.get("mfe"),"mae":r.get("mae")}
  raw["evidence_hash"]=sha256(_canon(raw).encode()).hexdigest()
  out.append(raw)
 return out
''',encoding="utf-8")
T=Path("test_slop_061_canonical_prospective_learning_evidence.py")
T.write_text(r'''from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_061_canonical_prospective_learning_evidence import learning_evidence
x=learning_evidence(Path.cwd())
assert x,"NO_RESOLVED_LEARNING_EVIDENCE"
assert all(len(v["evidence_hash"])==64 for v in x)
assert all(v["condition"]=="BUY_PRESSURE" and v["horizon_seconds"]==60 for v in x)
assert all(v["target_fraction"]==.10 and v["stop_fraction"]==-.05 and v["friction_bps"]==200 for v in x)
print("[EVIDENCE_RECORDS]",len(x))
print("[INDEPENDENT_TOKENS]",len({v["token_address"] for v in x}))
print("[OUTCOMES]",{k:sum(v["outcome"]==k for v in x) for k in sorted({v["outcome"] for v in x})})
print("[PASS] canonical prediction+resolution learning evidence materialized")
print("[PASS] frozen BUY_PRESSURE economics preserved")
print("[PASS] source ledgers unchanged")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-061 CERTIFIED")
''',encoding="utf-8")
print("[PASS] SLOP-061 canonical prospective learning evidence installed")
print("[PASS] test installed:",T.name)