from hashlib import sha256
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
